#!/bin/bash

# Create Limited IAM User for GitHub Actions
# This user will have minimal permissions for just JHEEM plot generation

echo "👤 Creating GitHub Actions IAM User..."

# 1. Create the IAM user
aws iam create-user \
  --user-name jheem-github-actions \
  --tags Key=Project,Value=jheem Key=Purpose,Value=github-actions

# 2. Create minimal permissions policy
cat > jheem-minimal-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3PlotStorage",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject", 
        "s3:DeleteObject",
        "s3:PutObjectAcl"
      ],
      "Resource": [
        "arn:aws:s3:::jheem-plots-*/*",
        "arn:aws:s3:::jheem-test-*/*"
      ]
    },
    {
      "Sid": "S3BucketOperations",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::jheem-plots-*",
        "arn:aws:s3:::jheem-test-*"
      ]
    },
    {
      "Sid": "DynamoDBPlotMetadata",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:*:*:table/jheem-plot-metadata-*",
        "arn:aws:dynamodb:*:*:table/jheem-test-*"
      ]
    },
    {
      "Sid": "CloudWatchMetrics",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "JHEEM/PlotGeneration"
        }
      }
    }
  ]
}
EOF

# 3. Create the policy
aws iam create-policy \
  --policy-name JheemGitHubActionsPolicy \
  --policy-document file://jheem-minimal-policy.json \
  --description "Minimal permissions for JHEEM plot generation via GitHub Actions"

# 4. Attach policy to user
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam attach-user-policy \
  --user-name jheem-github-actions \
  --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/JheemGitHubActionsPolicy

# 5. Create access keys for GitHub Actions
echo "🔑 Creating access keys..."
aws iam create-access-key --user-name jheem-github-actions > github-actions-keys.json

echo "✅ GitHub Actions user created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Save the access keys from github-actions-keys.json"
echo "2. Add them to GitHub Secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "3. Delete github-actions-keys.json after saving"
echo ""
echo "🔒 Security note: This user can only access jheem-* resources"

# Show the created access keys (one time only)
echo ""
echo "🔑 Access Keys (save these immediately):"
cat github-actions-keys.json
echo ""
echo "⚠️  IMPORTANT: Delete github-actions-keys.json after saving these keys!"

# Cleanup policy file
rm jheem-minimal-policy.json
