#!/usr/bin/env node
import fs from 'node:fs';
import { validateBindings, validateBindingArtifacts } from './calibration-bindings.mjs';
import { verifyDelivery } from './calibration-promotion.mjs';

const config = JSON.parse(fs.readFileSync(new URL('../.github/config/models.json', import.meta.url)));
const promotion = JSON.parse(fs.readFileSync(new URL('../.github/config/calibration-promotion.json', import.meta.url)));
const args = process.argv.slice(2);
if (args.length === 0) {
  validateBindings(config, promotion);
  console.log('Calibration configuration bindings passed (3 products)');
} else {
  if (args[0] !== '--artifacts' || !args[1] || args.length > 3 ||
      (args.length === 3 && args[2] !== '--delivery')) throw new Error('Use [--artifacts DIR [--delivery]]');
  const files = validateBindingArtifacts(config, promotion, args[1]);
  if (args[2] === '--delivery') {
    for (const file of files) await verifyDelivery(promotion, file);
  }
  console.log(`Calibration manifest and location bindings passed (${files.length} files; CloudFront ${args[2] ? 'verified' : 'not requested'})`);
}
