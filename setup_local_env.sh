#!/bin/bash

# setup_local_env.sh
# Quick setup script for JHEEM local development environment

echo "🔧 Setting up JHEEM local development environment..."

# Auto-detect current LocalStack API Gateway ID
echo "🔍 Detecting current LocalStack API Gateway ID..."
API_ID=$(awslocal apigateway get-rest-apis --query 'items[0].id' --output text 2>/dev/null)

if [ "$API_ID" != "None" ] && [ -n "$API_ID" ]; then
    echo "✅ Found API Gateway ID: $API_ID"
    
    # Export for current session
    export JHEEM_API_GATEWAY_ID="$API_ID"
    
    # Add to .env file for persistence
    echo "JHEEM_API_GATEWAY_ID=$API_ID" > .env.local
    
    echo "🔑 Environment variable set:"
    echo "   JHEEM_API_GATEWAY_ID=$API_ID"
    echo ""
    echo "📝 Saved to .env.local for persistence"
    echo ""
    echo "🚀 Ready to run orchestration:"
    echo "   python scripts/local_orchestration.py orchestration_configs/master_config_medium.yaml --max-parallel 2"
    echo ""
    echo "💡 In future sessions, source the environment:"
    echo "   source .env.local"
    
else
    echo "❌ Could not detect API Gateway ID"
    echo "   Make sure LocalStack is running and has deployed resources"
    echo "   Try: localstack status"
    exit 1
fi
