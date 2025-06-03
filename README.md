# JHEEM Backend

Serverless backend for the JHEEM epidemiological modeling application. This service provides API endpoints for retrieving pre-generated plot data from computational epidemiological simulations.

## Architecture

- **AWS Lambda**: Serverless functions for API logic
- **API Gateway**: REST API endpoints
- **S3**: Storage for plot JSON files
- **Serverless Framework**: Infrastructure as code
- **LocalStack**: Local AWS emulation for development

## Project Structure

```
jheem-backend/
├── src/
│   └── handlers/
│       ├── plot_retrieval.py    # Main Lambda function for plot API
│       └── test_s3.py          # S3 connection test function
├── serverless.yml              # Serverless Framework configuration
├── requirements.txt            # Python dependencies
└── package.json               # Node.js dependencies (for Serverless plugins)
```

## API Endpoints

### GET /plot

Retrieves a pre-generated plot JSON file from S3.

**Parameters:**
- `plotKey` (required): The S3 key for the plot file (e.g., `plots/C.12580/cessation/incidence_mean_facet_sex.json`)

**Response:**
- `200`: Returns Plotly JSON specification
- `404`: Plot not found
- `500`: Server error

**Example:**
```bash
curl "http://localhost:4566/restapis/{api-id}/local/_user_request_/plot?plotKey=plots/test.json"
```

## Development Setup

### Prerequisites

- Node.js and npm
- Python 3.9+
- LocalStack running
- AWS CLI Local (`awscli-local`)

### Installation

1. **Install dependencies:**
```bash
npm install
pip install -r requirements.txt
```

2. **Start LocalStack:**
```bash
localstack start -d
```

3. **Set environment variables:**
```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

4. **Deploy to LocalStack:**
```bash
serverless deploy --stage local
```

### Testing

**Test S3 bucket creation:**
```bash
awslocal s3 ls
```

**Test Lambda function:**
```bash
awslocal lambda invoke --function-name jheem-backend-local-getPrerunPlot --payload '{"queryStringParameters":{"plotKey":"test"}}' response.json
```

**Test API endpoint:**
```bash
curl "http://localhost:4566/restapis/{api-id}/local/_user_request_/plot?plotKey=plots/test.json"
```

## Plot Data Format

The API serves Plotly JSON specifications with this structure:

```json
{
  "data": [
    {
      "x": [2010, 2011, 2012, ...],
      "y": [164.33, 147.50, 135.85, ...],
      "type": "scatter",
      "mode": "lines",
      "name": "Series Name"
    }
  ],
  "layout": {
    "title": "Plot Title",
    "xaxis": {"title": "Year"},
    "yaxis": {"title": "Value"}
  }
}
```

## Plot Organization in S3

Plots are organized in S3 with the following structure:

```
s3://prerun-plots-bucket-local/
└── plots/
    └── {city}/
        └── {scenario}/
            └── {outcome}_{statistic_type}_{facet_choice}.json
```

**Example paths:**
- `plots/C.12580/cessation/incidence_mean.and.interval_facet_sex.json`
- `plots/C.12580/cessation/prevalence_mean.and.interval_unfaceted.json`

## Production Deployment

To deploy to real AWS:

1. **Configure AWS credentials:**
```bash
aws configure
```

2. **Deploy to production:**
```bash
serverless deploy --stage prod
```

3. **Update environment variables in frontend:**
```bash
# In jheem-portal/.env.local
NEXT_PUBLIC_API_BASE_URL=https://{api-id}.execute-api.us-east-1.amazonaws.com/prod
```

## Environment Variables

| Variable | Description | Local Value | Production Value |
|----------|-------------|-------------|------------------|
| `S3_BUCKET_NAME` | S3 bucket for plots | `prerun-plots-bucket-local` | `prerun-plots-bucket-prod` |
| `S3_ENDPOINT_URL` | S3 endpoint | `http://host.docker.internal:4566` | (not set - uses AWS) |
| `AWS_ACCESS_KEY_ID` | AWS access key | `test` | (from AWS credentials) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `test` | (from AWS credentials) |

## Related Repositories

- **Frontend**: `jheem-portal` - Next.js application that consumes this API
- **Plot Generation**: `jheem2_interactive` - R scripts that generate the plot JSON files
- **Group Website**: `jhu-comp-epi` - Main research group website

## Contributing

This is part of a larger effort to modernize the JHEEM epidemiological modeling interface, transitioning from a Shiny-based application to a cloud-native serverless architecture.

The current implementation focuses on serving pre-generated plots for "prerun scenarios." Future development will include:
- Custom model execution endpoints
- Real-time job status tracking
- Additional plot types and data formats
