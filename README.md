# JHEEM Backend

Central orchestration for JHEEM data generation workflows. This repository hosts:

- **`models.json`** - Single source of truth for all model configurations
- **Reusable workflow template** - Handles data extraction, aggregation, and deployment
- **Thin wrapper workflows** - Model-specific entry points

## Architecture

```
GitHub Releases          R Containers              S3              CloudFront         Portal
(simulation data)   →   (data extraction)    →   (storage)   →   (CDN)         →   (frontend)
     │                        │                      │              │
     └────────────────────────┴──────────────────────┴──────────────┘
                         Orchestrated by GitHub Actions workflows
```

## Current Models

| Workflow | Model | Locations | Output |
|----------|-------|-----------|--------|
| `generate-msa.yml` | Ryan White MSA | 31 cities | `/ryan-white/` |
| `generate-ajph.yml` | AJPH State Analysis | 11 states | `/ryan-white-state/` |
| `generate-croi.yml` | CROI State Analysis | 30 states | `/ryan-white-state-croi/` |
| `generate-cdc-testing.yml` | CDC Testing | 18 states | `/cdc-testing/` |

## Running a Workflow

1. Go to **Actions** tab
2. Select the workflow (e.g., "Generate MSA Data")
3. Click **Run workflow**
4. Choose:
   - `location_set`: `test` (3 locations) or `full` (all locations)
   - `dry_run`: Skip S3 upload for testing
   - `max_parallel`: Concurrent jobs (default varies by model)
5. Monitor progress in Actions dashboard

Data is uploaded to S3 and served via CloudFront at `https://d320iym4dtm9lj.cloudfront.net`.

## Adding a New Model

### 1. Add configuration to models.json

Edit `.github/config/models.json`:

```json
{
  "my-new-model": {
    "displayName": "My New Model",
    "geographyType": "state",
    "locations": {
      "test": ["AL", "CA", "FL"],
      "full": ["AL", "CA", "FL", "GA", "NY", "TX"]
    },
    "scenarios": [
      { "id": "baseline", "label": "Baseline" },
      { "id": "intervention", "label": "Intervention", "filePatterns": ["intr"] }
    ],
    "outcomes": ["incidence", "prevalence"],
    "facets": ["none", "age", "race", "sex"],
    "container": {
      "image": "ghcr.io/ncsizemore/my-container",
      "version": "1.0.0"
    },
    "dataSource": {
      "type": "GitHub-Release",
      "repository": "ncsizemore/jheem-simulations",
      "release": "my-model-v1.0.0",
      "filePattern": "my_model_{STATE}_*.Rdata"
    },
    "output": {
      "s3Bucket": "jheem-data-production",
      "s3Path": "portal/my-model",
      "cloudfrontUrl": "https://d320iym4dtm9lj.cloudfront.net/my-model",
      "summaryFile": "state-summaries.json"
    },
    "interventionStartYear": 2025,
    "summaryMetrics": {
      "statusMetrics": [
        { "outcome": "prevalence", "year": 2024, "label": "Prevalence", "format": "count" }
      ],
      "impactOutcome": "incidence"
    }
  }
}
```

### 2. Create thin wrapper workflow

Create `.github/workflows/generate-my-model.yml`:

```yaml
name: Generate My Model Data

on:
  workflow_dispatch:
    inputs:
      location_set:
        description: 'Locations to generate'
        required: true
        default: 'test'
        type: choice
        options:
          - test
          - full
      dry_run:
        description: 'Skip S3 uploads'
        required: true
        default: false
        type: boolean

jobs:
  generate:
    uses: ./.github/workflows/_generate-data-template.yml
    with:
      model_id: 'my-new-model'
      location_set: ${{ inputs.location_set }}
      dry_run: ${{ inputs.dry_run }}
    secrets: inherit
```

### 3. Upload simulation data

Create a GitHub Release in `ncsizemore/jheem-simulations`:
- Tag: `my-model-v1.0.0`
- Upload `.Rdata` files matching your `filePattern`

### 4. Create R container (if needed)

If your model requires different extraction logic, create a new container repository following the pattern in existing `jheem-*-container` repos.

### 5. Add portal route

In `jheem-portal`, create a route page that uses the shared components with your model's config.

## Repository Structure

```
.github/
├── config/
│   └── models.json              # Model configurations
└── workflows/
    ├── _generate-data-template.yml  # Reusable template
    ├── generate-msa.yml             # MSA wrapper
    ├── generate-ajph.yml            # AJPH wrapper
    ├── generate-croi.yml            # CROI wrapper
    └── generate-cdc-testing.yml     # CDC Testing wrapper

docs/                            # Architecture documentation
```

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [jheem-portal](https://github.com/ncsizemore/jheem-portal) | Next.js frontend |
| [jheem-simulations](https://github.com/ncsizemore/jheem-simulations) | Simulation data (GitHub Releases) |
| jheem-*-container | R containers for data extraction |

## Infrastructure

| Resource | Value |
|----------|-------|
| S3 Bucket | `jheem-data-production` |
| CloudFront Distribution | `E3VDQ7V9FBIIGD` |
| CloudFront Domain | `d320iym4dtm9lj.cloudfront.net` |

## Serverless Infrastructure

The `serverless.yml` and `infrastructure/` directories contain Lambda/DynamoDB infrastructure that is **not currently active** but preserved for potential future use.

**Background:** The legacy Shiny apps supported two modes:
- **Prerun simulations** - Now handled by the GitHub Actions workflows above
- **Custom simulations** - User-specified parameters, run on-demand

The custom simulation feature could leverage the existing serverless infrastructure if implemented in the future.
