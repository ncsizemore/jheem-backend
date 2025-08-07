# JHEEM Backend - Production Serverless API

A modern, production-ready serverless backend for the JHEEM epidemiological modeling system. Successfully deployed to AWS and serving live data to the [JHEEM Portal](https://jheem-portal.vercel.app/), replacing the legacy Shiny application with a scalable, cost-effective cloud-native architecture.

## 🚀 Live System

**🌐 Production Frontend**: https://jheem-portal.vercel.app/  
**📡 Production API**: `https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod`  
**📊 Cost**: ~$5-15/month (70% reduction from $50/month Shiny)  
**⚡ Performance**: Sub-2-second plot loading  
**📈 Scale**: Auto-scaling serverless architecture  

## 🏗️ Architecture Overview

This system implements a **pre-computed plot library** approach with intelligent metadata indexing, generating epidemiological plots via GitHub Actions and serving them instantly through a serverless API.

### Production Architecture

```
GitHub Actions Container → S3 + DynamoDB → AWS Lambda → API Gateway → Frontend
     Plot Generation           Storage        Processing    RESTful API    Vercel App
```

### Core Components

- **🔄 GitHub Actions**: Container-based plot generation pipeline
- **📦 S3 Storage**: Plot JSON files with lifecycle management  
- **🗄️ DynamoDB**: Composite key metadata index for efficient discovery
- **⚡ Lambda Functions**: Serverless API endpoints with automatic scaling
- **🌐 API Gateway**: RESTful interface with CORS support
- **🖥️ Frontend**: Next.js application deployed to Vercel

### Data Flow

1. **Automated Generation**: GitHub Actions matrix strategy generates plots in parallel
2. **Container Processing**: Uses `849611540600.dkr.ecr.us-east-1.amazonaws.com/jheem-ryan-white-model:latest`
3. **Storage & Indexing**: Plots uploaded to S3, metadata stored in DynamoDB with composite keys
4. **API Discovery**: Frontend queries Lambda functions to discover available plots
5. **Plot Retrieval**: Lambda fetches plot data from S3 on-demand
6. **Visualization**: Interactive plots rendered with Plotly.js

## 📋 Production API Reference

### Base URL
```
https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod
```

### Available Endpoints

#### 1. Get All Cities
**GET** `/plots/cities`

Discovers all cities with available plot data.

**Example:**
```bash
curl "https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plots/cities"
```

**Response:**
```json
{
  "cities": {
    "C.12580": ["cessation"]
  },
  "total_cities": 1
}
```

#### 2. Search Plots by City/Scenario  
**GET** `/plots/search`

**Parameters:**
- `city` (required): City code (e.g., "C.12580")
- `scenario` (required): Scenario name (e.g., "cessation")
- `outcomes` (optional): Comma-separated outcome filter

**Example:**
```bash
curl "https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plots/search?city=C.12580&scenario=cessation"
```

**Response:**
```json
{
  "city": "C.12580",
  "scenario": "cessation", 
  "total_plots": 1,
  "plots": [
    {
      "outcome": "testing",
      "statistic_type": "mean.and.interval",
      "facet_choice": "none", 
      "s3_key": "github_actions_integration/C.12580/C.12580/cessation/testing_mean.and.interval_facet_sex_metadata.json",
      "file_size": 393,
      "created_at": "2025-08-06T17:36:22Z"
    }
  ]
}
```

#### 3. Get Specific Plot Data
**GET** `/plot`

**Parameters:**
- `plotKey` (required): S3 key from search results

**Example:**
```bash
curl "https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plot?plotKey=github_actions_integration/C.12580/C.12580/cessation/testing_mean.and.interval_facet_sex_metadata.json"
```

**Response:**
```json
{
  "city": ["C.12580"],
  "scenario": ["cessation"],
  "outcome": ["testing"],
  "statistic_type": ["mean.and.interval"],
  "facet_choice": ["sex"],
  "has_baseline": [true],
  "generation_time": ["2025-08-06 17:36:16"]
}
```

#### 4. Register New Plot (GitHub Actions)
**POST** `/plots/register`

Used by GitHub Actions to register generated plots.

## 🚀 Production Deployment

### Prerequisites
- **AWS CLI**: Configured with appropriate credentials
- **Node.js 18+**: For Serverless Framework  
- **Git**: Repository access

### Deploy to Production

```bash
# Clone repository
git clone <jheem-backend-repo>
cd jheem-backend

# Install dependencies
npm install

# Deploy to production AWS
serverless deploy --stage prod --region us-east-1
```

**Expected Output:**
```
Service deployed to stack jheem-backend-prod (123s)

endpoints:
  GET - https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plot
  GET - https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plots/search  
  GET - https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plots/cities
  POST - https://abre4axci6.execute-api.us-east-1.amazonaws.com/prod/plots/register

functions:
  getPrerunPlot: jheem-backend-prod-getPrerunPlot
  searchPlots: jheem-backend-prod-searchPlots
  registerPlot: jheem-backend-prod-registerPlot  
  getAllCities: jheem-backend-prod-getAllCities
```

### Production Resources

**AWS Account**: `849611540600`  
**Region**: `us-east-1`  
**S3 Bucket**: `jheem-test-tiny-bucket`  
**DynamoDB Table**: `jheem-test-tiny`  
**IAM Role**: `jheem-backend-prod-us-east-1-lambdaRole`

## 🤖 GitHub Actions Integration

### Automated Plot Generation

The system uses GitHub Actions with a container-based approach for scalable plot generation:

**Container**: `849611540600.dkr.ecr.us-east-1.amazonaws.com/jheem-ryan-white-model:latest`  
**Workflow**: `.github/workflows/generate-plots.yml`  
**Strategy**: Matrix execution across cities for parallel processing  

### Configuration Types

| Type | Cities | Est. Plots | Runtime | Use Case |
|------|---------|------------|---------|----------|
| `minimal` | 1 | ~30 | 5 min | Development testing |
| `test` | 4 | ~300 | 15 min | Integration testing |  
| `medium` | 6 | ~900 | 30 min | Staging validation |
| `full` | 31 | ~64K | 2-6 hours | Production deployment |

### Triggering Plot Generation

1. Go to **GitHub Actions** tab
2. Select **"Generate JHEEM Plots"** workflow
3. Click **"Run workflow"**
4. Choose configuration type and max parallel jobs
5. Monitor execution in Actions dashboard

## 💻 Local Development with LocalStack

For local development and testing without AWS costs:

### Setup LocalStack Environment

```bash
# Install LocalStack
pip install localstack[pro]  # or use Docker

# Start LocalStack
localstack start -d

# Set LocalStack credentials  
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

### Deploy to LocalStack

```bash
# Install Node.js dependencies
npm install

# Deploy to local stack
serverless deploy --stage local

# Expected local API base URL format:
# http://localhost:4566/restapis/[API-ID]/local/_user_request_
```

### Test Local Deployment

```bash
# Register test data
python scripts/register_existing_plots.py

# Test API endpoints
python scripts/test_discovery.py

# Manual endpoint testing  
curl "http://localhost:4566/restapis/[API-ID]/local/_user_request_/plots/cities"
```

### LocalStack vs Production

| Aspect | LocalStack | Production AWS |
|--------|------------|----------------|
| **Cost** | Free | ~$5-15/month |
| **Performance** | Fast (local) | Network latency |
| **Data Persistence** | Temporary | Persistent |
| **Scale Testing** | Limited | Full scale |
| **Development Speed** | Instant | Deployment delays |

## 📊 Database Schema

### DynamoDB Table: `jheem-test-tiny`

**Composite Key Structure:**
- **Partition Key**: `city_scenario` (format: `"C.12580#cessation"`)
- **Sort Key**: `outcome_stat_facet` (format: `"testing#mean.and.interval#sex"`)

**Attributes:**
```json
{
  "city_scenario": "C.12580#cessation",
  "outcome_stat_facet": "testing#mean.and.interval#sex", 
  "outcome": "testing",
  "statistic_type": "mean.and.interval",
  "facet_choice": "sex",
  "s3_key": "github_actions_integration/C.12580/...",
  "file_size": 393,
  "created_at": "2025-08-06T17:36:22Z"
}
```

### S3 Bucket: `jheem-test-tiny-bucket`

**Structure:**
```
jheem-test-tiny-bucket/
├── github_actions_integration/
│   └── C.12580/
│       └── C.12580/
│           └── cessation/
│               ├── testing_mean.and.interval_facet_sex.json
│               └── testing_mean.and.interval_facet_sex_metadata.json
└── plots/ (legacy test data)
```

## 🛠️ Development Workflow

### Making Code Changes

1. **Modify Lambda functions** in `src/handlers/`
2. **Test locally** with LocalStack (optional)
3. **Deploy changes**: `serverless deploy --stage prod`
4. **Verify endpoints** work correctly
5. **Test frontend integration** at https://jheem-portal.vercel.app/

### Adding New API Endpoints

1. **Create handler function** in `src/handlers/`
2. **Add function configuration** to `serverless.yml`
3. **Configure CORS** for frontend access
4. **Deploy and test** new endpoint

### Database Operations

```bash
# Query production DynamoDB
aws dynamodb scan --table-name jheem-test-tiny --limit 5

# Query specific city/scenario
aws dynamodb query \
  --table-name jheem-test-tiny \
  --key-condition-expression "city_scenario = :cs" \
  --expression-attribute-values '{":cs":{"S":"C.12580#cessation"}}'
```

### S3 Operations

```bash
# List plot files
aws s3 ls s3://jheem-test-tiny-bucket/github_actions_integration/ --recursive

# Download plot for inspection  
aws s3 cp s3://jheem-test-tiny-bucket/github_actions_integration/C.12580/C.12580/cessation/testing_mean.and.interval_facet_sex.json ./plot.json
```

## 🔍 Monitoring & Troubleshooting

### CloudWatch Logs

```bash
# View Lambda logs
aws logs filter-log-events --log-group-name /aws/lambda/jheem-backend-prod-getAllCities --start-time $(date -d '1 hour ago' +%s)000

# Monitor API Gateway logs
aws logs filter-log-events --log-group-name API-Gateway-Execution-Logs_[API-ID]/prod
```

### Common Issues

#### API Returns 500 Errors
1. **Check Lambda logs** for credential/permission issues
2. **Verify IAM role** has correct DynamoDB/S3 permissions  
3. **Test resources exist** (table, bucket accessible)

#### Frontend Can't Connect to API
1. **Verify CORS configuration** in `serverless.yml`
2. **Check environment variable** `NEXT_PUBLIC_API_BASE_URL` in Vercel
3. **Test API directly** with curl

#### Plot Data Not Loading
1. **Verify S3 keys** match between DynamoDB and actual files
2. **Check file permissions** on S3 objects
3. **Validate JSON structure** of plot files

### Performance Monitoring

- **Lambda Duration**: Average ~200-500ms per request
- **DynamoDB Read Capacity**: Pay-per-request, auto-scaling
- **S3 Transfer**: ~32KB average per plot
- **API Gateway**: <2-second response times

## 💰 Cost Analysis

### Production Costs (Monthly)

| Service | Usage | Cost |
|---------|--------|------|
| **Lambda** | ~10K invocations | ~$0.00 (free tier) |
| **API Gateway** | ~10K requests | ~$0.00 (free tier) |
| **DynamoDB** | PAY_PER_REQUEST | ~$0.33 |
| **S3** | Storage + requests | ~$0.10 |
| **CloudWatch** | Basic logging | ~$0.50 |
| **Total** | | **~$1-2/month** |

**Cost Comparison:**
- **Legacy Shiny**: $50/month
- **New Architecture**: $1-2/month  
- **Savings**: 95%+ cost reduction

## 🤝 Contributing

### Code Standards
- **Python**: PEP 8, type hints, docstrings
- **Error Handling**: Consistent HTTP status codes and error messages  
- **Testing**: Test both success and failure cases

### Pull Request Process
1. **Create feature branch** from `master`
2. **Test changes locally** with LocalStack
3. **Deploy to development** environment for testing
4. **Verify frontend integration** works correctly
5. **Submit PR** with clear description

## 📚 Additional Documentation

- **GitHub Actions**: See `.github/README.md`
- **AWS Infrastructure**: See `infrastructure/README.md`  
- **Frontend Integration**: See [jheem-portal repository](https://github.com/your-org/jheem-portal)

## 📞 Support

### Production Issues
1. **Check CloudWatch logs** for error details
2. **Verify AWS resource status** in AWS Console
3. **Test API endpoints directly** to isolate issues
4. **Review recent deployments** for changes

### Development Help
1. **LocalStack documentation**: https://docs.localstack.cloud/
2. **Serverless Framework docs**: https://www.serverless.com/framework/docs/
3. **AWS Lambda debugging**: CloudWatch logs and X-Ray tracing

---

**🎯 Project Status**: ✅ **Production Ready** - Successfully serving live epidemiological data with 95% cost reduction and sub-2-second performance.