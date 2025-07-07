#!/bin/bash

# Create minimal test infrastructure to validate AWS costs
# This creates tiny resources to understand pricing before full deployment

echo "🧪 Creating test infrastructure for cost validation..."

# 1. Create test S3 bucket
echo "📦 Creating test S3 bucket..."
aws s3 mb s3://jheem-test-tiny-bucket --region us-east-1

# Add bucket tagging for cost tracking
aws s3api put-bucket-tagging \
  --bucket jheem-test-tiny-bucket \
  --tagging 'TagSet=[{Key=Project,Value=jheem},{Key=Environment,Value=test}]'

# 2. Create test DynamoDB table
echo "🗄️ Creating test DynamoDB table..."
aws dynamodb create-table \
  --table-name jheem-test-tiny \
  --attribute-definitions \
    AttributeName=city,AttributeType=S \
    AttributeName=plot_id,AttributeType=S \
  --key-schema \
    AttributeName=city,KeyType=HASH \
    AttributeName=plot_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Project,Value=jheem Key=Environment,Value=test \
  --region us-east-1

# 3. Test S3 operations (simulate plot uploads)
echo "📤 Testing S3 operations..."

# Create a small test file (simulating a JSON plot)
cat > test-plot.json << 'EOF'
{
  "data": [{"x": [1,2,3], "y": [4,5,6], "type": "scatter"}],
  "layout": {"title": "Test Plot", "xaxis": {"title": "X"}, "yaxis": {"title": "Y"}}
}
EOF

# Upload test files (simulate 10 plots)
for i in {1..10}; do
  aws s3 cp test-plot.json s3://jheem-test-tiny-bucket/plots/test_city_${i}.json \
    --metadata project=jheem,environment=test
done

echo "📊 Uploaded 10 test plots to S3"

# 4. Test DynamoDB operations
echo "🗄️ Testing DynamoDB operations..."

# Insert test records (simulate plot metadata)
for i in {1..10}; do
  aws dynamodb put-item \
    --table-name jheem-test-tiny \
    --item '{
      "city": {"S": "C.12580"},
      "plot_id": {"S": "test_plot_'$i'"},
      "scenario": {"S": "cessation"},
      "outcome": {"S": "incidence"},
      "s3_key": {"S": "plots/test_city_'$i'.json"},
      "file_size": {"N": "256"},
      "created_at": {"S": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}
    }' \
    --region us-east-1
done

echo "📊 Inserted 10 test records into DynamoDB"

# 5. Test query operations (simulate discovery API)
echo "🔍 Testing query operations..."

aws dynamodb query \
  --table-name jheem-test-tiny \
  --key-condition-expression "city = :city" \
  --expression-attribute-values '{":city":{"S":"C.12580"}}' \
  --region us-east-1 > query-test-results.json

echo "📊 Query test completed"

# 6. Calculate approximate costs
echo "💰 Estimating costs for this test..."
echo ""
echo "📊 Test Resources Created:"
echo "   - S3 Bucket: jheem-test-tiny-bucket"
echo "   - 10 JSON files (~256 bytes each = 2.56 KB total)"
echo "   - DynamoDB table: jheem-test-tiny" 
echo "   - 10 items inserted + 1 query"
echo ""
echo "💵 Estimated daily costs for this test:"
echo "   - S3 Storage: ~\$0.0000006/day (2.56 KB)"
echo "   - S3 Requests: ~\$0.000044 (10 PUTs + 1 GET)"
echo "   - DynamoDB: ~\$0.00000125/day (10 WCU + 1 RCU)"
echo "   - Total: <\$0.001/day (<\$0.03/month)"
echo ""
echo "📈 Scaling estimates:"
echo "   - 900 plots (medium test): ~\$0.09/month"
echo "   - 64K plots (full scale): ~\$6.40/month" 
echo "   - Add ~\$5/month for API Gateway if used"
echo ""
echo "🎯 Target: \$50/month budget looks very comfortable!"

# 7. Create cost monitoring script
cat > check-costs.sh << 'EOF'
#!/bin/bash
echo "💰 Current JHEEM costs:"
aws ce get-cost-and-usage \
  --time-period Start=2025-07-01,End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --filter file://cost-filter.json

cat > cost-filter.json << 'FILTER'
{
  "Tags": {
    "Key": "Project",
    "Values": ["jheem"]
  }
}
FILTER
EOF

chmod +x check-costs.sh

echo ""
echo "✅ Test infrastructure created successfully!"
echo ""
echo "📋 What to do now:"
echo "1. Wait 24-48 hours for costs to appear in billing"
echo "2. Run './check-costs.sh' to see actual costs"
echo "3. Check AWS Cost Explorer: https://console.aws.amazon.com/ce/home"
echo "4. If costs look good, proceed with GitHub Actions test"
echo ""
echo "🧹 To clean up test resources later:"
echo "   aws s3 rb s3://jheem-test-tiny-bucket --force"
echo "   aws dynamodb delete-table --table-name jheem-test-tiny"

# Cleanup temp files
rm test-plot.json query-test-results.json
