import os
import logging
from logging_config import APILogger, UserAnalytics
import firebase_admin
from firebase_admin import credentials, auth, db
from fastapi import FastAPI, Request, HTTPException, Depends, Security, Header
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from google.auth import jwt
from drop_agent.sub_agents.video_generator.agent import video_generator_agent
from drop_agent.custom_tools import (
    generate_video_complete, get_video_job_status, submit_veo_generation_job,
    check_user_access, submit_video_job, check_video_status, check_user_access_direct
)
from drop_agent.services import get_runner, get_or_create_session, queue_processor
from pydantic import BaseModel
import time
from staging_access_control import staging_access
import json
import asyncio
import requests
from typing import Optional
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import uuid
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

# Initialize logger
logger = APILogger()

# CORS allowed origins - including frontend domains
ALLOWED_ORIGINS = [
    "http://localhost:4200",  # Angular dev server
    "http://127.0.0.1:4200",  # Angular dev server alternative
    "https://82ndrop.web.app",       # Production frontend
    "https://82ndrop.firebaseapp.com",  # Firebase hosting alternative
    "https://localhost:4200",  # HTTPS dev server
]

# Firebase configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "taajirah")
DATABASE_URL = "https://taajirah-default-rtdb.europe-west1.firebasedatabase.app"

# Initialize Firebase Admin SDK
try:
    if not firebase_admin._apps:  # Only initialize if not already initialized
        cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path and os.path.exists(cred_path):
            print(f"✅ Found service account at {cred_path}")
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': DATABASE_URL,
                'projectId': PROJECT_ID,
                'databaseAuthVariableOverride': {
                    'uid': 'service-account',
                    'token': {
                        'email': 'taajirah-agents@taajirah.iam.gserviceaccount.com'
                    }
                }
            })
            print("✅ Firebase Admin SDK initialized with service account")
        else:
            print("⚠️  No service account found, using default credentials")
            firebase_admin.initialize_app(options={
                'databaseURL': DATABASE_URL,
                'projectId': PROJECT_ID
            })
            print("✅ Firebase Admin SDK initialized with default credentials")
except Exception as e:
    print(f"⚠️  Warning: Firebase initialization error: {e}")
    if "already exists" not in str(e):
        print(f"❌ CRITICAL: Failed to initialize Firebase Admin SDK: {e}")

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication middleware
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify Firebase ID token and return user info"""
    try:
        if not credentials:
            raise HTTPException(status_code=401, detail="No credentials provided")
            
        token = credentials.credentials
        
        # For testing purposes
        if os.getenv("ENVIRONMENT") == "staging" and token == "test-token":
            return {
                "uid": "test_user",  # Use correct test user ID
                "email": "test@example.com",
                "token": {
                    "email": "taajirah-agents@taajirah.iam.gserviceaccount.com",
                    "kid": "test-kid",  # Add kid claim for test token
                    "aud": "taajirah",
                    "iss": "https://securetoken.google.com/taajirah",
                    "sub": "test_user",  # Use correct test user ID
                    "exp": int(time.time()) + 3600,  # 1 hour from now
                    "iat": int(time.time())
                }
            }
            
        # Verify the Firebase token
        try:
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

async def auth_middleware(request, call_next):
    """Global authentication middleware"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="No authorization header")
            
        scheme, credentials = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
            
        token = credentials
        
        # For testing purposes
        if os.getenv("ENVIRONMENT") == "staging" and token == "test-token":
            request.state.user = {
                "uid": "test_user",  # Use correct test user ID
                "email": "test@example.com",
                "token": {
                    "email": "taajirah-agents@taajirah.iam.gserviceaccount.com"
                }
            }
            return await call_next(request)
            
        # Verify the token
        try:
            decoded_token = auth.verify_id_token(token)
            request.state.user = decoded_token
            return await call_next(request)
        except Exception as e:
            raise HTTPException(status_code=401, detail=str(e))
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

app.middleware("http")(auth_middleware)

class ChatRequest(BaseModel):
    message: str

class AgentRequest(BaseModel):
    appName: str
    userId: str
    sessionId: str | None
    newMessage: dict

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "environment": os.getenv("ENV", "unknown"),
        "timestamp": int(time.time())
    }

# Staging info endpoint
@app.get("/staging-info")
async def get_staging_info():
    """Get information about the staging environment"""
    try:
        info = staging_access.get_staging_info()
        info.update({
            "video_generation_costs": {
                "veo_3_video": "$0.50/second",
                "veo_3_video_audio": "$0.75/second", 
                "example_8_second_video": "$4.00",
                "example_8_second_with_audio": "$6.00"
            },
            "protection_reason": "Videos cost real money - staging environment is locked down",
            "current_environment": os.getenv("ENVIRONMENT", "unknown")
        })
        return info
    except Exception as e:
        return {"error": str(e), "environment": "unknown"}

