#!/usr/bin/env python3
"""
Staging Deployment Script
Deploys the enhanced workflow to staging with proper Firebase authentication
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Configuration
PROJECT_ID = "taajirah"
REGION = "us-central1"
SERVICE_NAME = "drop-agent-staging"
ENV_VARS = {
    "GOOGLE_CLOUD_PROJECT": PROJECT_ID,
    "GOOGLE_CLOUD_LOCATION": REGION,
    "FIREBASE_PROJECT_ID": PROJECT_ID,
    "FIREBASE_AUTH_EMULATOR_HOST": "",  # Disable emulator in staging
    "ENV": "staging",
    "LOG_LEVEL": "DEBUG",
    "FIREBASE_DATABASE_URL": "https://taajirah-default-rtdb.europe-west1.firebasedatabase.app",
}

def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)

def main():
    """Main deployment function"""
    print("🚀 Deploying enhanced workflow to staging...")
    
    # 1. Build environment variables string
    env_vars = ",".join([f"{k}={v}" for k, v in ENV_VARS.items()])

    # 2. Deploy to Cloud Run
    deploy_cmd = [
        "gcloud", "run", "deploy", SERVICE_NAME,
        "--source", ".",
        "--region", REGION,
        "--platform", "managed",
        "--allow-unauthenticated",  # Required for Firebase Auth
        "--memory", "2Gi",
        "--cpu", "2",
        "--min-instances", "0",
        "--max-instances", "2",
        "--set-env-vars", env_vars,
        "--project", PROJECT_ID,
        "--quiet"  # Skip confirmations
    ]

    try:
        run_command(deploy_cmd)
        print("\n✅ Staging deployment successful!")
        
        # Get service URL
        url_cmd = [
            "gcloud", "run", "services", "describe", SERVICE_NAME,
            "--platform", "managed",
            "--region", REGION,
            "--format", "value(status.url)"
        ]
        result = subprocess.run(url_cmd, capture_output=True, text=True, check=True)
        service_url = result.stdout.strip()
        
        print("\n🧪 Test the enhanced workflow:")
        print(f"1. Guide Agent Analysis:   curl -X POST {service_url}/analyze -H 'Authorization: Bearer $FIREBASE_TOKEN'")
        print(f"2. Search Agent Research:  curl -X POST {service_url}/research -H 'Authorization: Bearer $FIREBASE_TOKEN'")
        print(f"3. Prompt Writer:         curl -X POST {service_url}/compose -H 'Authorization: Bearer $FIREBASE_TOKEN'")
        print(f"4. Video Generator:       curl -X POST {service_url}/generate -H 'Authorization: Bearer $FIREBASE_TOKEN'")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 