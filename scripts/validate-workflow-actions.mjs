#!/usr/bin/env node

import { readFileSync, readdirSync } from "node:fs";

const workflowsDirectory = new URL("../.github/workflows/", import.meta.url);
const expectedActions = new Map([
  ["actions/checkout", {
    ref: "3d3c42e5aac5ba805825da76410c181273ba90b1",
    version: "v7.0.1",
  }],
  ["actions/setup-node", {
    ref: "820762786026740c76f36085b0efc47a31fe5020",
    version: "v7.0.0",
  }],
  ["actions/upload-artifact", {
    ref: "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    version: "v7.0.1",
  }],
  ["actions/download-artifact", {
    ref: "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
    version: "v8.0.1",
  }],
  ["aws-actions/configure-aws-credentials", {
    ref: "e6de054238d6b7531b4efff3b6587d9aade6a06c",
    version: "v6.2.3",
  }],
  ["docker/login-action", {
    ref: "dbcb813823bdd20940b903addbd779551569679f",
    version: "v4.6.0",
  }],
]);

const workflowFiles = readdirSync(workflowsDirectory, { withFileTypes: true })
  .filter((entry) => entry.isFile() && /\.ya?ml$/.test(entry.name))
  .map((entry) => entry.name)
  .sort();
const errors = [];
const seenActions = new Set();
let externalUseCount = 0;

for (const workflowFile of workflowFiles) {
  const workflow = readFileSync(new URL(workflowFile, workflowsDirectory), "utf8");
  const lines = workflow.split(/\r?\n/);

  for (const [index, line] of lines.entries()) {
    const usesMatch = line.match(/^\s*uses:\s*([^@\s]+)@([^\s#]+)(?:\s+#\s*(\S+))?\s*$/);
    if (usesMatch) {
      const [, action, ref, documentedVersion] = usesMatch;
      if (action.startsWith("./")) continue;

      externalUseCount += 1;
      seenActions.add(action);
      const expected = expectedActions.get(action);
      if (!expected) {
        errors.push(`${workflowFile}:${index + 1}: unreviewed external action ${action}`);
        continue;
      }
      if (ref !== expected.ref) {
        errors.push(
          `${workflowFile}:${index + 1}: ${action} must use immutable ref ${expected.ref}`,
        );
      }
      if (documentedVersion !== expected.version) {
        errors.push(
          `${workflowFile}:${index + 1}: ${action} must document ${expected.version}`,
        );
      }
    }

    const nodeVersionMatch = line.match(/^\s*node-version:\s*['"]?([^'"\s#]+)/);
    if (nodeVersionMatch && nodeVersionMatch[1] !== "24") {
      errors.push(
        `${workflowFile}:${index + 1}: workflow toolchain must use supported Node 24 LTS`,
      );
    }
  }
}

for (const action of expectedActions.keys()) {
  if (!seenActions.has(action)) {
    errors.push(`expected reviewed action is not used by an active workflow: ${action}`);
  }
}

if (errors.length > 0) {
  console.error(`Workflow action validation failed (${errors.length}):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(
  `Workflow action policy passed (${workflowFiles.length} active workflows, ` +
    `${externalUseCount} pinned external uses)`,
);
