#!/usr/bin/env node

import { readFileSync } from "node:fs";

const configPath = new URL("../.github/config/models.json", import.meta.url);
const config = JSON.parse(readFileSync(configPath, "utf8"));
const errors = [];

function check(condition, message) {
  if (!condition) errors.push(message);
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

for (const [modelId, model] of Object.entries(config)) {
  if (modelId.startsWith("_") || !model || typeof model !== "object") continue;

  const custom = model.customSimulation;
  if (!custom || custom.simulationScript !== "simple_ryan_white.R") continue;

  check(
    custom.interventionType === "permanent_cessation",
    `${modelId}: Ryan White custom simulations must declare permanent_cessation`,
  );
  const timing = custom.timing;
  check(timing && typeof timing === "object", `${modelId}: customSimulation.timing is required`);
  if (!timing || typeof timing !== "object") continue;

  const numericFields = [
    "interventionStartTime",
    "lossLagYears",
    "simulationStartYear",
    "simulationEndYear",
    "reportingStartYear",
    "reportingEndYear",
  ];
  for (const field of numericFields) {
    check(isFiniteNumber(timing[field]), `${modelId}: timing.${field} must be numeric`);
  }
  for (const field of [
    "simulationStartYear",
    "simulationEndYear",
    "reportingStartYear",
    "reportingEndYear",
  ]) {
    check(Number.isInteger(timing[field]), `${modelId}: timing.${field} must be a whole-number year`);
  }

  if (numericFields.every((field) => isFiniteNumber(timing[field]))) {
    check(timing.lossLagYears >= 0, `${modelId}: lossLagYears cannot be negative`);
    check(
      timing.simulationStartYear < timing.simulationEndYear,
      `${modelId}: simulation period must be ordered`,
    );
    check(
      timing.interventionStartTime >= timing.simulationStartYear &&
        timing.interventionStartTime <= timing.simulationEndYear,
      `${modelId}: intervention must fall within the simulation period`,
    );
    check(
      timing.reportingStartYear >= timing.simulationStartYear &&
        timing.reportingEndYear <= timing.simulationEndYear &&
        timing.reportingStartYear <= timing.reportingEndYear,
      `${modelId}: reporting period must be ordered and contained in the simulation period`,
    );
  }
}

const croiTiming = config["ryan-white-state-croi"]?.customSimulation?.timing;
check(croiTiming?.interventionStartTime === 2026.5, "CROI: interruption must begin in July 2026");
check(croiTiming?.lossLagYears === 0.25, "CROI: suppression effect lag must be three months");
check(croiTiming?.reportingStartYear === 2026, "CROI: reporting must begin in 2026");
check(croiTiming?.reportingEndYear === 2031, "CROI: reporting must end in 2031");

if (errors.length > 0) {
  console.error(`Model configuration validation failed (${errors.length}):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log("Model configuration timing contracts passed");
