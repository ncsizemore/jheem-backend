# Session Summary: Infrastructure & Cost Optimization
**Date:** January 8, 2025

## Overview

This session focused on optimizing cloud costs for the JHEEM data generation pipeline and establishing infrastructure for the state-level Ryan White model.

## Key Accomplishments

### 1. Container Registry Optimization
**Problem:** ECR data transfer costs (~$7/run) when pulling container images from GitHub Actions.

**Solution:** Added ghcr.io (GitHub Container Registry) as third registry alongside Docker Hub and ECR.

**Changes:**
- `jheem-container-minimal/.github/workflows/build-and-push.yml` - Now pushes to all three registries
- `jheem-backend/.github/workflows/generate-native-data.yml` - Pulls from ghcr.io instead of ECR

**Cost Impact:** ECR pulls from GitHub Actions: ~$7 → $0

### 2. Simulation Hosting via GitHub Releases
**Problem:** S3 data transfer costs (~$1/run) when downloading simulation files.

**Solution:** Host simulations on GitHub Releases (free egress) instead of S3.

**Changes:**
- Created `ncsizemore/jheem-simulations` repo
- Uploaded `ryan-white-state-v1.0.0` release (11 states, 44 files, ~2.8GB)
- State-level workflow downloads from GitHub Releases

**Cost Impact:** S3 simulation downloads: ~$1/run → $0

### 3. State-Level Workflow
**Created:** `.github/workflows/generate-native-data-ryan-white-state.yml`

**Key findings:**
- Same container works for both MSA and state-level (no separate container needed)
- Container treats location generically - accepts state codes (AL, CA) just like MSA codes (C.12580)
- Simulations mounted to `simulations/ryan-white/` regardless of model variant

**Features:**
- `dry_run` option to skip S3 uploads for testing
- Downloads simulations from GitHub Releases
- Uses `generate-state-summaries.ts` for state-specific hover card data

### 4. Streaming JSON Aggregation
**Problem:** `RangeError: Invalid string length` when aggregating state-level data (~394MB per state).

**Solution:** Implemented streaming JSON output using `big-json` library.

**Changes:**
- `jheem-portal/scripts/aggregate-city-data.ts` - Uses streaming instead of `JSON.stringify()`

**Impact:** No longer limited by JavaScript's ~512MB string limit. Works for any size data.

### 5. State-Level Data Infrastructure
**Created in jheem-portal:**
- `src/data/states.ts` - 11 states with coordinates
- `scripts/generate-state-summaries.ts` - State-specific summary generation for map hover cards

## Architecture Decisions

### Single Container Strategy
- One container (`ghcr.io/ncsizemore/jheem-ryan-white-model`) serves both MSA and state-level
- Specification treats location generically
- Simpler maintenance, guaranteed consistency

### Separate Workflows
- `generate-native-data.yml` - MSA-level (31 cities)
- `generate-native-data-ryan-white-state.yml` - State-level (11 states)
- Separate concerns, clear ownership, can evolve independently

### jheem_analyses Versioning
- Container pinned to commit `fc3fe1d2` (July 2025)
- Ryan White papers published → simulations static → stability over new features
- Future models can use appropriate commits for their simulations

### Separate Repos per Model (Option A)
- Decided against monorepo for now
- "Freeze" benefit valuable for published models
- Reassess at 5+ models if repo sprawl becomes painful

## Cost Summary

| Item | Before | After |
|------|--------|-------|
| ECR container pulls | ~$7/run | $0 (ghcr.io) |
| S3 simulation downloads | ~$1/run | $0 (GitHub Releases)* |
| **Total per full run** | **~$8** | **~$0-1** |

*MSA simulations still on S3 until migrated (~$1 one-time cost to download)

## Repositories Affected

| Repo | Changes |
|------|---------|
| `jheem-container-minimal` | Added ghcr.io to build pipeline |
| `jheem-backend` | Updated MSA workflow, added state workflow |
| `jheem-portal` | Added streaming JSON, state data/scripts |
| `jheem-simulations` | NEW - hosts simulation releases |

## Next Steps

### Immediate
- [ ] Run state-level workflow with `dry_run=false` to test full pipeline including S3 upload
- [ ] Verify state summary generation works end-to-end

### Short-term
- [ ] Migrate MSA simulations to GitHub Releases (~$1 S3 download cost)
- [ ] Update MSA workflow to use GitHub Releases
- [ ] Design state-level map UI (choropleth vs markers)

### Future
- [ ] Parameterize `--simulation-root` in container (optional enhancement)
- [ ] Consider combined MSA + state map view in portal

## URL Migration Notes

**Published paper URLs to preserve:**
- State-level paper references: `https://jheem.org/ryan-white-state-level`
  - Currently: landing page for Shiny app
  - After migration: redirect to `/ryan-white/state/explorer`
- MSA paper URL: TBD (need to check paper)

**Route Structure (Option C - DECIDED):**
- `/ryan-white/msa/explorer` → MSA marker map
- `/ryan-white/state/explorer` → State choropleth map
- `/ryan-white/` → Landing page for both (refactored)

*Note: Option C was selected as the final route structure. Options A and B are not documented here as they were not chosen.*

**Choropleth prototype:**
- Created `StateMapSample.tsx` with synthetic data
- Route: `/ryan-white/explorer/state` (temporary for testing)
- Uses GeoJSON fill layers with data-driven coloring
- Matches MSA explorer interaction patterns (hover cards, click to explore)

*Note: This prototype is intentionally temporary scaffolding for cross-machine development. It will either be promoted to a full implementation or removed once the state choropleth is finalized.*

## Files Created/Modified This Session

### New Files
- `jheem-simulations/README.md`
- `jheem-simulations/WORKFLOW_MIGRATION_PLAN.md`
- `jheem-backend/.github/workflows/generate-native-data-ryan-white-state.yml`
- `jheem-portal/src/data/states.ts`
- `jheem-portal/scripts/generate-state-summaries.ts`
- `jheem-portal/src/components/StateMapSample.tsx` - Choropleth prototype
- `jheem-portal/src/app/ryan-white/explorer/state/page.tsx` - Temp route for prototype
- `jheem-portal/public/us-states.json` - GeoJSON for state boundaries

### Modified Files
- `jheem-container-minimal/.github/workflows/build-and-push.yml`
- `jheem-backend/.github/workflows/generate-native-data.yml`
- `jheem-portal/scripts/aggregate-city-data.ts`
- `jheem-portal/package.json` (added big-json dependency)
