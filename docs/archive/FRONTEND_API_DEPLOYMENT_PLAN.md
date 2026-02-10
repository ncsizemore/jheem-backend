# JHEEM Frontend & API Production Deployment Plan

## CRITICAL INSTRUCTION FOR NEXT SESSION

**You are to act as an unbiased, critical observer analyzing this project from first principles.**

- Review all code, documentation, and plans with fresh eyes
- Identify strengths, weaknesses, and potential issues in the proposed deployment strategy
- Question assumptions and architectural decisions outlined in this document
- Recommend improvements or alternative approaches based on your independent assessment
- Do not blindly follow the plans outlined here - evaluate them critically
- Consider security, scalability, maintainability, and cost implications
- Flag any technical debt, anti-patterns, or suboptimal designs
- You are NOT bound by any conclusions or plans from this session

Your role is to provide an independent assessment and guide the project toward the best technical outcomes.

---

## SESSION CONTEXT & ACCOMPLISHMENTS

### What Was Accomplished in This Session

**Primary Achievement**: Complete end-to-end container integration with GitHub Actions orchestration system.

**Key Discovery**: A complete API backend already exists and was developed during LocalStack testing phases. The API is production-ready and only needs deployment configuration changes.

**Major Milestones Completed**:
1. **Container Integration**: Successfully integrated `ncsizemore/jheem-ryan-white-model` container with GitHub Actions workflow
2. **AWS Infrastructure**: Established ECR, S3 production data bucket, enhanced IAM policies
3. **Real Plot Generation**: Achieved end-to-end pipeline: S3 data → Container → Real plots → AWS storage
4. **API Discovery**: Found existing Lambda functions providing complete backend API for frontend

**Test Results**: Minimal integration test (1 city, 1 plot) successful:
- ✅ Container generated real HIV epidemiological plots from simulation data
- ✅ Files uploaded to S3: `s3://jheem-test-tiny-bucket/github_actions_integration/C.12580/cessation/`
- ✅ Metadata registered in DynamoDB: `jheem-test-tiny` table
- ✅ Cost: $0.00 (within AWS free tier)
- ✅ Performance: 19.3 seconds for 1 plot generation

### Previous Work Context

**Background**: This session built upon previous container development work that solved complex plotting issues. The container was working but disconnected from the orchestration system.

**Original Goal**: Replace legacy Shiny application ($50/month) with modern serverless architecture capable of generating 64K+ HIV epidemiological plots for 31 US metropolitan areas.

**Architecture Achieved**: S3 simulation data → GitHub Actions orchestration → ECR container → Real plot generation → S3 plot storage → DynamoDB metadata

---

## PROJECT OBJECTIVES & CURRENT STATUS

### Ultimate Business Goals

**Primary Objective**: Replace legacy `jheem2_interactive` Shiny application with modern, scalable, cost-effective plot serving infrastructure.

**Key Requirements**:
- **Scale**: Generate 64,000+ pre-run plots across 31 cities, multiple HIV intervention scenarios
- **Performance**: Sub-second plot serving to researchers and public health officials  
- **Cost**: Stay under $50/month (current Shiny hosting cost)
- **Reliability**: 100% uptime with proper error handling and monitoring
- **Maintainability**: Clean, documented, reproducible infrastructure

### Current System State

**Infrastructure Status** (✅ Production Ready):
- **Container System**: `849611540600.dkr.ecr.us-east-1.amazonaws.com/jheem-ryan-white-model:latest`
- **Simulation Data**: `s3://jheem-data-production/simulations/ryan-white/` (3.6GB, 124 files)
- **Plot Storage**: `s3://jheem-test-tiny-bucket/github_actions_integration/`
- **Metadata**: `jheem-test-tiny` DynamoDB table
- **Orchestration**: GitHub Actions matrix strategy with YAML configuration system

**Frontend Status** (✅ Exists, Needs Connection):
- **Location**: `/Users/cristina/wiley/Documents/jheem-portal`
- **Technology**: Next.js 15, React 19, TypeScript, Tailwind CSS, Plotly.js
- **Features**: Interactive map explorer, plot viewer, test interface
- **Current State**: Configured for LocalStack, needs production API connection

**API Status** (✅ Exists, Needs Deployment):
- **Location**: `/Users/cristina/wiley/Documents/jheem-backend/src/handlers/`
- **Technology**: Python 3.9 Lambda functions with Serverless Framework
- **Current State**: LocalStack-configured, ready for AWS deployment

