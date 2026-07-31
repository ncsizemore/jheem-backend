#!/usr/bin/env node

import { readFileSync } from "node:fs";

const configPath = new URL("../.github/config/models.json", import.meta.url);
const config = JSON.parse(readFileSync(configPath, "utf8"));
const errors = [];
const mirroredWorkflowDefaults = {
  "ryan-white-msa": "../.github/workflows/generate-msa.yml",
  "ryan-white-state-ajph": "../.github/workflows/generate-ajph.yml",
  "ryan-white-state-croi": "../.github/workflows/generate-croi.yml",
  "cdc-testing": "../.github/workflows/generate-cdc-testing.yml",
};
const customSimulationWorkflowPath = "../.github/workflows/run-custom-sim.yml";

function check(condition, message) {
  if (!condition) errors.push(message);
}

function isFiniteNumber(value) {
  return typeof value === "number" && Number.isFinite(value);
}

for (const [modelId, workflowPath] of Object.entries(mirroredWorkflowDefaults)) {
  const container = config[modelId]?.container;
  check(container && typeof container === "object", `${modelId}: container configuration is required`);
  if (!container || typeof container !== "object") continue;

  check(
    /^\d+\.\d+\.\d+$/.test(container.version),
    `${modelId}: container.version must be an exact semver tag`,
  );
  const workflow = readFileSync(new URL(workflowPath, import.meta.url), "utf8");
  const expectedDefault = `default: '${container.image}:${container.version}'`;
  check(
    workflow.includes(expectedDefault),
    `${modelId}: ${workflowPath} must mirror ${container.image}:${container.version}`,
  );
}

const customSimulationWorkflow = readFileSync(
  new URL(customSimulationWorkflowPath, import.meta.url),
  "utf8",
);
for (const requiredFragment of [
  ".metadata.custom_simulation = $custom_simulation",
  ".metadata.custom_simulation == $custom_simulation",
  "request_id:",
  "EXPECTED_REQUEST_ID=\"v1:${MODEL_ID}:${LOCATION}:${SCENARIO_KEY}\"",
  "[ \"$REQUEST_ID\" != \"$EXPECTED_REQUEST_ID\" ]",
  "run_contract_version: \"v1\"",
  "cancel-in-progress: false",
  "Check for an already-published result",
  "skipping duplicate compute",
  "refusing to risk duplicate compute",
]) {
  check(
    customSimulationWorkflow.includes(requiredFragment),
    `${customSimulationWorkflowPath}: missing fail-closed result metadata invariant: ${requiredFragment}`,
  );
}

function validateTimeline(modelId, label, timeline) {
  check(timeline && typeof timeline === "object", `${modelId}/${label}: timeline is required`);
  if (!timeline || typeof timeline !== "object") return;

  for (const field of ["serviceInterruptionStartTime", "suppressionEffectStartTime"]) {
    check(isFiniteNumber(timeline[field]), `${modelId}/${label}: ${field} must be numeric`);
  }
  if (isFiniteNumber(timeline.serviceInterruptionStartTime) &&
      isFiniteNumber(timeline.suppressionEffectStartTime)) {
    check(
      timeline.suppressionEffectStartTime >= timeline.serviceInterruptionStartTime,
      `${modelId}/${label}: suppression effect cannot precede service interruption`,
    );
  }

  const hasResume = timeline.serviceResumeTime !== undefined;
  const hasRecovery = timeline.suppressionRecoveryEndTime !== undefined;
  check(
    hasResume === hasRecovery,
    `${modelId}/${label}: service resume and suppression recovery must be specified together`,
  );
  if (hasResume && hasRecovery) {
    check(isFiniteNumber(timeline.serviceResumeTime), `${modelId}/${label}: serviceResumeTime must be numeric`);
    check(
      isFiniteNumber(timeline.suppressionRecoveryEndTime),
      `${modelId}/${label}: suppressionRecoveryEndTime must be numeric`,
    );
    if (isFiniteNumber(timeline.serviceResumeTime) &&
        isFiniteNumber(timeline.suppressionRecoveryEndTime)) {
      check(
        timeline.serviceResumeTime > timeline.serviceInterruptionStartTime,
        `${modelId}/${label}: service resume must follow interruption`,
      );
      check(
        timeline.suppressionRecoveryEndTime >= timeline.serviceResumeTime,
        `${modelId}/${label}: suppression recovery cannot finish before services resume`,
      );
    }
  }
}

for (const [modelId, model] of Object.entries(config)) {
  if (modelId.startsWith("_") || !model || typeof model !== "object") continue;

  const custom = model.customSimulation;
  if (!custom || custom.simulationScript !== "simple_ryan_white.R") continue;

  for (const scenario of model.scenarios ?? []) {
    validateTimeline(modelId, scenario.id ?? "unnamed-scenario", scenario.timeline);
  }

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

// Scientific regression contract traced to the CROI 2026 model-owner analysis.
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
