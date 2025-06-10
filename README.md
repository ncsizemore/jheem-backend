# JHEEM Backend

A modern serverless backend for the JHEEM epidemiological modeling system, replacing the legacy Shiny application with a scalable cloud-native architecture. Built with AWS Lambda, S3, DynamoDB, and API Gateway, deployable to both LocalStack (development) and AWS (production).

## 🏗️ Architecture Overview

This system implements a **pre-computed plot library** approach, generating 20,160+ epidemiological plots offline and serving them instantly via API. This replaces the slow on-demand computation of the original Shiny app with sub-second plot retrieval.

### Core Components

- **📦 S3 Storage**: Stores pre-generated plot JSON files (~630MB total)
- **🗄️ DynamoDB**: Metadata index enabling intelligent plot discovery
- **⚡ Lambda Functions**: Serverless compute for API endpoints
- **🌐 API Gateway**: RESTful API interface
- **🖥️ Frontend**: Next.js web application (separate repository)

### Data Flow

1. **Offline Generation**: R scripts generate atomic plots as JSON files
2. **Storage & Indexing**: Plots uploaded to S3, metadata stored in DynamoDB  
3. **Discovery**: Frontend queries database to find available plots
4. **Retrieval**: Lambda functions fetch plot data from S3
5. **Visualization**: Frontend renders interactive plots with Plotly.js

## 🚀 Quick Start

### Prerequisites

- **Docker**: For LocalStack development environment
- **Python 3.9+**: For Lambda functions and AWS CLI tools
- **Node.js 16+**: For Serverless Framework
- **Git**: For repository management

### 1. Initial Setup

```bash
# Clone the repository
git clone <jheem-backend-repo>
cd jheem-backend

# Create Python virtual environment for LocalStack tools
python3 -m venv localstack-env
source localstack-env/bin/activate
pip install boto3 awscli-local requests

# Install Node.js dependencies
npm install

# Install Serverless Framework globally (if not already installed)
npm install -g serverless
```

### 2. Start Development Environment

```bash
# Start LocalStack (AWS emulation)
localstack start -d

# Set LocalStack credentials
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Verify LocalStack is running
localstack status
```

### 3. Deploy Backend Services

```bash
# Activate Python environment
source localstack-env/bin/activate

# Deploy all services (Lambda + API Gateway + S3 + DynamoDB)
serverless deploy --stage local
```

**Expected Output:**
```
✔ Service deployed to stack jheem-backend-local (94s)

endpoints:
  GET - http://localhost:4566/restapis/ABC123/local/_user_request_/plot
  GET - http://localhost:4566/restapis/ABC123/local/_user_request_/plots/search
  POST - http://localhost:4566/restapis/ABC123/local/_user_request_/plots/register
functions:
  getPrerunPlot: jheem-backend-local-getPrerunPlot
  searchPlots: jheem-backend-local-searchPlots  
  registerPlot: jheem-backend-local-registerPlot
```

**⚠️ Important**: Note the API Gateway ID (e.g., `ABC123`) - you'll need this for frontend configuration.

### 4. Populate Database with Test Data

```bash
# Register existing test plots in database
python scripts/register_existing_plots.py

# Verify everything works
python scripts/test_discovery.py
```

### 5. Test the System

```bash
# Test plot discovery
curl "http://localhost:4566/restapis/ABC123/local/_user_request_/plots/search?city=C.12580&scenario=cessation"

# Test plot retrieval  
curl "http://localhost:4566/restapis/ABC123/local/_user_request_/plot?plotKey=plots/jheem_real_plot.json"
```

## 📡 API Reference

### Plot Discovery
**GET** `/plots/search`

Discovers available plots for a city/scenario combination with optional outcome filtering.

**Parameters:**
- `city` (required): City code (e.g., "C.12580")
- `scenario` (required): Scenario name (e.g., "cessation")  
- `outcomes` (optional): Comma-separated outcome filter (e.g., "incidence,prevalence")

**Example Request:**
```bash
curl "http://localhost:4566/restapis/ABC123/local/_user_request_/plots/search?city=C.12580&scenario=cessation&outcomes=incidence,diagnosed.prevalence"
```

**Example Response:**
```json
{
  "city": "C.12580",
  "scenario": "cessation",
  "total_plots": 2,
  "plots": [
    {
      "outcome": "incidence",
      "statistic_type": "mean.and.interval",
      "facet_choice": "sex",
      "s3_key": "plots/jheem_real_plot.json",
      "file_size": 32768,
      "created_at": "2025-06-10T20:00:00Z"
    },
    {
      "outcome": "diagnosed.prevalence", 
      "statistic_type": "mean.and.interval",
      "facet_choice": "sex",
      "s3_key": "plots/prevalence_test.json",
      "file_size": 28500,
      "created_at": "2025-06-10T21:00:00Z"
    }
  ]
}
```

### Plot Retrieval
**GET** `/plot`

Retrieves plot JSON data from S3 storage.

