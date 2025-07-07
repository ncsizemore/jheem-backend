# AWS Infrastructure Guide for JHEEM Project

This is a complete reference guide for AWS setup, management, and troubleshooting for the JHEEM plot generation project.

## Quick Reference

### Current AWS Setup
- **Account**: 849611540600
- **Region**: us-east-1
- **Budget**: $50/month (matching current Shiny costs)
- **Free Tier Status**: Active (test resources cost $0.00)

### Key Resources
- **Admin User**: `ncsizemore` (development user)
- **GitHub Actions User**: `jheem-github-actions` (limited permissions)
- **Test Bucket**: `jheem-test-tiny-bucket`
- **Test Table**: `jheem-test-tiny`

## AWS CLI Setup

### Current CLI Configuration
This project uses **AWS CLI v2** (global installation, no virtual environment needed):
```bash
aws --version
# Should show: aws-cli/2.x.x Python/3.x.x Darwin/24.5.0 botocore/2.x.x
```

### Credential Management
```bash
# Check current user
aws sts get-caller-identity

# Admin credentials are stored in:
~/.aws/credentials    # Access keys
~/.aws/config        # Region and output settings
```

### Multi-Environment Usage
- **Production AWS**: Use `aws` commands directly
- **LocalStack Development**: 
  ```bash
  source ~/localstack-env/bin/activate
  awslocal s3 ls
  ```

## User Management

### Admin User (Development Account)
- **Username**: `ncsizemore`
- **Permissions**: AdministratorAccess
- **Use for**: Development, infrastructure management, debugging
- **MFA**: Enabled on root account

### GitHub Actions User (Automation Account)
- **Username**: `jheem-github-actions`
- **Permissions**: Limited to `jheem-*` resources only
- **Use for**: Automated plot generation via GitHub Actions
- **Access Keys**: Stored in GitHub Secrets

### GitHub Actions User Permissions
The limited user can ONLY:
- **S3**: Read/write objects in `jheem-*` buckets
- **DynamoDB**: Read/write items in `jheem-*` tables
- **CloudWatch**: Send metrics to `JHEEM/PlotGeneration` namespace

The limited user CANNOT:
- Access other AWS services (EC2, IAM, etc.)
- Create/delete infrastructure
- Access non-JHEEM resources
- Incur costs outside JHEEM scope

## Cost Management

### Budget Setup
- **Monthly Budget**: $50
- **Email Alerts**: nsizemo1@jh.edu
- **Alert Thresholds**: 
  - $10 (20%) - Early warning
  - $25 (50%) - Investigation needed
  - $40 (80%) - Emergency action required

### Free Tier Coverage
JHEEM usage is well within AWS Free Tier:
- **S3**: 5 GB storage (project uses ~64 MB for 64K plots)
- **S3 Requests**: 20K GET + 2K PUT (will exceed PUT at full scale = ~$0.31)
- **DynamoDB**: 25 GB storage + 200M requests (project uses tiny fraction)
- **Expected Monthly Cost**: $0.31 for full 64K plots

### Cost Monitoring
```bash
# Check current costs (after 24-48 hours)
cd infrastructure
./check-costs.sh

# View in console
# https://console.aws.amazon.com/billing/home#/bills
# https://console.aws.amazon.com/billing/home#/budgets
```

## Infrastructure Scripts

### Setup Scripts Location
```
jheem-backend/infrastructure/
├── aws-cost-monitoring.sh     # Budget and alerts
├── github-actions-iam.sh      # Limited user creation
├── test-infrastructure.sh     # Test resources
└── README.md                  # This file
```

### Running Scripts
```bash
cd infrastructure

# 1. Set up cost monitoring (safe, no billable resources)
bash aws-cost-monitoring.sh

# 2. Create GitHub Actions user (safe, just IAM user)
bash github-actions-iam.sh

# 3. Create test infrastructure (creates tiny billable resources)
bash test-infrastructure.sh
```

## Current Test Infrastructure

### Resources Created
- **S3 Bucket**: `jheem-test-tiny-bucket`
  - Contains 10 test JSON files in `plots/` folder
  - Total size: ~2.56 KB
  - Cost: $0.00 (free tier)

