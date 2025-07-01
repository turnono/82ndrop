#!/bin/bash
# 82ndrop Staging Deployment
# Creates a production-like environment for testing video generation

set -e

echo "🚀 Deploying 82ndrop to Staging Environment"
echo "============================================"

# Configuration
PROJECT_ID="taajirah"
STAGING_SERVICE="drop-agent-staging"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${STAGING_SERVICE}"

echo "📋 Configuration:"
echo "  Project: ${PROJECT_ID}"
echo "  Service: ${STAGING_SERVICE}"
echo "  Region: ${REGION}"
echo "  Image: ${IMAGE_NAME}"
echo ""

# Build staging image
echo "🔨 Building staging Docker image..."
docker build -t ${IMAGE_NAME} .

# Push to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run (Staging)..."
gcloud run deploy ${STAGING_SERVICE} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=staging \
  --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  --set-env-vars FIREBASE_DATABASE_URL=https://taajirah-default-rtdb.europe-west1.firebasedatabase.app/ \
  --set-env-vars LOG_LEVEL=DEBUG \
  --project ${PROJECT_ID}

# Get the staging URL
STAGING_URL=$(gcloud run services describe ${STAGING_SERVICE} --region=${REGION} --format="value(status.url)" --project=${PROJECT_ID})

echo ""
echo "✅ Staging Deployment Complete!"
echo "🔗 Staging URL: ${STAGING_URL}"
echo ""
echo "🧪 Test Commands:"
echo "  Health Check: curl ${STAGING_URL}/health"
echo "  Frontend Test: curl -X POST ${STAGING_URL}/run -H 'Content-Type: application/json' -d '{\"message\":\"test\",\"user_id\":\"staging_test\"}'"
echo ""
echo "🎬 Video Generation Testing:"
echo "  The staging environment uses the same Veo API integration"
echo "  Users can test with their real Google Cloud API keys"
echo "  All video generation costs are paid directly to Google"
echo ""

# Test the deployment
echo "🔍 Testing staging deployment..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${STAGING_URL}/health" || echo "FAILED")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $HEALTH_RESPONSE"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Update frontend to point to staging for testing"
echo "2. Test video generation with real API keys"
echo "3. Validate the 'pay Google directly' model"
echo "4. Once satisfied, deploy the same code to production" 