# JHEEM Backend

A serverless backend for the JHEEM epidemiological modeling system, built with AWS Lambda, S3, and DynamoDB, deployable to both LocalStack (for development) and AWS (for production).

## Architecture Overview

- **S3**: Stores pregenerated plot JSON files
- **DynamoDB**: Metadata index for plot discovery and management
- **Lambda Functions**: 
  - `getPrerunPlot`: Retrieves plot data from S3
  - `searchPlots`: Discovers available plots via database queries
  - `registerPlot`: Registers new plot metadata in database
- **API Gateway**: REST API endpoints

## Development Setup

### Prerequisites

1. **Docker**: LocalStack runs in Docker
2. **Python 3.9+**: For Lambda functions and AWS CLI tools
3. **Node.js**: For Serverless Framework

### Initial Setup

1. **Create Python virtual environment**:
   ```bash
   python3 -m venv localstack-env
   source localstack-env/bin/activate
   pip install boto3 awscli-local
   ```

2. **Install Serverless Framework**:
   ```bash
   npm install -g serverless
   npm install
   ```

3. **Start LocalStack**:
   ```bash
   docker run --rm -it -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack
   ```

4. **Set AWS credentials for LocalStack**:
   ```bash
   export AWS_ACCESS_KEY_ID=test
   export AWS_SECRET_ACCESS_KEY=test
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Deployment

1. **Deploy to LocalStack**:
   ```bash
   source localstack-env/bin/activate
   serverless deploy --stage local
   ```

2. **Note the API Gateway endpoint** from deployment output:
   ```
   endpoint: http://localhost:4566/restapis/qn20ihefoo/local/_user_request_
   ```

### Database Setup

**Create DynamoDB table** (one-time setup):
```bash
source localstack-env/bin/activate
awslocal dynamodb create-table \
    --table-name jheem-plot-metadata \
    --attribute-definitions \
        AttributeName=city_scenario,AttributeType=S \
        AttributeName=outcome_stat_facet,AttributeType=S \
    --key-schema \
        AttributeName=city_scenario,KeyType=HASH \
        AttributeName=outcome_stat_facet,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

## API Endpoints

### 1. Get Plot Data
**GET** `/plot?plotKey={s3_key}`

Retrieves plot JSON data from S3.

**Example**:
```bash
curl "http://localhost:4566/restapis/qn20ihefoo/local/_user_request_/plot?plotKey=plots/jheem_real_plot.json"
```

### 2. Search Available Plots  
**GET** `/plots/search?city={city}&scenario={scenario}&outcomes={optional_filter}`

Discovers available plots for a city/scenario combination.

**Example**:
```bash
curl "http://localhost:4566/restapis/qn20ihefoo/local/_user_request_/plots/search?city=C.12580&scenario=cessation"
```

**Response**:
```json
{
  "city": "C.12580",
  "scenario": "cessation", 
  "total_plots": 3,
  "plots": [
    {
      "outcome": "incidence",
      "statistic_type": "mean.and.interval",
      "facet_choice": "sex",
      "s3_key": "plots/jheem_real_plot.json",
      "file_size": 32131,
      "created_at": "2025-06-10T20:00:00Z"
    }
  ]
}
```

### 3. Register New Plot
**POST** `/plots/register`

Registers metadata for a new plot in the database.

**Example**:
```bash
curl -X POST "http://localhost:4566/restapis/qn20ihefoo/local/_user_request_/plots/register" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "C.12580",
    "scenario": "cessation", 
    "outcome": "incidence",
    "statistic_type": "mean.and.interval",
    "facet_choice": "sex",
    "s3_key": "plots/jheem_real_plot.json",
    "file_size": 32131
  }'
```

## Data Management

### S3 Bucket Operations

**List current plots**:
```bash
source localstack-env/bin/activate
awslocal s3 ls s3://prerun-plots-bucket-local/plots/
```

**Upload new plot**:
```bash
awslocal s3 cp /path/to/plot.json s3://prerun-plots-bucket-local/plots/plot_name.json
```

### DynamoDB Operations

**List all registered plots**:
```bash
awslocal dynamodb scan --table-name jheem-plot-metadata
```

**Register plot manually**:
```bash
awslocal dynamodb put-item \
    --table-name jheem-plot-metadata \
    --item '{
        "city_scenario": {"S": "C.12580#cessation"},
        "outcome_stat_facet": {"S": "incidence#mean.and.interval#sex"},
        "s3_key": {"S": "plots/jheem_real_plot.json"},
        "file_size": {"N": "32131"},
        "outcome": {"S": "incidence"},
        "statistic_type": {"S": "mean.and.interval"},
        "facet_choice": {"S": "sex"},
        "created_at": {"S": "2025-06-10T20:00:00Z"}
    }'
```

## Frontend Integration

The frontend (jheem-portal) connects to this backend via the API Gateway endpoint. Set this in the frontend's `.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:4566/restapis/qn20ihefoo/local/_user_request_
```

**Note**: The API Gateway ID (`qn20ihefoo`) may change if LocalStack is restarted. Check with:
```bash
awslocal apigateway get-rest-apis
```

## Troubleshooting

### Common Issues

1. **"AWS credentials missing"** during deployment:
   - Make sure to export AWS credentials before deploying
   - Use `test` credentials for LocalStack

2. **API Gateway ID changed**:
   - Run `awslocal apigateway get-rest-apis` to get new ID
   - Update frontend `.env.local` file

3. **DynamoDB table doesn't exist**:
   - Run the table creation command above
   - Check with: `awslocal dynamodb list-tables`

4. **LocalStack not responding**:
   - Check if container is running: `docker ps`
   - Restart if needed: `docker restart localstack-main`

### Useful Debug Commands

```bash
# Check LocalStack status
docker ps | grep localstack

# List all LocalStack services
awslocal --endpoint-url=http://localhost:4566 sts get-caller-identity

# Test API endpoint directly
curl "http://localhost:4566/restapis/qn20ihefoo/local/_user_request_/plots/search?city=C.12580&scenario=cessation"
```

## Development Workflow

1. **Make code changes** in `src/handlers/`
2. **Deploy updates**: `serverless deploy --stage local`
3. **Test endpoints** with curl or frontend
4. **Check logs** if needed (LocalStack prints to console)
5. **Iterate**

## Future Enhancements

- [ ] Bulk plot registration scripts
- [ ] Production AWS deployment configuration  
- [ ] Enhanced error handling and logging
- [ ] Plot validation before S3 upload
- [ ] Automated testing suite