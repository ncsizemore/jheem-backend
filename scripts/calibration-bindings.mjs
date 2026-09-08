import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const products = {
  'ryan-white-msa': { model: 'ryan-white-msa', portal: 'ryan-white', geography: 'msa', samples: 80 },
  'ryan-white-state-ajph': { model: 'ryan-white-ajph', portal: 'ryan-white-state-ajph', geography: 'state', samples: 1000 },
  'ryan-white-state-croi': { model: 'ryan-white-croi', portal: 'ryan-white-state-croi', geography: 'state', samples: 1000 },
};

export function validateBindings(config, promotion) {
  const bindings = [];
  for (const [id, model] of Object.entries(config)) {
    if (model?.calibration && !products[id]) throw new Error(`${id}: calibration has no reviewed product mapping`);
  }
  for (const [id, product] of Object.entries(products)) {
    const binding = config[id]?.calibration;
    assert.ok(binding, `${id}: calibration binding is required`);
    assert.deepEqual(Object.keys(binding).sort(), [
      'displayFacets', 'locationIndexSha256', 'locationIndexUrl', 'manifestSha256', 'manifestUrl', 'release',
    ], `${id}: unsupported or missing calibration fields`);
    assert.equal(binding.release, promotion.release, `${id}: release differs from promotion`);
    assert.equal(binding.manifestUrl, `${promotion.delivery_url}/${product.model}/manifest.json`, `${id}: wrong manifest URL`);
    assert.equal(binding.locationIndexUrl, `${promotion.delivery_url}/${product.model}/locations.json`, `${id}: wrong location index URL`);
    for (const field of ['manifestSha256', 'locationIndexSha256']) {
      assert.match(binding[field], /^[0-9a-f]{64}$/, `${id}: invalid ${field}`);
    }
    assert.deepEqual(binding.displayFacets, ['total', 'age'], `${id}: display facets exceed reviewed scope`);
    bindings.push({ id, product, binding, config: config[id] });
  }
  return bindings;
}

export function validateBindingArtifacts(config, promotion, root) {
  const files = [];
  for (const { id, product, binding, config: model } of validateBindings(config, promotion)) {
    function load(filename, expectedHash) {
      const relative = `${product.model}/${filename}`;
      const bytes = fs.readFileSync(path.join(root, relative));
      const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
      assert.equal(sha256, expectedHash, `${id}: ${filename} checksum differs from config`);
      files.push({ path: relative, size: bytes.length, sha256, content_type: 'application/json' });
      return JSON.parse(bytes);
    }
    const manifest = load('manifest.json', binding.manifestSha256);
    const locations = load('locations.json', binding.locationIndexSha256);
    for (const [name, document, schema] of [
      ['manifest', manifest, 'jheem-calibration-manifest/v1'],
      ['locations', locations, 'jheem-calibration-location-index/v1'],
    ]) {
      assert.equal(document.schema_version, schema, `${id}: wrong ${name} schema`);
      assert.equal(document.release, binding.release, `${id}: wrong ${name} release`);
      assert.equal(document.model, product.model, `${id}: wrong ${name} model`);
      assert.equal(document.portal_model, product.portal, `${id}: wrong ${name} portal model`);
    }
    assert.equal(manifest.geography, product.geography, `${id}: wrong geography`);
    assert.equal(model.geographyType, product.geography === 'msa' ? 'city' : 'state', `${id}: backend geography differs`);
    assert.deepEqual(locations.locations.map((location) => location.id).sort(), [...model.locations.full].sort(), `${id}: location coverage differs from backend`);
    assert.equal(manifest.locations.count, model.locations.full.length, `${id}: wrong location count`);
    assert.equal(manifest.locations.index, 'locations.json', `${id}: wrong index reference`);
    assert.equal(manifest.locations.artifact_pattern, 'locations/{location}/{stage}.json', `${id}: unsupported artifact paths`);
    assert.deepEqual(Object.keys(manifest.stages).sort(), ['ehe', 'ryan-white'], `${id}: both stages are required`);
    assert.equal(manifest.stages.ehe.sample_count, 1000, `${id}: incorrect EHE sample count`);
    assert.equal(manifest.stages['ryan-white'].sample_count, product.samples, `${id}: incorrect Ryan White sample count`);
    assert.equal(manifest.stages.ehe.simulation_release, product.geography === 'msa' ? 'ehe-msa-v1.0.0' : 'ehe-state-v1.0.0', `${id}: wrong EHE source`);
    assert.equal(manifest.stages['ryan-white'].simulation_release, model.dataSource.release, `${id}: service fit differs from deployed simulation source`);
    for (const location of locations.locations) {
      assert.deepEqual(Object.keys(location.artifacts).sort(), ['ehe', 'ryan-white'], `${id}/${location.id}: missing stage`);
      for (const [stage, artifact] of Object.entries(location.artifacts)) {
        assert.equal(artifact.path, `locations/${location.id}/${stage}.json`, `${id}: unexpected artifact path`);
        assert.match(artifact.sha256, /^[0-9a-f]{64}$/, `${id}: missing artifact checksum`);
        assert.ok(Number.isInteger(artifact.size_bytes) && artifact.size_bytes > 0, `${id}: invalid artifact size`);
        assert.equal(artifact.simulation_source.release, manifest.stages[stage].simulation_release, `${id}: index stage source differs`);
      }
    }
  }
  return files;
}
