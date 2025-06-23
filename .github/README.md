# GitHub Actions Plot Generation

This directory contains the GitHub Actions workflow for cloud-based JHEEM plot generation.

## Current Status: Development Phase ⚠️

The workflow is currently in **mock mode** while we prepare the production components:

### ✅ **Working Now**
- Workflow orchestration and matrix strategy
- Configuration generation and city distribution  
- R environment setup and dependency installation
- Mock plot generation simulation

### 🔄 **In Development**  
- Simulation data packaging and distribution
- Production R script integration
- AWS credentials and infrastructure setup

### ❌ **Pending AWS Account**
- Production S3 bucket and DynamoDB setup
- Real plot upload and database registration
- Production API Gateway integration

## Workflow Overview

### 1. **Prepare Job**
- Generates orchestration configuration based on input type (test/medium/full)
- Extracts city list for matrix strategy
- Uploads configuration as artifact

### 2. **Generate Plots Job** (Matrix Strategy)
- Runs one job per city in parallel (configurable max-parallel)
- Sets up R environment with JHEEM dependencies
- Downloads simulation data (currently mocked)
- Generates plots using batch_plot_generator.R (currently mocked)
- Uploads to S3 and registers in database (currently mocked)

### 3. **Summarize Job**
- Collects results from all city jobs
- Provides execution summary and next steps

## Usage

### Manual Trigger
1. Go to GitHub Actions tab in repository
2. Select "Generate JHEEM Plots" workflow  
3. Click "Run workflow"
4. Choose configuration type:
   - `test`: 4 cities, ~108 plots
   - `medium`: 6 cities, ~900 plots
   - `full`: 31 cities, ~64K plots
5. Set max parallel jobs (default: 4)

### Expected Performance
Based on local testing results:
- **Test config**: ~2-3 minutes
- **Medium config**: ~5-10 minutes  
- **Full config**: ~2-6 hours (estimated)

## Production Deployment Checklist

### Phase 1: Simulation Data ⏳
- [ ] Package simulation data by city (~110MB each)
- [ ] Upload to GitHub Releases
- [ ] Update workflow to download real data

### Phase 2: R Environment ⏳
- [ ] Copy batch_plot_generator.R to workflow
- [ ] Copy required utility scripts and dependencies
- [ ] Test R environment setup in GitHub Actions

### Phase 3: AWS Integration ⏳  
- [ ] Set up production AWS account
- [ ] Create S3 bucket: jheem-plots-production
- [ ] Create DynamoDB table: jheem-plot-metadata-production
- [ ] Deploy API Gateway with custom domain (api.jheem.org)
- [ ] Configure GitHub Secrets for AWS credentials

### Phase 4: Production Deployment ⏳
- [ ] Replace mock calls with real AWS integration
- [ ] Full end-to-end testing with small config
- [ ] Production deployment of 64K plots

## Development Testing

To test the current mock workflow:

```bash
# Push workflow to GitHub
git add .github/workflows/generate-plots.yml
git commit -m "Add GitHub Actions plot generation workflow"
git push

# Then trigger manually via GitHub UI
```

The mock workflow will simulate the complete process and provide timing estimates for production deployment.
