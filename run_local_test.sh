#!/bin/bash

# 82ndrop Local Testing Script
# This script sets up the environment and runs local tests

echo "🔧 82ndrop Local Testing Setup"
echo "================================"

# Set environment variables
export LOCAL_DEV_TOKEN="firebase"
export GOOGLE_APPLICATION_CREDENTIALS=""  # Disable service account for local testing

echo "✅ Environment configured for local testing"
echo "   LOCAL_DEV_TOKEN=firebase"
echo "   Using Firebase token directly"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Consider running: source .venv/bin/activate"
fi

echo ""
echo "🚀 Starting local server..."
echo "   Server will run on http://localhost:8000"
echo "   Press Ctrl+C to stop the server"
echo ""

# Start the server
python main.py 