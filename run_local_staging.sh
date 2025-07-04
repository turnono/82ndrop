#!/bin/bash

# Set environment variables for staging
export GOOGLE_CLOUD_PROJECT="taajirah"
export GOOGLE_CLOUD_LOCATION="us-central1"
export FIREBASE_PROJECT_ID="taajirah"
export FIREBASE_DATABASE_URL="https://taajirah-default-rtdb.europe-west1.firebasedatabase.app"
export ENV="staging"
export LOG_LEVEL="DEBUG"
export PORT=8000

# Set Firebase ID token for turnono@gmail.com
# This is a development token that identifies you as an authorized user
export LOCAL_DEV_TOKEN="turnono@gmail.com"
export SKIP_AUTH="true"  # Allow local development mode

# Set service account credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/taajirah-agents-service-account.json"
echo "✅ Using service account: taajirah-agents-service-account.json"

echo "🚀 Starting local server with staging configuration..."
echo "📝 Environment variables set:"
echo "  GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
echo "  GOOGLE_CLOUD_LOCATION: $GOOGLE_CLOUD_LOCATION"
echo "  FIREBASE_PROJECT_ID: $FIREBASE_PROJECT_ID"
echo "  ENV: $ENV"
echo "  PORT: $PORT"
echo "  USER: $LOCAL_DEV_TOKEN (authorized for video generation)"
echo "  CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS"

# Start the server
python main.py 