#!/bin/bash
# Test the staging environment deployment

echo "🧪 82ndrop Staging Environment Test"
echo "===================================="

# Deploy staging
echo "1️⃣ Deploying to staging..."
./deploy_staging.sh

if [ $? -ne 0 ]; then
    echo "❌ Staging deployment failed"
    exit 1
fi

# Get staging URL
STAGING_URL="https://drop-agent-staging-855515190257.us-central1.run.app"

echo ""
echo "2️⃣ Testing staging endpoints..."

# Test health endpoint
echo "🏥 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${STAGING_URL}/health")
echo "Response: $HEALTH_RESPONSE"

# Test run endpoint (should require auth)
echo ""
echo "🔐 Testing /run endpoint (expect 401)..."
RUN_RESPONSE=$(curl -s -w "HTTP_%{http_code}" -X POST "${STAGING_URL}/run" \
  -H "Content-Type: application/json" \
  -d '{"message":"test staging","user_id":"staging_test"}')
echo "Response: $RUN_RESPONSE"

echo ""
echo "3️⃣ Video Generation Features to Test:"
echo "  ✅ API Key Setup Guide"
echo "  ✅ Veo Pricing Information"  
echo "  ✅ Real Video Generation (with user API keys)"
echo "  ✅ Job Status Polling"

echo ""
echo "4️⃣ Frontend Testing:"
echo "  • Update frontend to use staging environment"
echo "  • Test authentication flow"
echo "  • Test video generation with real API keys"

echo ""
echo "🎯 Staging Environment Ready!"
echo "   URL: ${STAGING_URL}"
echo "   Same as production but isolated for testing"
echo ""
echo "💡 Next: Test video generation end-to-end in staging" 