- **DynamoDB Table**: `jheem-test-tiny`
  - Contains 10 test metadata records
  - Cost: $0.00 (free tier)

### Testing Commands
```bash
# Test S3 access
aws s3 ls s3://jheem-test-tiny-bucket/plots/

# Test DynamoDB access
aws dynamodb scan --table-name jheem-test-tiny --max-items 3

# Test GitHub Actions user access
export AWS_ACCESS_KEY_ID=github-actions-access-key
export AWS_SECRET_ACCESS_KEY=github-actions-secret-key
aws s3 ls s3://jheem-test-tiny-bucket/    # Should work
aws iam list-users                        # Should fail (good!)
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
```

## GitHub Integration

### GitHub Secrets Required
In GitHub repository settings → Secrets and variables → Actions:
- `AWS_ACCESS_KEY_ID`: From `jheem-github-actions` user
- `AWS_SECRET_ACCESS_KEY`: From `jheem-github-actions` user
- `AWS_REGION`: `us-east-1`

### Workflow Integration
The GitHub Actions workflow uses these secrets to:
1. Upload generated plot JSON files to S3
2. Register plot metadata in DynamoDB
3. Send performance metrics to CloudWatch

## Security Best Practices

### Implementation Status
- ✅ Root account secured with MFA
- ✅ Working through IAM user (not root)
- ✅ Created limited user for automation
- ✅ Least-privilege permissions
- ✅ Cost monitoring and budgets
- ✅ Free tier usage validation

### Access Key Management
- **Never commit access keys to git**
- **Rotate keys periodically** (every 90 days recommended)
- **Use GitHub Secrets** for automation credentials
- **Monitor usage** in AWS CloudTrail if needed

## Troubleshooting

### Common Issues

#### "Access Denied" Errors
```bash
# Check which user is active
aws sts get-caller-identity

# If wrong user, check credentials
cat ~/.aws/credentials
aws configure list
```

#### Cost Alerts Not Working
- Check email: nsizemo1@jh.edu
- Billing data takes 24-48 hours to appear
- Verify budget exists in AWS Console

#### GitHub Actions Failures
1. **Check GitHub Secrets** are set correctly
2. **Verify IAM user permissions** in AWS Console
3. **Test access keys manually** with AWS CLI
4. **Check AWS resource exists** (bucket, table names)

### Useful Console Links
- **Billing Dashboard**: https://console.aws.amazon.com/billing/home#/bills
- **Cost Explorer**: https://console.aws.amazon.com/ce/home
- **IAM Users**: https://console.aws.amazon.com/iam/home#/users
- **S3 Buckets**: https://console.aws.amazon.com/s3/
- **DynamoDB Tables**: https://console.aws.amazon.com/dynamodb/

## Project Scaling Plan

### Current Status: Test Infrastructure
- 10 test plots in S3
- 10 test records in DynamoDB  
- Cost: $0.00/month
- Purpose: Validate AWS integration

### Next: Small GitHub Actions Test
- 1-2 cities via GitHub Actions
- ~300 plots total
- Expected cost: $0.00/month (free tier)
- Purpose: Validate end-to-end pipeline

### Future: Full Production Scale
- 31 cities, 64K total plots
- Expected cost: ~$0.31/month
- Well under $50 budget
- Purpose: Replace legacy Shiny application

## Quick Commands Reference

```bash
# Check AWS setup
aws sts get-caller-identity
aws s3 ls
aws dynamodb list-tables

# Switch to LocalStack
source ~/localstack-env/bin/activate
awslocal s3 ls

# Check costs (after 24-48 hours)
cd infrastructure && ./check-costs.sh

# Test limited user permissions
export AWS_ACCESS_KEY_ID=github-actions-key
aws s3 ls s3://jheem-test-tiny-bucket/  # Should work
aws iam list-users                      # Should fail
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
```

## Support Contacts

- **AWS Support**: Account has basic support
- **Billing Questions**: AWS Billing Dashboard or support tickets
- **JHEEM Project**: This documentation and session history
- **Emergency**: Delete resources manually via AWS Console if costs spike
