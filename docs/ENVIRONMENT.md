# Environment Configuration

## Local Development Setup

### Quick Setup
```bash
# Auto-configure environment for LocalStack
./setup_local_env.sh

# Then run orchestration
python scripts/local_orchestration.py orchestration_configs/master_config_medium.yaml --max-parallel 2
```

### Manual Setup
```bash
# Get current LocalStack API Gateway ID
awslocal apigateway get-rest-apis --query 'items[0].id' --output text

# Set environment variable
export JHEEM_API_GATEWAY_ID="your-api-gateway-id"

# Or save to .env.local for persistence
echo "JHEEM_API_GATEWAY_ID=your-api-gateway-id" > .env.local
source .env.local
```

## Production Setup

### AWS Production Environment
```bash
# Set production API Gateway ID
export JHEEM_API_GATEWAY_ID="your-production-api-gateway-id"

# Or set in your CI/CD system as a secret
# GitHub Actions: Add JHEEM_API_GATEWAY_ID to repository secrets
# AWS Lambda: Set as environment variable in serverless.yml
```

### GitHub Actions
Add these secrets to your GitHub repository:
- `JHEEM_API_GATEWAY_ID`: Your production API Gateway ID
- `AWS_ACCESS_KEY_ID`: Production AWS access key
- `AWS_SECRET_ACCESS_KEY`: Production AWS secret key

## Environment Variables

| Variable | Description | Local Example | Production Example |
|----------|-------------|---------------|-------------------|
| `JHEEM_API_GATEWAY_ID` | API Gateway ID for plot registration | `jmvl1gdtfx` | `abc123xyz` |
| `AWS_ACCESS_KEY_ID` | AWS credentials (production only) | (auto from awslocal) | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials (production only) | (auto from awslocal) | `secret...` |

## Troubleshooting

### LocalStack Restart
When LocalStack restarts, the API Gateway ID changes:
```bash
# Re-run setup after LocalStack restart
./setup_local_env.sh
```

### Missing Environment Variable
If you see "Could not determine API Gateway ID":
1. Check LocalStack is running: `localstack status`
2. Verify API Gateway exists: `awslocal apigateway get-rest-apis`
3. Run setup script: `./setup_local_env.sh`

### Production Deployment
For production, ensure `JHEEM_API_GATEWAY_ID` is set to your production API Gateway ID, not the LocalStack development ID.
