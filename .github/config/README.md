# JHEEM Configuration Registry

This directory contains the **single source of truth** for all JHEEM model configurations.

## Files

- `models.json` - Complete configuration for all models (MSA, AJPH, CROI, CDC Testing)

## Purpose

Previously, configuration was scattered across:
- Workflow environment variables (SCENARIOS, OUTCOMES, FACETS)
- Portal `model-configs.ts`
- Container entrypoint scripts
- Aggregation scripts

This led to sync issues when configurations changed.

Now, `models.json` serves as the canonical source. Workflows read from it, and the portal can import or fetch it at build time.

## Structure

Each model entry contains:

```json
{
  "model-id": {
    // Display info
    "displayName": "Human readable name",
    "shortName": "Short label",
    "description": "What this model does",

    // Geography
    "geographyType": "city" | "state",
    "geographyLabel": "City" | "State",
    "locations": {
      "test": ["subset for testing"],
      "full": ["all locations"]
    },

    // Model configuration
    "scenarios": [{ "id", "label", "description" }],
    "outcomes": ["list of outcome IDs"],
    "facets": ["list of facet combinations"],
    "statistics": { "base": [], "all": [] },

    // Infrastructure
    "container": { "image", "version", "repository" },
    "dataSource": { "type", "path/release", "patterns" },
    "output": { "s3Path", "cloudfrontUrl", "summaryFile" },

    // Frontend settings
    "defaults": { "outcome", "statistic" },
    "map": { "center", "zoom" },
    "interventionStartYear": 2025,

    // Workflow settings
    "workflow": { "maxParallel", "includeIndividualSimulation" }
  }
}
```

## Usage in Workflows

Workflows can read configuration using `jq`:

```yaml
- name: Load model config
  id: config
  run: |
    MODEL_ID="ryan-white-msa"
    CONFIG_FILE=".github/config/models.json"

    # Extract scenarios as comma-separated list
    SCENARIOS=$(jq -r ".\"$MODEL_ID\".scenarios | map(.id) | join(\",\")" $CONFIG_FILE)
    echo "SCENARIOS=$SCENARIOS" >> $GITHUB_ENV

    # Extract outcomes
    OUTCOMES=$(jq -r ".\"$MODEL_ID\".outcomes | join(\",\")" $CONFIG_FILE)
    echo "OUTCOMES=$OUTCOMES" >> $GITHUB_ENV

    # Extract locations (full set)
    LOCATIONS=$(jq -c ".\"$MODEL_ID\".locations.full" $CONFIG_FILE)
    echo "locations=$LOCATIONS" >> $GITHUB_OUTPUT
```

## Usage in Portal

The portal can:

1. **Fetch at build time** (recommended):
   ```typescript
   // next.config.js or build script
   const config = await fetch('https://raw.githubusercontent.com/.../models.json');
   ```

2. **Import directly** (if copied to portal):
   ```typescript
   import modelsJson from '@/config/models.json';
   ```

3. **Generate TypeScript** from JSON:
   ```bash
   npx json-schema-to-typescript models.schema.json > models.d.ts
   ```

## Adding a New Model

1. Add entry to `models.json` with all required fields
2. Create thin workflow wrapper (see `workflows/generate-{model}.yml`)
3. Add route in portal
4. Done!

## Versioning

The `_meta.version` field tracks schema changes:
- `1.0.0` - Initial version

When making breaking changes to the schema, increment the major version.

## Container Versions

**Important**: Container `version` fields should use semver tags (e.g., `v1.0.0`), not `latest`.

Using `:latest` makes builds non-reproducible. Tag container releases and reference specific versions here.