**Parameters:**
- `plotKey` (required): S3 key for the plot file

**Example Request:**
```bash
curl "http://localhost:4566/restapis/ABC123/local/_user_request_/plot?plotKey=plots/jheem_real_plot.json"
```

**Example Response:**
```json
{
  "data": [
    {
      "x": ["2020", "2021", "2022"],
      "y": [100, 95, 87],
      "type": "scatter",
      "name": "Male"
    }
  ],
  "layout": {
    "title": "HIV Incidence Over Time",
    "xaxis": {"title": "Year"},
    "yaxis": {"title": "New Infections"}
  }
}
```

### Plot Registration
**POST** `/plots/register`

Registers metadata for a new plot in the database.

**Request Body:**
```json
{
  "city": "C.12580",
  "scenario": "cessation",
  "outcome": "incidence", 
  "statistic_type": "mean.and.interval",
  "facet_choice": "sex",
  "s3_key": "plots/new_plot.json",
  "file_size": 35000
}
```

**Example Response:**
```json
{
  "message": "Plot registered successfully",
  "city_scenario": "C.12580#cessation",
  "outcome_stat_facet": "incidence#mean.and.interval#sex",
  "s3_key": "plots/new_plot.json"
}
```

## 🗃️ Data Management

### S3 Operations

```bash
# List all plots in bucket
awslocal s3 ls s3://prerun-plots-bucket-local/plots/ --recursive

# Upload new plot file
awslocal s3 cp /path/to/new_plot.json s3://prerun-plots-bucket-local/plots/new_plot.json

# Download plot for inspection
awslocal s3 cp s3://prerun-plots-bucket-local/plots/jheem_real_plot.json ./downloaded_plot.json

# Get bucket size
awslocal s3 ls s3://prerun-plots-bucket-local --recursive --human-readable --summarize
```

### DynamoDB Operations

```bash
# List all registered plots
awslocal dynamodb scan \
    --table-name jheem-plot-metadata-local \
    --query 'Items[*].{Outcome:outcome.S,City:city_scenario.S,S3Key:s3_key.S}' \
    --output table

# Query plots for specific city/scenario
awslocal dynamodb query \
    --table-name jheem-plot-metadata-local \
    --key-condition-expression "city_scenario = :cs" \
    --expression-attribute-values '{":cs":{"S":"C.12580#cessation"}}'

# Count total plots in database
awslocal dynamodb scan \
    --table-name jheem-plot-metadata-local \
    --select COUNT

# Delete plot metadata
awslocal dynamodb delete-item \
    --table-name jheem-plot-metadata-local \
    --key '{"city_scenario":{"S":"C.12580#cessation"},"outcome_stat_facet":{"S":"incidence#mean.and.interval#sex"}}'
```

## 🔗 Frontend Integration

### Setup Frontend Connection

The frontend (jheem-portal repository) connects via environment variables. Create or update `jheem-portal/.env.local`:

```bash
# Get your current API Gateway ID
awslocal apigateway get-rest-apis --query 'items[0].id' --output text

# Set in frontend .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:4566/restapis/YOUR_API_ID/local/_user_request_
```

### Frontend Usage Pattern

```javascript
// 1. Discover available plots
const response = await fetch(`${API_BASE}/plots/search?city=C.12580&scenario=cessation`);
const discovery = await response.json();

// 2. Fetch plot data for each discovered plot
const plotPromises = discovery.plots.map(plot => 
  fetch(`${API_BASE}/plot?plotKey=${plot.s3_key}`)
);
const plots = await Promise.all(plotPromises);

// 3. Render with Plotly.js
plots.forEach(plotData => {
  Plotly.newPlot('chart-container', plotData.data, plotData.layout);
});
```

## 🛠️ Development Workflow

### Adding New Plots

1. **Generate plot with R script** (in jheem2_interactive repo):
   ```bash
   cd /path/to/jheem/code/jheem2_interactive
   Rscript atomic_plot_generator_extracted.R \
     --city "C.12580" \
     --scenario "cessation" \
     --outcome "mortality" \
     --statistic_type "mean.and.interval" \
     --facet_choice "sex" \
     --debug
   ```

2. **Upload to S3**:
   ```bash
   awslocal s3 cp plots/C.12580/cessation/mortality_mean.and.interval_facet_sex.json \
     s3://prerun-plots-bucket-local/plots/mortality_test.json
   ```

3. **Register in database** (via API):
   ```bash
   curl -X POST "http://localhost:4566/restapis/ABC123/local/_user_request_/plots/register" \
     -H "Content-Type: application/json" \
     -d '{
       "city": "C.12580",
       "scenario": "cessation",
       "outcome": "mortality",
       "statistic_type": "mean.and.interval", 
       "facet_choice": "sex",
       "s3_key": "plots/mortality_test.json",
       "file_size": 29000
     }'
   ```

### Code Changes & Testing

