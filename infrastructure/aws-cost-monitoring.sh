#!/bin/bash

# AWS Cost Monitoring Setup for JHEEM Project 
# Run this to set up comprehensive cost tracking

echo "🏦 Setting up AWS Cost Monitoring..."

# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Email for alerts
YOUR_EMAIL="nsizemo1@jh.edu"

# 1. Create Simple Budget
echo "📊 Creating AWS Budget..."

cat > budget-config-simple.json << EOF
{
  "BudgetName": "jheem-production-budget-cli",
  "BudgetLimit": {
    "Amount": "50.00",
    "Unit": "USD"
  },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
EOF

# Create budget (skip if already exists)
aws budgets create-budget \
  --account-id $ACCOUNT_ID \
  --budget file://budget-config-simple.json 2>/dev/null || echo "Budget may already exist"

# 2. Create notifications separately, then add subscribers
echo "🚨 Setting up Budget Alerts..."

# Create notification configs
cat > notification-20.json << EOF
{
  "NotificationType": "ACTUAL",
  "ComparisonOperator": "GREATER_THAN",
  "Threshold": 20.0,
  "ThresholdType": "PERCENTAGE"
}
EOF

cat > notification-50.json << EOF
{
  "NotificationType": "ACTUAL",
  "ComparisonOperator": "GREATER_THAN",
  "Threshold": 50.0,
  "ThresholdType": "PERCENTAGE"
}
EOF

cat > notification-80.json << EOF
{
  "NotificationType": "ACTUAL",
  "ComparisonOperator": "GREATER_THAN",
  "Threshold": 80.0,
  "ThresholdType": "PERCENTAGE"
}
EOF

# Create notifications
aws budgets create-notification \
  --account-id $ACCOUNT_ID \
  --budget-name "jheem-production-budget-cli" \
  --notification file://notification-20.json 2>/dev/null || echo "20% notification may already exist"

aws budgets create-notification \
  --account-id $ACCOUNT_ID \
  --budget-name "jheem-production-budget-cli" \
  --notification file://notification-50.json 2>/dev/null || echo "50% notification may already exist"

aws budgets create-notification \
  --account-id $ACCOUNT_ID \
  --budget-name "jheem-production-budget-cli" \
  --notification file://notification-80.json 2>/dev/null || echo "80% notification may already exist"

# Create subscribers
aws budgets create-subscriber \
  --account-id $ACCOUNT_ID \
  --budget-name "jheem-production-budget-cli" \
  --notification file://notification-20.json \
  --subscriber SubscriptionType=EMAIL,Address=$YOUR_EMAIL 2>/dev/null || echo "20% subscriber may already exist"

aws budgets create-subscriber \
  --account-id $ACCOUNT_ID \
  --budget-name "jheem-production-budget-cli" \
  --notification file://notification-50.json \
  --subscriber SubscriptionType=EMAIL,Address=$YOUR_EMAIL 2>/dev/null || echo "50% subscriber may already exist"

aws budgets create-subscriber \
  --account-id $ACCOUNT_ID \
  --budget-name "jheem-production-budget-cli" \
  --notification file://notification-80.json \
  --subscriber SubscriptionType=EMAIL,Address=$YOUR_EMAIL 2>/dev/null || echo "80% subscriber may already exist"

echo "✅ Cost monitoring setup complete!"
echo ""
echo "📧 Email alerts configured for: $YOUR_EMAIL"
echo "   - At 20% of budget (\$10) - Early warning"
echo "   - At 50% of budget (\$25) - Investigation needed"  
echo "   - At 80% of budget (\$40) - Emergency action required"
echo ""
echo "💡 View your costs at: https://console.aws.amazon.com/billing/home#/bills"
echo "💡 View your budget at: https://console.aws.amazon.com/billing/home#/budgets"
echo ""
echo "🎯 Since you already have a manual budget, you can delete this CLI one if preferred."

# Cleanup temp files
rm budget-config-simple.json notification-*.json