---

## EXISTING API ANALYSIS (CRITICAL DISCOVERY)

### Complete API Already Built

**Key Finding**: During LocalStack development, a complete production-ready API was implemented.

**API Endpoints Implemented**:

#### 1. Plot Retrieval Endpoint
**File**: `/Users/cristina/wiley/Documents/jheem-backend/src/handlers/plot_retrieval.py`
**Function**: `get_plot(event, context)`
**Endpoint**: `GET /plot?plotKey=<s3_key>`
**Purpose**: Fetch plot JSON from S3 and return to frontend

**Implementation**:
```python
def get_plot(event, context):
    plot_key = query_params.get('plotKey')
    s3_client = boto3.client('s3', endpoint_url=s3_endpoint, ...)
    response = s3_client.get_object(Bucket=bucket_name, Key=plot_key)
    plot_data = response['Body'].read().decode('utf-8')
    return {'statusCode': 200, 'body': plot_data}
```

#### 2. Plot Discovery Endpoints  
**File**: `/Users/cristina/wiley/Documents/jheem-backend/src/handlers/plot_discovery.py`

**Function**: `search_plots(event, context)`
**Endpoint**: `GET /plots/search?city=C.12580&scenario=cessation&outcomes=incidence`
**Purpose**: Query DynamoDB for plots matching city/scenario/outcome criteria

**Function**: `get_all_available_cities(event, context)`  
**Endpoint**: `GET /plots/cities`
**Purpose**: Return all cities with available scenarios for frontend initialization

**Function**: `register_plot(event, context)`
**Endpoint**: `POST /plots/register`
**Purpose**: Register new plot metadata in DynamoDB (used by GitHub Actions)

### Serverless Framework Configuration

**File**: `/Users/cristina/wiley/Documents/jheem-backend/serverless.yml`

**Key Configuration**:
```yaml
service: jheem-backend
provider:
  name: aws
  runtime: python3.9
  region: us-east-1

functions:
  getPrerunPlot:
    handler: src/handlers/plot_retrieval.get_plot
    events:
      - http:
          path: plot
          method: get
          cors: true
  
  getAllCities:
    handler: src/handlers/plot_discovery.get_all_available_cities
    events:
      - http:
          path: plots/cities
          method: get
          cors: true

resources:
  Resources:
    PlotsBucket:
      Type: AWS::S3::Bucket
    PlotMetadataTable:
      Type: AWS::DynamoDB::Table
```

### Frontend Integration Points

**File**: `/Users/cristina/wiley/Documents/jheem-portal/src/hooks/useAvailableCities.ts`
**Current API Call**:
```javascript
const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
const discoverUrl = `${baseUrl}/plots/cities`;
```

**File**: `/Users/cristina/wiley/Documents/jheem-portal/src/app/explore/page.tsx`
**Current Plot Loading**:
```javascript
const plotUrl = `${baseUrl}/plot?plotKey=${encodeURIComponent(plotMeta.s3_key)}`;
```

---

## CRITICAL ISSUES IDENTIFIED

### 1. Database Schema Mismatch (BLOCKING)

**Problem**: DynamoDB table structure mismatch between GitHub Actions output and Lambda function expectations.

**Current GitHub Actions Output** (`jheem-test-tiny` table):
```json
{
  "city": {"S": "C.12580"},
  "plot_id": {"S": "container_C.12580_testing_mean.and.interval_facet_sex"},
  "scenario": {"S": "cessation"}, 
  "outcome": {"S": "testing"},
  "statistic": {"S": "mean.and.interval"},
  "facet": {"S": "none"},
  "s3_key": {"S": "github_actions_integration/C.12580/cessation/testing_mean.and.interval_facet_sex.json"}
}
```

**Expected by Lambda Functions**:
```json
{
  "city_scenario": {"S": "C.12580#cessation"},
  "outcome_stat_facet": {"S": "testing#mean.and.interval#none"},
  "statistic_type": {"S": "mean.and.interval"},
  "facet_choice": {"S": "none"}
}
```

**Root Cause**: GitHub Actions workflow writes to DynamoDB using one schema, Lambda functions expect a different composite key structure.

**Impact**: Frontend discovery API calls will fail because Lambda functions can't query the existing data structure.

