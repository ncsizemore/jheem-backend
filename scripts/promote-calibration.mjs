#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';
import { createPlan, createAwsStorage, promote, verifyDelivery } from './calibration-promotion.mjs';

const config = JSON.parse(fs.readFileSync(new URL('../.github/config/calibration-promotion.json', import.meta.url)));
const args = process.argv.slice(2);
const options = { mode: 'plan' };
for (let i = 0; i < args.length; i += 2) {
  if (!['--consumer', '--output', '--mode'].includes(args[i]) || !args[i + 1]) throw new Error('Use --consumer DIR --output NEW_DIR [--mode plan|promote]');
  options[args[i].slice(2)] = args[i + 1];
}
if (!options.consumer || !options.output || !['plan', 'promote'].includes(options.mode)) throw new Error('Invalid promotion arguments');
const consumer = path.resolve(options.consumer);
const output = path.resolve(options.output);
const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: consumer, encoding: 'utf8' }).trim();
const dirty = execFileSync('git', ['status', '--porcelain', '--untracked-files=no'], { cwd: consumer, encoding: 'utf8' }).trim();
if (head !== config.consumer_commit || dirty) throw new Error('Consumer checkout must be clean at the pinned commit');
if (fs.existsSync(output)) throw new Error('Output directory must be new');
const descriptor = JSON.parse(fs.readFileSync(path.join(consumer, 'config/calibration-release-source.json')));
if (descriptor.tag !== config.release) throw new Error('Consumer release differs from promotion pin');
const { fetchCalibrationRelease } = await import(pathToFileURL(path.join(consumer, 'scripts/lib/calibration-release-fetch.mjs')));
const { stageCalibrationRelease } = await import(pathToFileURL(path.join(consumer, 'scripts/lib/calibration-release-consumer.mjs')));
fs.mkdirSync(output, { recursive: true });
await fetchCalibrationRelease({ rawDescriptor: descriptor, outputDirectory: path.join(output, 'release') });
const staticRoot = path.join(output, 'static');
stageCalibrationRelease({ rawDescriptor: descriptor, sourceDirectory: path.join(output, 'release'), outputDirectory: staticRoot });
const plan = createPlan(staticRoot, config);
fs.writeFileSync(path.join(output, 'plan.json'), `${JSON.stringify(plan, null, 2)}\n`);
console.log(JSON.stringify({ mode: options.mode, ...plan, files: undefined }, null, 2));
if (options.mode === 'promote') {
  const result = await promote(plan, createAwsStorage(config, staticRoot),
    (file) => verifyDelivery(config, file), console.log);
  fs.writeFileSync(path.join(output, 'result.json'), `${JSON.stringify(result, null, 2)}\n`);
  console.log(JSON.stringify(result));
}
