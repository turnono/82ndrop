#!/bin/bash

# 82ndrop Local Development Setup Script
# This script sets up the environment variables needed for local development

echo "🔧 Setting up 82ndrop local development environment..."

# Set required environment variables
export GOOGLE_CLOUD_PROJECT=taajirah
export FIREBASE_DATABASE_URL=https://taajirah-default-rtdb.europe-west1.firebasedatabase.app/
export GOOGLE_CLOUD_LOCATION=us-central1
export LOCAL_DEV_TOKEN=firebase
export LOG_LEVEL=DEBUG

echo "✅ Environment variables set:"
echo "   GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT"
echo "   FIREBASE_DATABASE_URL=$FIREBASE_DATABASE_URL"
echo "   GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION"
echo "   LOCAL_DEV_TOKEN=$LOCAL_DEV_TOKEN"
echo "   LOG_LEVEL=$LOG_LEVEL"

echo ""
echo "🚀 You can now start the services:"
echo "   Backend: python main.py"
echo "   Frontend: cd frontend && npm start"
echo ""
echo "⚠️  Note: Remember to source this script to set variables in your shell:"
echo "   source setup_local_dev.sh" 