### 2. Environment Configuration Mismatch

**LocalStack Configuration** (current):
```yaml
environment:
  S3_ENDPOINT_URL: http://host.docker.internal:4566
  DYNAMODB_ENDPOINT_URL: http://host.docker.internal:4566
  S3_BUCKET_NAME: prerun-plots-bucket-local
  DYNAMODB_TABLE_NAME: jheem-plot-metadata-local
```

**Production Requirements**:
```yaml
environment:
  S3_BUCKET_NAME: jheem-test-tiny-bucket
  DYNAMODB_TABLE_NAME: jheem-test-tiny
  # Remove endpoint URLs for production AWS
```

### 3. Frontend Environment Configuration

**Current** (LocalStack):
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:4566/restapis/0brpehjrjy/local/_user_request_
```

**Production Required**:
```
NEXT_PUBLIC_API_BASE_URL=https://<api-gateway-id>.execute-api.us-east-1.amazonaws.com
```

---

## DEPLOYMENT STRATEGY & IMPLEMENTATION PLAN

### Phase 1: Database Schema Resolution (CRITICAL FIRST STEP)

**Decision Required**: Choose one of two approaches:

#### Option A: Modify GitHub Actions to Match Lambda Schema (Recommended)
**File to Modify**: `/Users/cristina/wiley/Documents/jheem-backend/.github/workflows/generate-plots.yml`
**Lines**: ~210-224 (DynamoDB registration section)

**Current Registration Logic**:
```bash
plot_id="container_${{ matrix.city }}_${base_name}"
aws dynamodb put-item \
  --table-name jheem-test-tiny \
  --item "{
    \"city\": {\"S\": \"${{ matrix.city }}\"},
    \"plot_id\": {\"S\": \"$plot_id\"},
    \"scenario\": {\"S\": \"$scenario\"},
    ...
  }"
```

**Required Change**:
```bash
city_scenario="${{ matrix.city }}#${scenario}"
outcome_stat_facet="${outcome}#${statistic}#${facet}"

aws dynamodb put-item \
  --table-name jheem-test-tiny \
  --item "{
    \"city_scenario\": {\"S\": \"$city_scenario\"},
    \"outcome_stat_facet\": {\"S\": \"$outcome_stat_facet\"},
    \"outcome\": {\"S\": \"$outcome\"},
    \"statistic_type\": {\"S\": \"$statistic\"},
    \"facet_choice\": {\"S\": \"$facet\"},
    \"s3_key\": {\"S\": \"$s3_key\"},
    ...
  }"
```

#### Option B: Modify Lambda Functions to Match Current Schema
**Files to Modify**: 
- `/Users/cristina/wiley/Documents/jheem-backend/src/handlers/plot_discovery.py`
- Update query logic to use `city` as partition key instead of `city_scenario`

**Recommendation**: **Option A** - Modify GitHub Actions to match existing Lambda schema, as the Lambda schema is more efficient for queries.

### Phase 2: API Deployment to AWS Production

#### Step 1: Update Serverless Configuration
**File**: `/Users/cristina/wiley/Documents/jheem-backend/serverless.yml`

**Required Changes**:
```yaml
# Current
environment:
  S3_BUCKET_NAME: ${self:custom.bucketName}
  S3_ENDPOINT_URL: http://host.docker.internal:4566
  
# Change to
environment:
  S3_BUCKET_NAME: jheem-test-tiny-bucket
  DYNAMODB_TABLE_NAME: jheem-test-tiny
  # Remove endpoint URLs for production
```

#### Step 2: Deploy Lambda Functions
**Commands**:
```bash
cd /Users/cristina/wiley/Documents/jheem-backend

# Install dependencies
npm install -g serverless
npm install

# Deploy to AWS production
serverless deploy --stage prod --region us-east-1

# Expected output: API Gateway endpoints
# GET - https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/plot
# GET - https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/plots/cities
```

**IAM Permissions Required**: The deployment will need IAM permissions to:
- Create Lambda functions
- Create API Gateway resources  
- Access existing S3 bucket and DynamoDB table

### Phase 3: Frontend Deployment Strategy

#### Domain Strategy Decision
**Current**: `jheem.org` → forwards to shinyapps.io
**Options**:
1. **Replace completely**: `jheem.org` → new frontend
2. **Gradual migration**: `app.jheem.org` → new frontend, keep `jheem.org` → old app
3. **Legacy subdomain**: `jheem.org` → new frontend, `legacy.jheem.org` → old app

#### Frontend Hosting Options

**Option A: AWS S3 + CloudFront (Recommended)**
```bash
# Build static export
cd /Users/cristina/wiley/Documents/jheem-portal
npm run build
npm run export

