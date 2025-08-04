#!/bin/bash
# ECR Repository Setup Script
# Sets up ECR repository with lifecycle policy for JHEEM container

set -e

REPOSITORY_NAME="jheem-ryan-white-model"
REGION="us-east-1"
ACCOUNT_ID="849611540600"

echo "🏗️  Setting up ECR repository: $REPOSITORY_NAME"

# Create ECR repository
echo "Creating ECR repository..."
aws ecr create-repository --repository-name $REPOSITORY_NAME --region $REGION || echo "Repository may already exist"

# Create lifecycle policy (keep only 1 image)
echo "Setting up lifecycle policy..."
cat > lifecycle-policy.json << EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep only the most recent image",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 1
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF

# Apply lifecycle policy
aws ecr put-lifecycle-policy \
  --repository-name $REPOSITORY_NAME \
  --lifecycle-policy-text file://lifecycle-policy.json

# Create and attach ECR policy to GitHub Actions user
echo "Setting up IAM permissions..."
aws iam create-policy \
    --policy-name JheemECRPolicy \
    --policy-document file://ecr-policy.json || echo "Policy may already exist"

aws iam attach-user-policy \
    --user-name jheem-github-actions \
    --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/JheemECRPolicy || echo "Policy may already be attached"

echo "✅ ECR setup complete!"
echo "Repository URI: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME"
echo "Max storage cost: ~$0.50/month (1 image × 5GB)"

# Cleanup
rm -f lifecycle-policy.json