# Video generation endpoints
@app.post("/generate-video")
async def generate_video(request: dict, current_user: dict = Depends(get_current_user)):
    """Generate a video using VEO3"""
    try:
        # Check user access
        user_id = current_user.get("uid", "test-user")
        if not check_user_access_direct(user_id):
            raise HTTPException(status_code=403, detail="User does not have access to video generation")
            
        # Extract parameters
        prompt = request.get("prompt")
        aspect_ratio = request.get("aspect_ratio", "16:9")  # Default to 16:9 for VEO3
        duration_seconds = request.get("duration_seconds", 8)
        sample_count = request.get("sample_count", 1)
        person_generation = request.get("person_generation", "allow_adult")
        generate_audio = request.get("generate_audio", True)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
            
        # Submit the job using direct function
        result = submit_video_job(
            prompt=prompt,
            user_id=user_id,  # Use the authenticated user ID
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            sample_count=sample_count,
            person_generation=person_generation,
            generate_audio=generate_audio
        )
        
        # Check for error message
        if result.startswith("Error:"):
            return {
                "status": "error",
                "message": result
            }
            
        # Extract job ID from result
        if "Job" in result:
            job_id = result.split("Job")[1].split("submitted")[0].strip()
            return {
                "status": "processing",
                "job_id": job_id,
                "message": "Video generation started"
            }
        else:
            return {
                "status": "error",
                "message": result
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video-status/{job_id}")
async def get_status(job_id: str, current_user: dict = Depends(get_current_user)):
    """Get the status of a video generation job"""
    try:
        # Check user access
        user_id = current_user.get("uid", "test-user")
        if not check_user_access_direct(user_id):
            raise HTTPException(status_code=403, detail="User does not have access to video generation")
            
        # Check status using direct function
        result = check_video_status(job_id)
        
        # Verify job ownership
        if result.get("data", {}).get("userId") != user_id:
            raise HTTPException(status_code=403, detail="You do not have access to this job")
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/check-vertex-operation")
async def check_vertex_operation(request: dict, current_user: dict = Depends(get_current_user)):
    """Check Vertex AI operation status directly"""
    try:
        operation_name = request.get("operationName")
        if not operation_name:
            raise HTTPException(status_code=400, detail="Operation name is required")
            
        # Get service account credentials
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise HTTPException(status_code=500, detail="Service account credentials not found")
            
        credentials = service_account.Credentials.from_service_account_file(
            cred_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        # Refresh token if needed
        if not credentials.valid:
            request = GoogleRequest()
            credentials.refresh(request)
            
        # Get operation status
        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"https://us-central1-aiplatform.googleapis.com/v1/{operation_name}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to check operation status: {response.text}"
            )
            
        return response.json()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run")
async def run_agent(request: AgentRequest):
    """Run the multi-agent workflow"""
    try:
        # Get or create session ID
        session_id = get_or_create_session(request.userId, request.sessionId)

        # Get the ADK runner
        runner = get_runner()

        # Create an async generator to stream responses
        async def stream_response():
            try:
                # Run the multi-agent workflow
                async for event in runner.run_async(
                    user_id=request.userId,
                    session_id=session_id,
                    new_message=request.newMessage
                ):
                    # Add timestamp and event type for better tracking
                    event_data = {
                        **event,
                        "timestamp": int(time.time()),
                        "type": event.get("type", "message"),
                        "session_id": session_id
                    }
                    
                    # Log the event for debugging
                    logger.log_api_request(UserAnalytics(
                        user_id=request.userId,
                        email=None,  # Email not needed for event logging
                        access_level="staging",
                        endpoint="/run",
                        method="POST",
                        status_code=200,
                        response_time_ms=0,
                        message_length=len(str(event_data))
                    ))
                    
                    # Convert event to JSON and yield
                    yield json.dumps(event_data) + "\n"
                    
            except Exception as e:
                error_data = {
                    "error": str(e),
                    "type": "error",
                    "timestamp": int(time.time()),
                    "session_id": session_id,
                    "code": "STREAM_ERROR"
                }
                
                logger.log_error(e, user_id=request.userId, context={
                    "endpoint": "/run",
                    "method": "POST",
                    "app_name": request.appName,
                    "error_type": "streaming",
                    "session_id": session_id
                })
                
                yield json.dumps(error_data) + "\n"

        # Return a streaming response with proper headers
        response = StreamingResponse(
            stream_response(),
            media_type="application/x-ndjson"
        )
        
        # Add headers for better client handling
        response.headers["X-Session-ID"] = session_id
        response.headers["X-User-ID"] = request.userId
        response.headers["Cache-Control"] = "no-cache"
        
        return response

    except Exception as e:
        error_context = {
            "endpoint": "/run",
            "method": "POST",
            "app_name": request.appName,
            "error_type": "initialization",
            "session_id": session_id if 'session_id' in locals() else None
        }
        
        logger.log_error(e, user_id=request.userId, context=error_context)
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "type": "initialization_error",
                "timestamp": int(time.time()),
                "code": "INIT_ERROR",
                **error_context
            }
        )

def main():
    # Start queue processor
    queue_processor.start()
    print("✅ Video job queue processor started")
    
    # Rest of main function...

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000))) 