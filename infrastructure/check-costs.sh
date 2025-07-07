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
