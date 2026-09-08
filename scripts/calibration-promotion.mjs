import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';

const cacheControl = 'public, max-age=31536000, immutable';
const digest = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

function filesUnder(root, relative = '') {
  return fs.readdirSync(path.join(root, relative)).sort().flatMap((name) => {
    if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(name)) throw new Error(`Unsafe filename: ${name}`);
    const file = relative ? `${relative}/${name}` : name;
    const stat = fs.lstatSync(path.join(root, file));
    if (stat.isDirectory()) return filesUnder(root, file);
    if (!stat.isFile()) throw new Error(`Nonregular file: ${file}`);
    const bytes = fs.readFileSync(path.join(root, file));
    return [{ path: file, size: bytes.length, sha256: digest(bytes),
      content_type: file.endsWith('.json') ? 'application/json' : 'text/plain' }];
  });
}

export function createPlan(root, config) {
  const files = filesUnder(root);
  const index = files.find((file) => file.path === 'index.json');
  const totalBytes = files.reduce((sum, file) => sum + file.size, 0);
  if (index?.sha256 !== config.index_sha256 || files.length !== config.expected_files ||
      totalBytes !== config.expected_bytes) throw new Error('Staged release differs from promotion pin');
  const payload = JSON.parse(fs.readFileSync(path.join(root, 'index.json'), 'utf8'));
  if (payload.release !== config.release || config.prefix !== `portal/${payload.destination_prefix}` ||
      new URL(config.delivery_url).pathname !== `/${payload.destination_prefix}`) {
    throw new Error('Delivery paths differ from the pinned release');
  }
  return {
    release: config.release, bucket: config.bucket, prefix: config.prefix,
    delivery_url: config.delivery_url, file_count: files.length, total_bytes: totalBytes,
    cache_control: cacheControl,
    manifests: payload.products.map((product) => ({
      model: product.model, portal_model: product.portal_model,
      url: `${config.delivery_url}/${product.manifest}`,
      sha256: files.find((file) => file.path === product.manifest).sha256,
    })),
    files,
  };
}

export function createAwsStorage(config, root, run = execFileSync) {
  function aws(operation, args) {
    return JSON.parse(run('aws', ['s3api', operation, '--bucket', config.bucket,
      ...args, '--output', 'json', '--no-cli-pager'], {
      encoding: 'utf8', timeout: 120000, maxBuffer: 4 * 1024 * 1024,
    }) || '{}');
  }
  return {
    list: async () => {
      const response = aws('list-objects-v2', ['--prefix', `${config.prefix}/`]);
      return (response.Contents ?? []).map((item) => item.Key.slice(config.prefix.length + 1));
    },
    head: async (file) => aws('head-object', ['--key', `${config.prefix}/${file.path}`,
      '--checksum-mode', 'ENABLED']),
    put: async (file) => {
      const filename = path.join(root, file.path);
      // Check again immediately before writing, even though staging was already verified.
      if (digest(fs.readFileSync(filename)) !== file.sha256) throw new Error(`Local bytes changed: ${file.path}`);
      aws('put-object', ['--key', `${config.prefix}/${file.path}`, '--body', filename,
        '--if-none-match', '*', '--checksum-algorithm', 'SHA256',
        '--checksum-sha256', Buffer.from(file.sha256, 'hex').toString('base64'),
        '--content-type', file.content_type, '--cache-control', cacheControl]);
    },
  };
}

function verifyStored(file, metadata) {
  if (metadata.ContentLength !== file.size ||
      metadata.ChecksumSHA256 !== Buffer.from(file.sha256, 'hex').toString('base64') ||
      metadata.ContentType !== file.content_type || metadata.CacheControl !== cacheControl ||
      metadata.ContentEncoding || metadata.ContentDisposition) {
    throw new Error(`Existing object differs from release bytes or delivery metadata: ${file.path}`);
  }
}

export async function verifyDelivery(config, file, fetchImplementation = globalThis.fetch) {
  const response = await fetchImplementation(`${config.delivery_url}/${file.path}`, {
    headers: { Origin: config.browser_origin }, signal: AbortSignal.timeout(60000),
    redirect: 'error',
  });
  if (!response.ok) throw new Error(`CloudFront HTTP ${response.status}: ${file.path}`);
  const allowOrigin = response.headers.get('access-control-allow-origin');
  if (allowOrigin !== '*' && allowOrigin !== config.browser_origin) {
    throw new Error(`CloudFront CORS does not allow the portal: ${file.path}`);
  }
  if (response.headers.get('content-type')?.split(';')[0] !== file.content_type ||
      response.headers.get('content-disposition') ||
      response.headers.get('cache-control') !== cacheControl) {
    throw new Error(`CloudFront delivery metadata differs: ${file.path}`);
  }
  // Fetch decompresses a CDN-compressed response; compare the original scientific bytes.
  const bytes = Buffer.from(await response.arrayBuffer());
  if (bytes.length !== file.size || digest(bytes) !== file.sha256) {
    throw new Error(`CloudFront bytes differ: ${file.path}`);
  }
}

export async function promote(plan, storage, verify, log = () => {}) {
  const expected = new Map(plan.files.map((file) => [file.path, file]));
  const existing = new Set(await storage.list());
  // Complete preflight before the first write, including every object from a partial earlier run.
  for (const name of existing) {
    if (!expected.has(name)) throw new Error(`Unexpected object in release prefix: ${name}`);
    verifyStored(expected.get(name), await storage.head(expected.get(name)));
  }
  if (existing.has('index.json') && existing.size !== expected.size) {
    throw new Error('Published index exists but release is incomplete');
  }
  const ordered = [...plan.files.filter((file) => file.path !== 'index.json'), expected.get('index.json')];
  let uploaded = 0;
  for (const file of ordered) {
    if (!existing.has(file.path)) {
      await storage.put(file);
      verifyStored(file, await storage.head(file));
      uploaded += 1;
    }
    // index.json is uploaded only after all other files pass browser-origin delivery checks.
    await verify(file);
    log(`Verified ${file.path}`);
  }
  return { release: plan.release, verified: ordered.length, uploaded, reused: existing.size };
}
