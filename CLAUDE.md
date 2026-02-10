# JHEEM Backend - Architecture Reference

Central orchestration hub for JHEEM data generation workflows. Hosts `models.json` (the single source of truth for all model configurations) and reusable GitHub Actions workflows.

## System Context

```
jheem-backend (this repo)
├── models.json (configuration source of truth)
└── workflows (data generation orchestration)

jheem-portal (frontend)
├── syncs config from models.json at build time
└── serves interactive explorers

jheem-simulations (data artifacts)
└── GitHub Releases with simulation files

jheem-*-container (R containers)
└── Extract outcomes from simulation files
```

**Data flow:** GitHub Releases → R containers (via workflow) → S3 → CloudFront → Portal

## Key Files

| File | Purpose |
|------|---------|
| `.github/config/models.json` | Model configurations (locations, scenarios, outcomes, containers, outputs) |
| `.github/workflows/_generate-data-template.yml` | Reusable workflow template (~590 lines) |
| `.github/workflows/generate-*.yml` | Thin wrapper workflows (~40 lines each) |

## models.json Structure

Each model entry defines:

```json
{
  "model-id": {
    "displayName": "...",
    "geographyType": "city|state",
    "locations": { "test": [...], "full": [...] },
    "scenarios": [{ "id": "...", "label": "...", "filePatterns": [...] }],
    "outcomes": [...],
    "facets": [...],
    "container": { "image": "...", "version": "..." },
    "dataSource": { "type": "GitHub-Release", "release": "..." },
    "output": { "s3Path": "...", "cloudfrontUrl": "..." },
    "summaryMetrics": { ... }
  }
}
```

The portal syncs this at build time to `src/config/model-configs.ts`.

## Current Models

| Model ID | Display Name | Geography | Locations |
|----------|--------------|-----------|-----------|
| `ryan-white-msa` | Ryan White MSA | city | 31 cities |
| `ryan-white-state-ajph` | AJPH (11 States) | state | 11 states |
| `ryan-white-state-croi` | CROI (30 States) | state | 30 states |
| `cdc-testing` | CDC Testing | state | 18 states |

## Workflow Architecture

### Template Pattern
The reusable template (`_generate-data-template.yml`) handles:
1. **Prepare**: Load config from models.json, resolve locations
2. **Generate**: Matrix strategy runs R container per location in parallel
3. **Finalize**: Combine summaries, upload to S3, invalidate CloudFront

Thin wrappers just specify `model_id` and expose workflow_dispatch inputs.

### Adding a New Model

1. **Add config to models.json** - Define locations, scenarios, outcomes, container, output paths
2. **Create thin wrapper workflow** - Copy existing `generate-*.yml`, change `model_id`
3. **Create container** (if new extraction logic needed) - See existing `jheem-*-container` repos
4. **Upload simulations** - Create GitHub Release in `jheem-simulations`
5. **Create portal route** - Add page in `jheem-portal`

## Infrastructure

| Resource | Value |
|----------|-------|
| S3 Bucket | `jheem-data-production` |
| CloudFront Distribution | `E3VDQ7V9FBIIGD` |
| CloudFront Domain | `d320iym4dtm9lj.cloudfront.net` |
| Container Registry | `ghcr.io/ncsizemore/jheem-*` |

### S3/CloudFront Paths

| Model | S3 Path | CloudFront Path |
|-------|---------|-----------------|
| MSA | `portal/ryan-white/` | `/ryan-white/` |
| AJPH | `portal/ryan-white-state/` | `/ryan-white-state/` |
| CROI | `portal/ryan-white-state-croi/` | `/ryan-white-state-croi/` |
| CDC Testing | `portal/cdc-testing/` | `/cdc-testing/` |

## Architectural Decisions

### Why models.json as source of truth?
- Single place to update model config (DRY)
- Frontend syncs at build time (type-safe)
- Workflows read at runtime (no duplication)
- Makes adding new models mechanical

### Why reusable workflow template?
- 54% code reduction (1,270 → 590 lines across 4 workflows)
- Consistent behavior across models
- Thin wrappers are easy to create/maintain

### Why GitHub Releases for simulation data?
- Free egress (vs S3 ~$1/run)
- Versioned and immutable
- Easy to reference in workflows

### Why ghcr.io for containers?
- Free (vs ECR ~$7/run for pulls)
- Integrated with GitHub Actions
- Semver tags for reproducibility

## Serverless Infrastructure (Dormant)

The `serverless.yml`, `infrastructure/`, and `src/` directories contain Lambda/DynamoDB infrastructure that is **not currently active** but may be used for future custom simulation features.

**Context:** The legacy Shiny apps had two modes:
1. **Prerun** - Plot pre-generated simulations (now handled by GitHub Actions workflows)
2. **Custom** - Run simulations with user-specified parameters (would use serverless)

The prerun pipeline has been migrated to workflows + S3/CloudFront. Custom simulations remain a potential future feature that could leverage the existing serverless infrastructure.
