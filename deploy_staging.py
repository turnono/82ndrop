#!/usr/bin/env python3
"""
Deploy to staging environment for isolated testing
Separate from production to safely test video generation fixes
"""

import subprocess
import os
import json
import sys

def deploy_staging():
    """Deploy to staging environment with test configurations"""
    
    print("🚀 Deploying 82ndrop to Staging Environment")
    print("=" * 50)
    
    # 1. Create staging environment variables
    staging_env = {
        "ENVIRONMENT": "staging",
        "GOOGLE_CLOUD_PROJECT": "82ndrop-staging",
        "FIREBASE_DATABASE_URL": "https://82ndrop-staging-default-rtdb.firebaseio.com/",
        "ALLOWED_ORIGINS": "https://82ndrop-staging.web.app,https://82ndrop-staging.firebaseapp.com",
        "LOG_LEVEL": "DEBUG",
        "ENABLE_DEBUG_LOGGING": "true"
    }
    
    # 2. Update main.py for staging
    staging_main_content = """
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import your existing agent code
from drop_agent.agent import DropAgent
from drop_agent.custom_tools import *

app = FastAPI(title="82ndrop Staging API", version="1.0.0")

# Staging-specific CORS (more permissive for testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://82ndrop-staging.web.app",
        "https://82ndrop-staging.firebaseapp.com",
        "http://localhost:4200",
        "http://localhost:4201"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "staging",
        "timestamp": int(time.time()),
        "features": {
            "video_generation": True,
            "api_key_model": True,
            "cors_debug": True
        }
    }

@app.get("/staging-info")
async def staging_info():
    return {
        "message": "This is the staging environment for 82ndrop",
        "purpose": "Safe testing without affecting production",
        "video_generation": "Real Veo API calls with user API keys",
        "cors_origins": app.middleware[0].kwargs.get('allow_origins', [])
    }

# Include your existing routes here
# ... rest of your routes

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
"""
    
    with open('main_staging.py', 'w') as f:
        f.write(staging_main_content.strip())
    
    # 3. Create staging deployment script
    deploy_script = """#!/bin/bash
# Deploy to staging environment

echo "🚀 Deploying to Staging..."

# Build staging Docker image
docker build -t gcr.io/82ndrop-staging/drop-agent-staging .

# Push to Google Container Registry
docker push gcr.io/82ndrop-staging/drop-agent-staging

# Deploy to Cloud Run (staging)
gcloud run deploy drop-agent-staging \\
  --image gcr.io/82ndrop-staging/drop-agent-staging \\
  --platform managed \\
  --region us-central1 \\
  --allow-unauthenticated \\
  --port 8002 \\
  --set-env-vars ENVIRONMENT=staging \\
  --set-env-vars GOOGLE_CLOUD_PROJECT=82ndrop-staging \\
  --project 82ndrop-staging

echo "✅ Staging deployment completed!"
echo "🔗 Staging URL: https://drop-agent-staging-[PROJECT-HASH].us-central1.run.app"
"""
    
    with open('deploy_staging.sh', 'w') as f:
        f.write(deploy_script.strip())
    
    os.chmod('deploy_staging.sh', 0o755)
    
    print("✅ Created staging deployment files")
    print("📋 Staging Environment Setup Complete")
    
    return True

if __name__ == "__main__":
    deploy_staging() 