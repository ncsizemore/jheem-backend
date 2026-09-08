import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { createPlan, createAwsStorage, promote, verifyDelivery } from './calibration-promotion.mjs';

const digest = (value) => crypto.createHash('sha256').update(value).digest('hex');
const cacheControl = 'public, max-age=31536000, immutable';
const artifact = { path: 'model/locations/AA/ehe.json', size: 2, sha256: digest('{}'), content_type: 'application/json' };
const index = { ...artifact, path: 'index.json' };
const plan = { release: 'test-v1', files: [index, artifact] };
const metadata = (file) => ({ ContentLength: file.size, ChecksumSHA256: Buffer.from(file.sha256, 'hex').toString('base64'), ContentType: file.content_type, CacheControl: cacheControl });

function storageFixture(initial = []) {
  const objects = new Map(initial.map((file) => [file.path, metadata(file)]));
  const writes = [];
  return {
    writes, objects,
    list: async () => [...objects.keys()],
    head: async (file) => objects.get(file.path),
    put: async (file) => {
      assert.ok(!objects.has(file.path), 'must never overwrite an existing object');
      writes.push(file.path);
      objects.set(file.path, metadata(file));
    },
  };
}

test('publishes the index only after every scientific file passes delivery verification', async () => {
  const storage = storageFixture();
  const events = [];
  const result = await promote(plan, storage, async (file) => {
    events.push(file.path);
    if (file.path === artifact.path) assert.ok(!storage.objects.has('index.json'));
  });
  assert.deepEqual(events, [artifact.path, 'index.json']);
  assert.equal(result.uploaded, 2);
});

test('delivery failure leaves the index absent and the matching partial release can resume', async () => {
  const storage = storageFixture();
  await assert.rejects(promote(plan, storage, async () => { throw new Error('CORS failure'); }), /CORS failure/);
  assert.deepEqual(storage.writes, [artifact.path]);
  const result = await promote(plan, storage, async () => {});
  assert.equal(result.uploaded, 1);
  assert.equal(result.reused, 1);
});

test('complete matching publication is verified without any writes', async () => {
  const storage = storageFixture(plan.files);
  const result = await promote(plan, storage, async () => {});
  assert.equal(result.uploaded, 0);
  assert.equal(result.verified, 2);
});

test('rejects unexpected prefix objects before writing', async () => {
  const storage = storageFixture([{ ...artifact, path: 'unexpected.json' }]);
  await assert.rejects(promote(plan, storage, async () => {}), /Unexpected object/);
  assert.equal(storage.writes.length, 0);
});

test('rejects different bytes or headers before writing', async () => {
  for (const changes of [{ ChecksumSHA256: 'changed' }, { ContentType: 'text/html' }, { ContentEncoding: 'gzip' }]) {
    const storage = storageFixture([artifact]);
    Object.assign(storage.objects.get(artifact.path), changes);
    await assert.rejects(promote(plan, storage, async () => {}), /Existing object differs/);
    assert.equal(storage.writes.length, 0);
  }
});

test('rejects an already published index with missing scientific files', async () => {
  const storage = storageFixture([index]);
  await assert.rejects(promote(plan, storage, async () => {}), /release is incomplete/);
  assert.equal(storage.writes.length, 0);
});

test('conditional-write conflict is fatal and does not publish the index', async () => {
  const storage = storageFixture();
  storage.put = async () => { throw new Error('PreconditionFailed'); };
  await assert.rejects(promote(plan, storage, async () => {}), /PreconditionFailed/);
  assert.ok(!storage.objects.has('index.json'));
});

test('AWS upload uses atomic create-only and S3 checksum validation', async (context) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'calibration-promotion-test-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(path.join(root, 'index.json'), '{}');
  const calls = [];
  const storage = createAwsStorage({ bucket: 'test-bucket', prefix: 'portal/test-v1' }, root,
    (command, args) => { calls.push({ command, args }); return '{}'; });
  await storage.put(index);
  const args = calls[0].args;
  assert.equal(args[args.indexOf('--if-none-match') + 1], '*');
  assert.equal(args[args.indexOf('--checksum-sha256') + 1], Buffer.from(index.sha256, 'hex').toString('base64'));
  fs.writeFileSync(path.join(root, 'index.json'), 'changed');
  await assert.rejects(storage.put(index), /Local bytes changed/);
  assert.equal(calls.length, 1);
});

test('browser verification rejects bad CORS, headers, bytes and HTTP errors', async () => {
  const config = { delivery_url: 'https://example.test/test-v1', browser_origin: 'https://jheem.org' };
  const headers = { 'access-control-allow-origin': '*', 'content-type': 'application/json', 'cache-control': cacheControl };
  await verifyDelivery(config, index, async () => new Response('{}', { headers }));
  for (const response of [
    new Response('{}', { headers: { ...headers, 'access-control-allow-origin': 'https://wrong.test' } }),
    new Response('{}', { headers: { ...headers, 'content-type': 'text/html' } }),
    new Response('[]', { headers }),
    new Response('denied', { status: 403 }),
  ]) await assert.rejects(verifyDelivery(config, index, async () => response), /CloudFront/);
});

test('plan rejects staging that differs from the reviewed pin', (context) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'calibration-plan-test-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.writeFileSync(path.join(root, 'index.json'), '{}');
  assert.throws(() => createPlan(root, { index_sha256: 'wrong', expected_files: 1, expected_bytes: 2 }), /differs from promotion pin/);
});