# Create S3 bucket and upload
aws s3 mb s3://jheem-frontend-production
aws s3 sync out/ s3://jheem-frontend-production --delete

# Configure CloudFront distribution
# Point jheem.org to CloudFront
```

**Option B: Vercel Deployment**
```bash
# Install Vercel CLI  
npm install -g vercel

# Deploy (automatic builds from git)
vercel --prod

# Point jheem.org CNAME to Vercel domain
```

#### Step 4: Update Frontend Environment
**File**: `/Users/cristina/wiley/Documents/jheem-portal/.env.local`

**Required Change**:
```bash
# FROM
NEXT_PUBLIC_API_BASE_URL=http://localhost:4566/restapis/0brpehjrjy/local/_user_request_

# TO (after API deployment)
NEXT_PUBLIC_API_BASE_URL=https://<api-gateway-id>.execute-api.us-east-1.amazonaws.com/prod
```

### Phase 4: Integration Testing & Validation

#### Test Sequence
1. **API Smoke Test**: Verify Lambda functions respond correctly
   ```bash
   curl https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/plots/cities
   curl "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod/plot?plotKey=github_actions_integration/C.12580/cessation/testing_mean.and.interval_facet_sex.json"
   ```

2. **Frontend Integration Test**: Deploy frontend with API connection
3. **End-to-End Test**: Generate new plot via GitHub Actions, verify it appears in frontend
4. **Performance Test**: Measure plot loading time (target: sub-second)

---

## OUTSTANDING TECHNICAL CONSIDERATIONS

### 1. Cost Analysis & Monitoring

**Current AWS Costs**: $0.00 (within free tier for minimal test)
**Projected Production Costs**:
- **Lambda**: ~$0-5/month (1M free requests)
- **API Gateway**: ~$0-10/month (1M free requests)  
- **S3 + CloudFront**: ~$1-5/month (frontend hosting)
- **Total Estimated**: $5-20/month (vs $50/month current Shiny)

**Monitoring Strategy**: 
- Set up AWS budgets and cost alerts
- Monitor API Gateway and Lambda usage
- Track S3 storage costs as plot volume increases

### 2. Security Considerations

**Current CORS Configuration**: `Access-Control-Allow-Origin: '*'`
**Production Recommendation**: Restrict to frontend domain once deployed

**API Rate Limiting**: None currently implemented
**Consideration**: Add API Gateway throttling for production

### 3. Performance & Scalability

**Frontend Performance**: Static site should achieve sub-second loading
**API Performance**: Lambda cold starts may add 100-500ms latency
**S3 Performance**: Plot retrieval should be <200ms

**Scalability**: Current architecture scales automatically but consider:
- CloudFront caching for frequently accessed plots
- Lambda provisioned concurrency if cold starts become an issue

### 4. Error Handling & Monitoring

**Current State**: Basic error handling in Lambda functions
**Production Needs**:
- CloudWatch logging and monitoring
- Error alerting for failed requests
- Frontend error boundaries for graceful failure handling

### 5. Development Workflow

**Current**: Manual deployment via Serverless CLI
**Enhancement Considerations**:
- GitHub Actions CI/CD for API deployments
- Automated testing pipeline
- Staging environment for testing changes

---

## IMMEDIATE NEXT STEPS RECOMMENDATION

### Priority 1: Database Schema Fix (BLOCKING - Must be resolved first)
1. **Analyze** the current DynamoDB data structure in `jheem-test-tiny` table
2. **Decide** between modifying GitHub Actions vs Lambda functions for schema compatibility
3. **Implement** the chosen schema fix
4. **Test** with minimal plot generation to verify schema works

### Priority 2: API Deployment (High Impact)
1. **Update** serverless.yml configuration for production environment
2. **Deploy** Lambda functions to AWS using `serverless deploy`
3. **Test** API endpoints directly with curl/Postman
4. **Verify** Lambda functions can read existing plot data

### Priority 3: Frontend Connection (Quick Win)
1. **Update** frontend environment variable with new API Gateway URL
2. **Test** frontend locally with production API
3. **Deploy** frontend to S3 + CloudFront or Vercel
4. **Validate** end-to-end plot loading

### Priority 4: Domain Migration (Final Step)
1. **Choose** domain strategy (replace jheem.org vs gradual migration)
2. **Configure** DNS and CloudFront
3. **Test** production deployment
4. **Monitor** for issues and performance

---

## SUCCESS CRITERIA

### Technical Validation
- [ ] **API Functional**: All Lambda endpoints respond correctly to frontend requests
- [ ] **Database Integration**: Plot discovery and retrieval work with existing data
- [ ] **Frontend Integration**: Maps load cities, plots display correctly
- [ ] **Performance Target**: Plot loading <2 seconds end-to-end

### Business Validation  
- [ ] **Cost Target**: Total monthly cost <$25 (50% of current Shiny cost)
- [ ] **Reliability**: 99%+ uptime with error monitoring
- [ ] **User Experience**: Equivalent or better than current Shiny application
- [ ] **Scalability**: System handles multiple concurrent users without degradation

### Production Readiness
- [ ] **Monitoring**: CloudWatch logging and alerting configured
- [ ] **Security**: CORS and API access properly restricted
- [ ] **Documentation**: Deployment and maintenance procedures documented
- [ ] **Backup Strategy**: Data backup and recovery procedures defined

---

## CRITICAL DECISION POINTS FOR NEXT SESSION

### 1. Database Schema Resolution Strategy
**Decision Required**: Modify GitHub Actions or Lambda functions?
**Impact**: Affects all subsequent deployment steps
**Recommendation**: Analyze existing data first, then choose lowest-risk option

### 2. Frontend Deployment Platform
**Decision Required**: AWS S3+CloudFront vs Vercel vs other?
**Factors**: Cost, complexity, integration with existing AWS infrastructure
**Recommendation**: AWS-native for consistency, unless simplicity is prioritized

### 3. Domain Migration Strategy  
**Decision Required**: Big bang replacement vs gradual migration?
**Factors**: Risk tolerance, user disruption, rollback capability
**Recommendation**: Analyze current jheem.org traffic and user base first

### 4. API Environment Strategy
**Decision Required**: Reuse existing resources (jheem-test-tiny) vs create production-specific resources?
**Factors**: Data isolation, cost, complexity
**Recommendation**: Consider creating prod-specific resources for cleaner separation

---

## PROJECT CONTEXT FILES TO REVIEW

### Required Reading for Next Session
1. **`/Users/cristina/wiley/Documents/jheem-backend/docs/CONTAINER_INTEGRATION_SESSION_SUMMARY.md`** - Comprehensive background on container integration work
2. **`/Users/cristina/wiley/Documents/jheem-backend/src/handlers/`** - Existing API implementation
3. **`/Users/cristina/wiley/Documents/jheem-backend/serverless.yml`** - Infrastructure configuration
4. **`/Users/cristina/wiley/Documents/jheem-portal/`** - Frontend codebase and current configuration

### Key Configuration Files
- **`/Users/cristina/wiley/Documents/jheem-backend/.github/workflows/generate-plots.yml`** - Plot generation pipeline
- **`/Users/cristina/wiley/Documents/jheem-portal/.env.local`** - Frontend API configuration  
- **`/Users/cristina/wiley/Documents/jheem-portal/src/hooks/useAvailableCities.ts`** - API integration patterns
- **`/Users/cristina/wiley/Documents/jheem-portal/src/app/explore/page.tsx`** - Plot loading implementation

---

## FINAL NOTES

This project is remarkably close to production deployment. The major infrastructure work has been completed, and a functional API already exists. The primary challenge is ensuring compatibility between the data structures used by the plot generation pipeline and the API functions.

The next session should focus on systematic validation of the existing components and methodical resolution of the schema compatibility issue. Once that core integration challenge is resolved, deployment to production should be straightforward.

**Estimated Time to Production**: 1-2 days of focused development work, assuming no major architectural changes are required.

**Key Risk**: Database schema mismatch. This must be resolved before any deployment attempts, as it will cause the frontend to fail when trying to discover available plots.

**Key Opportunity**: The existing LocalStack-tested API provides a robust foundation that should translate directly to AWS production with minimal changes required.