```bash
# Make changes to Lambda functions in src/handlers/
# Redeploy
serverless deploy --stage local

# Test changes
python scripts/test_discovery.py

# Check logs (LocalStack prints to console)
# Or: docker logs localstack-main
```

### Database Schema Updates

```bash
# Delete table if schema changes needed
awslocal dynamodb delete-table --table-name jheem-plot-metadata-local

# Redeploy to recreate
serverless deploy --stage local

# Re-register data
python scripts/register_existing_plots.py
```

## 📊 Current Test Data

The system comes with 3 test plots representing different epidemiological outcomes:

| Outcome | Description | S3 Key | Database Key |
|---------|-------------|---------|--------------|
| **incidence** | New HIV infections over time | `plots/jheem_real_plot.json` | `C.12580#cessation` / `incidence#mean.and.interval#sex` |
| **diagnosed.prevalence** | Diagnosed HIV prevalence | `plots/prevalence_test.json` | `C.12580#cessation` / `diagnosed.prevalence#mean.and.interval#sex` |
| **adap.proportion** | ADAP program coverage | `plots/adap_proportion_test.json` | `C.12580#cessation` / `adap.proportion#mean.and.interval#sex` |

All plots represent:
- **City**: C.12580 (specific geographic location)
- **Scenario**: cessation (Ryan White funding cessation)  
- **Statistic**: mean.and.interval (mean with confidence intervals)
- **Faceting**: sex (split by male/female demographics)

## 🔍 Troubleshooting

### Common Issues

#### LocalStack Not Responding
```bash
# Check container status
docker ps | grep localstack

# Restart if needed
localstack stop
localstack start -d

# Verify services are ready
localstack status
```

#### API Gateway ID Changed
```bash
# Get new API ID after LocalStack restart
awslocal apigateway get-rest-apis --query 'items[0].id' --output text

# Update frontend .env.local file
NEXT_PUBLIC_API_BASE_URL=http://localhost:4566/restapis/NEW_ID/local/_user_request_
```

#### DynamoDB Table Issues
```bash
# Check if table exists
awslocal dynamodb list-tables

# Recreate if missing
serverless deploy --stage local

# Verify table structure
awslocal dynamodb describe-table --table-name jheem-plot-metadata-local
```

#### S3 Bucket Issues
```bash
# Check bucket exists
awslocal s3 ls

# Recreate if missing
awslocal s3 mb s3://prerun-plots-bucket-local

# Upload test data
awslocal s3 cp test-plot.json s3://prerun-plots-bucket-local/plots/
```

### Debug Commands

```bash
# Test LocalStack connectivity
awslocal sts get-caller-identity

# Check all deployed functions
awslocal lambda list-functions --query 'Functions[].FunctionName'

# Test API endpoints directly
curl -v "http://localhost:4566/restapis/ABC123/local/_user_request_/plots/search?city=C.12580&scenario=cessation"

# Monitor LocalStack logs
docker logs -f localstack-main

# Check function logs
awslocal logs describe-log-groups
```

### Environment Reset

```bash
# Complete reset (nuclear option)
localstack stop
docker system prune -f
localstack start -d

# Redeploy everything
serverless deploy --stage local
python scripts/register_existing_plots.py
```

## 🌍 Production Deployment

### AWS Setup
```bash
# Configure real AWS credentials
aws configure

# Deploy to production
serverless deploy --stage prod

# Note the production endpoints for frontend configuration
```

### Environment Differences
| Aspect | LocalStack | Production AWS |
|--------|------------|----------------|
| **Cost** | Free | Pay-per-use |
| **Speed** | Fast (local) | Network latency |
| **Scale** | Limited | Unlimited |
| **Data** | Temporary | Persistent |
| **URL** | localhost:4566 | Custom domain |

## 📈 Performance & Scale

### Current Metrics
- **Plot Size**: ~32KB average per plot
- **Total Library**: 20,160 plots (~630MB)
- **Query Speed**: <200ms discovery + retrieval
- **Concurrent Users**: Scales automatically

### Optimization Opportunities
- **CDN**: Add CloudFront for global distribution
- **Caching**: Redis for hot plot data
- **Compression**: Gzip plots for smaller transfer
- **Indexing**: Additional DynamoDB indexes for complex queries

## 🤝 Contributing

### Code Style
- **Python**: Follow PEP 8, use type hints
- **JavaScript**: ESLint + Prettier
- **Comments**: Explain business logic, not syntax

### Testing
```bash
# Run all tests
python scripts/test_discovery.py

# Add new tests in scripts/test_*.py
# Test both success and error cases
```

### Documentation
- Update this README for any architecture changes
- Add inline comments for complex business logic
- Document new API endpoints

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review LocalStack logs: `docker logs localstack-main` 
3. Test with debug scripts in `scripts/` directory
4. Verify frontend `.env.local` configuration

---

**🎯 Project Status**: Production-ready development environment with discovery system, multi-plot support, and automated infrastructure. Ready for bulk plot generation and production AWS deployment.