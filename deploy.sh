#!/bin/bash
# 82ndrop Deployment Script
# Supports both staging and production deployments with enhanced workflow

set -e

# Default to staging if no environment specified
ENVIRONMENT=${1:-staging}
echo "🚀 Deploying 82ndrop to ${ENVIRONMENT} Environment"
echo "============================================"

# Configuration based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    PROJECT_ID="taajirah"
    SERVICE_NAME="drop-agent"
    MIN_INSTANCES=1
    MAX_INSTANCES=10
    MEMORY="4Gi"
    CPU=4
else
    PROJECT_ID="taajirah"
    SERVICE_NAME="drop-agent-staging"
    MIN_INSTANCES=0
    MAX_INSTANCES=2
    MEMORY="2Gi"
    CPU=2
fi

REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "📋 Configuration:"
echo "  Environment: ${ENVIRONMENT}"
echo "  Project: ${PROJECT_ID}"
echo "  Service: ${SERVICE_NAME}"
echo "  Region: ${REGION}"
echo "  Image: ${IMAGE_NAME}"
echo "  Resources: ${CPU} CPU, ${MEMORY} RAM"
echo ""

# Verify the enhanced workflow files
echo "🔍 Verifying enhanced workflow components..."
required_files=(
    "drop_agent/agent.py"
    "drop_agent/prompts.py"
    "drop_agent/sub_agents/guide/agent.py"
    "drop_agent/sub_agents/search/agent.py"
    "drop_agent/sub_agents/prompt_writer/agent.py"
    "drop_agent/sub_agents/video_generator/agent.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Required file $file not found"
        exit 1
    fi
done

echo "✅ All required files present"

# Build Docker image
echo "🔨 Building ${ENVIRONMENT} Docker image..."
docker build -t ${IMAGE_NAME} \
    --build-arg ENVIRONMENT=${ENVIRONMENT} \
    --build-arg GOOGLE_CLOUD_PROJECT=${PROJECT_ID} .

# Push to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run (${ENVIRONMENT})..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8000 \
    --memory ${MEMORY} \
    --cpu ${CPU} \
    --min-instances ${MIN_INSTANCES} \
    --max-instances ${MAX_INSTANCES} \
    --timeout 300 \
    --set-env-vars ENVIRONMENT=${ENVIRONMENT} \
    --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
    --set-env-vars FIREBASE_DATABASE_URL=https://taajirah-default-rtdb.europe-west1.firebasedatabase.app/ \
    --set-env-vars LOG_LEVEL=DEBUG \
    --project ${PROJECT_ID}

# Get the deployment URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)" --project=${PROJECT_ID})

echo ""
echo "✅ ${ENVIRONMENT} Deployment Complete!"
echo "🔗 Service URL: ${SERVICE_URL}"
echo ""

# Test the deployment
echo "🔍 Testing deployment..."
sleep 5

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "${SERVICE_URL}/health" || echo "FAILED")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $HEALTH_RESPONSE"
fi

echo ""
echo "🎯 Enhanced Workflow Verification:"
echo "1. Test the complete video generation pipeline:"
echo "   curl -X POST ${SERVICE_URL}/generate-video \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"prompt\":\"test video\",\"user_id\":\"test_user\"}'"
echo ""
echo "2. Verify each step in the workflow:"
echo "   - Guide Agent analysis"
echo "   - Search Agent trend research"
echo "   - Prompt Writer template creation"
echo "   - Video Generator production"
echo ""
echo "3. Monitor the enhanced workflow:"
echo "   - Check Firebase for step completion"
echo "   - Verify trend integration"
echo "   - Confirm proper template usage"
echo ""

if [ "$ENVIRONMENT" = "staging" ]; then
    echo "🧪 Next Steps (Staging):"
    echo "1. Test the enhanced workflow thoroughly"
    echo "2. Verify trend research integration"
    echo "3. Validate template composition"
    echo "4. Once satisfied, deploy to production:"
    echo "   ./deploy.sh production"
else
    echo "🎬 Next Steps (Production):"
    echo "1. Monitor production metrics"
    echo "2. Watch for successful video generations"
    echo "3. Check trend integration quality"
    echo "4. Verify user cost tracking"
fi 