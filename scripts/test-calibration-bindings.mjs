import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import test from 'node:test';
import { validateBindings, validateBindingArtifacts } from './calibration-bindings.mjs';

const source = JSON.parse(fs.readFileSync(new URL('../.github/config/models.json', import.meta.url)));
const promotion = JSON.parse(fs.readFileSync(new URL('../.github/config/calibration-promotion.json', import.meta.url)));

function fixture(context, mutate = () => {}) {
  const config = structuredClone(source);
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'calibration-binding-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const { id, product, binding, config: model } of validateBindings(config, promotion)) {
    const identity = { release: binding.release, model: product.model, portal_model: product.portal };
    const stages = {
      ehe: { sample_count: 1000, simulation_release: product.geography === 'msa' ? 'ehe-msa-v1.0.0' : 'ehe-state-v1.0.0' },
      'ryan-white': { sample_count: product.samples, simulation_release: model.dataSource.release },
    };
    const manifest = { ...identity, schema_version: 'jheem-calibration-manifest/v1',
      geography: product.geography, stages,
      locations: { count: model.locations.full.length, index: 'locations.json', artifact_pattern: 'locations/{location}/{stage}.json' },
    };
    const locations = { ...identity, schema_version: 'jheem-calibration-location-index/v1',
      locations: model.locations.full.map((location) => ({ id: location,
        artifacts: Object.fromEntries(Object.entries(stages).map(([stage, details]) => [stage, {
          path: `locations/${location}/${stage}.json`, sha256: 'a'.repeat(64), size_bytes: 100,
          simulation_source: { release: details.simulation_release },
        }])),
      })),
    };
    // Rehash mutated documents so semantic failures cannot be hidden behind checksum failures.
    mutate({ id, manifest, locations });
    fs.mkdirSync(path.join(root, product.model));
    for (const [name, payload, field] of [
      ['manifest.json', manifest, 'manifestSha256'], ['locations.json', locations, 'locationIndexSha256'],
    ]) {
      const bytes = JSON.stringify(payload);
      fs.writeFileSync(path.join(root, product.model, name), bytes);
      binding[field] = crypto.createHash('sha256').update(bytes).digest('hex');
    }
  }
  return { config, root };
}

test('accepts bindings for all deployed locations and both scientific stages', (context) => {
  const { config, root } = fixture(context);
  assert.equal(validateBindingArtifacts(config, promotion, root).length, 6);
});

test('rejects missing bindings, cross-model URLs, malformed checksums, and unreviewed facets', () => {
  for (const mutate of [
    (config) => { delete config['ryan-white-msa'].calibration; },
    (config) => { config['ryan-white-state-ajph'].calibration.manifestUrl = config['ryan-white-state-croi'].calibration.manifestUrl; },
    (config) => { config['ryan-white-msa'].calibration.locationIndexSha256 = 'unknown'; },
    (config) => { config['ryan-white-msa'].calibration.displayFacets.push('race'); },
    (config) => { config['cdc-testing'].calibration = config['ryan-white-msa'].calibration; },
  ]) {
    const config = structuredClone(source);
    mutate(config);
    assert.throws(() => validateBindings(config, promotion));
  }
});

test('rejects changed location-index bytes even when JSON still parses', (context) => {
  const { config, root } = fixture(context);
  fs.appendFileSync(path.join(root, 'ryan-white-msa/locations.json'), ' ');
  assert.throws(() => validateBindingArtifacts(config, promotion, root), /locations.json checksum differs/);
});

test('rejects incorrect sample counts rather than relabeling the 80-draw city fit', (context) => {
  const { config, root } = fixture(context, ({ manifest }) => { manifest.stages['ryan-white'].sample_count = 999; });
  assert.throws(() => validateBindingArtifacts(config, promotion, root), /incorrect Ryan White sample count/);
});

test('rejects geographic and stage omissions with correctly rehashed documents', (context) => {
  for (const [mutate, expected] of [
    [({ locations }) => { locations.locations.pop(); }, /location coverage differs/],
    [({ manifest }) => { delete manifest.stages.ehe; }, /both stages are required/],
    [({ manifest }) => { manifest.geography = 'wrong'; }, /wrong geography/],
    [({ locations }) => { locations.locations[0].artifacts.ehe.path = '../wrong.json'; }, /unexpected artifact path/],
  ]) {
    const { config, root } = fixture(context, mutate);
    assert.throws(() => validateBindingArtifacts(config, promotion, root), expected);
  }
});

test('rejects a fitting source that differs from the deployed model release', (context) => {
  const { config, root } = fixture(context, ({ manifest }) => {
    manifest.stages['ryan-white'].simulation_release = 'unrelated-fit';
  });
  assert.throws(() => validateBindingArtifacts(config, promotion, root), /service fit differs from deployed/);
});
