import os
import logging
from logging_config import APILogger
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Request, HTTPException, FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
import vertexai
from vertexai.generative_models import GenerativeModel
import json
import google.generativeai as genai
import requests
from google import genai
from google.genai.types import GenerateVideosConfig
import time
import asyncio
import random
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up environment variables for google.genai
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if cred_path and os.path.exists(cred_path):
                print(f"Loading service account from: {cred_path}")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized with service account")
            else:
                firebase_admin.initialize_app()
                print("Firebase initialized with application default credentials")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            firebase_admin.initialize_app()
            print("Firebase initialized without credentials")

# Initialize Firebase
initialize_firebase()

# Initialize Vertex AI
vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
)

# Firebase authentication middleware
class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for health check and OPTIONS requests
        if request.url.path == "/health" or request.method == "OPTIONS":
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
        try:
            token = auth_header.split("Bearer ")[1]
            decoded_token = auth.verify_id_token(token)
            if not decoded_token.get('agent_access'):
                return JSONResponse(status_code=403, content={"detail": "User does not have agent access"})
            request.state.user = decoded_token
        except Exception as e:
            print(f"Firebase token verification failed: {e}")
            return JSONResponse(status_code=401, content={"detail": "Invalid authentication token"})
        return await call_next(request)

# Set web=False for API-only usage
SERVE_WEB_INTERFACE = False

# Define proper CORS origins
ALLOWED_ORIGINS = [
    "https://82ndrop.web.app",
    "https://82ndrop-staging.web.app",  # Staging frontend URL
    "http://localhost:4200",
    "http://localhost:8080",
    "http://localhost"
]

# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
    agents_dir="drop_agent",
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Add Firebase authentication middleware
app.add_middleware(FirebaseAuthMiddleware)

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Mock mode configuration
MOCK_MODE = True  # Set to False to use real video generation

# Mock video pool - only used when MOCK_MODE is True
MOCK_VIDEOS_POOL = [
    {
        "video_uri": "gs://82ndrop-videos-staging-taajirah/users/iVZ4Pu9YzXTGOo2dXRLmJhbgEnl1/sessions/fe19d3f1-b4ca-4b14-a756-9d8c48c65505/videos/11698914790024900414/sample_0.mp4",
        "operation_name": "projects/taajirah/locations/global/publishers/google/models/veo-3.0-generate-preview/operations/b3343691-c843-4f93-83a8-b70e27a76874"
    },
    {
        "video_uri": "gs://82ndrop-videos-staging-taajirah/users/iVZ4Pu9YzXTGOo2dXRLmJhbgEnl1/sessions/f5266bbe-ac19-4695-a675-6ff16457c2e1/videos/1848635107879644044/sample_0.mp4",
        "operation_name": "projects/taajirah/locations/global/publishers/google/models/veo-3.0-generate-preview/operations/c4454792-d954-5fa4-94b9-c81e38b87985"
    },
    {
        "video_uri": "gs://82ndrop-videos-staging-taajirah/users/iVZ4Pu9YzXTGOo2dXRLmJhbgEnl1/sessions/ef64de1c-ba1e-4593-9107-9d4fbeaef6ac/videos/14801039161406831426/sample_0.mp4",
        "operation_name": "projects/taajirah/locations/global/publishers/google/models/veo-3.0-generate-preview/operations/d5565893-ea65-6fb5-a5ca-d92f49c98a96"
    },
    {
        "video_uri": "gs://82ndrop-videos-staging-taajirah/users/iVZ4Pu9YzXTGOo2dXRLmJhbgEnl1/sessions/e887b7bc-7c75-46ab-adbe-1552f100fd3d/videos/13981806491487398775/sample_0.mp4",
        "operation_name": "projects/taajirah/locations/global/publishers/google/models/veo-3.0-generate-preview/operations/e6676994-fb76-7gc6-b6db-ea3g5ad99ba7"
    }
]

# Store mock operations
mock_operations: Dict[str, Dict] = {}

async def simulate_video_generation(operation_name: str, user_id: str, session_id: str) -> None:
    """Simulate async video generation process."""
    # Simulate processing time (5-10 seconds)
    await asyncio.sleep(random.uniform(5, 10))
    
    # Pick a random video from our pool
    video = random.choice(MOCK_VIDEOS_POOL)
    
    # Update operation status to complete
    mock_operations[operation_name] = {
        "status": "completed",
        "video_uri": video["video_uri"],
        "operation_name": operation_name,
        "user_id": user_id,
        "session_id": session_id,
        "created_at": datetime.now().isoformat()
    }

@app.post("/generate-video")
async def generate_video(request: Request):
    """Video generation endpoint."""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        
        if not user_id or not session_id:
            raise HTTPException(status_code=400, detail="Missing user_id or session_id")

        if MOCK_MODE:
            # Mock video generation
            operation_name = f"projects/taajirah/locations/global/publishers/google/models/veo-3.0-generate-preview/operations/{random.randbytes(16).hex()}"
            
            # Initialize operation status
            mock_operations[operation_name] = {
                "status": "processing",
                "operation_name": operation_name,
                "user_id": user_id,
                "session_id": session_id,
                "created_at": datetime.now().isoformat()
            }
            
            # Start async video generation simulation
            asyncio.create_task(simulate_video_generation(operation_name, user_id, session_id))
            
            return {
                "status": "processing",
                "operation_name": operation_name
            }
        else:
            # Original video generation code
            # Get user from request state
            user = request.state.user
            if not user:
                raise HTTPException(status_code=401, detail="User not authenticated")

            # Get request body
            body = await request.json()
            prompt = body.get("prompt")
            user_id = body.get("user_id", user.get('user_id'))  # Default to authenticated user's ID
            session_id = body.get("session_id")

            if not prompt:
                raise HTTPException(status_code=400, detail="Prompt is required")
            if not session_id:
                raise HTTPException(status_code=400, detail="session_id is required")

            # Initialize Google GenAI client
            client = genai.Client()

            # Set up GCS output path
            bucket = get_video_bucket()
            output_gcs_uri = f"gs://{bucket}/users/{user_id}/sessions/{session_id}/videos/"

            # Log the request details
            logger.info(f"Starting video generation for user {user_id}, session {session_id}")
            logger.info(f"Output GCS URI: {output_gcs_uri}")

            try:
                # Generate video
                operation = client.models.generate_videos(
                    model="veo-3.0-generate-preview",
                    prompt=prompt,
                    config=genai.types.GenerateVideosConfig(
                        aspect_ratio="16:9",  # Vertical video for TikTok
                        output_gcs_uri=output_gcs_uri,
                    ),
                )

                # Store operation in memory for status checks
                operation_id = operation.name
                operations[operation_id] = {
                    'operation': operation,  # Store the actual operation object
                    'user_id': user_id,
                    'session_id': session_id,
                    'created_at': datetime.now().isoformat(),
                    'status': 'in_progress'
                }

                # Log operation details
                logger.info(f"Started video generation operation: {operation_id}")

                return {
                    "operation_name": operation_id,
                    "status": "in_progress",
                    "user_id": user_id,
                    "session_id": session_id,
                    "created_at": operations[operation_id]['created_at']
                }

            except Exception as e:
                logger.error(f"Error in GenAI client operation: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Dictionary to store operations with additional metadata
operations = {}

def get_video_bucket():
    """Get the appropriate GCS bucket based on environment."""
    env = os.getenv('ENV', 'staging')  # Default to staging for safety
    if env == 'production':
        return "82ndrop-videos-taajirah"
    return "82ndrop-videos-staging-taajirah"

@app.get("/video-status/{operation_name:path}")
async def check_video_status(operation_name: str, request: Request):
    """Check status of video generation."""
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        if MOCK_MODE:
            if operation_name not in mock_operations:
                raise HTTPException(status_code=404, detail="Operation not found")
            return mock_operations[operation_name]
        else:
            # Original video status check code
            # Get operation data from memory
            operation_data = operations.get(operation_name)
            if not operation_data:
                raise HTTPException(status_code=404, detail="Operation not found")

            # Get the operation object
            operation = operation_data['operation']
            
            try:
                # Initialize Google GenAI client
                client = genai.Client()
                
                # Update operation status
                if not operation.done:
                    # Use asyncio.sleep instead of time.sleep
                    await asyncio.sleep(15)
                    operation = client.operations.get(operation)
                    operation_data['operation'] = operation  # Update stored operation
                
                # Check if operation is done
                if operation.done:
                    try:
                        if operation.error:
                            # Operation failed
                            error_msg = str(operation.error)
                            operations.pop(operation_name, None)  # Clean up
                            return {
                                "status": "failed",
                                "error": error_msg,
                                "operation_name": operation_name,
                                "user_id": operation_data['user_id'],
                                "session_id": operation_data['session_id'],
                                "created_at": operation_data['created_at']
                            }
                        
                        # Operation succeeded
                        if operation.response and operation.result.generated_videos:
                            video_uri = operation.result.generated_videos[0].video.uri
                            operations.pop(operation_name, None)  # Clean up
                            return {
                                "status": "completed",
                                "video_uri": video_uri,
                                "operation_name": operation_name,
                                "user_id": operation_data['user_id'],
                                "session_id": operation_data['session_id'],
                                "created_at": operation_data['created_at']
                            }
                        else:
                            raise ValueError("No video generated in the result")
                    except Exception as e:
                        logger.error(f"Error processing completed operation: {str(e)}")
                        operations.pop(operation_name, None)  # Clean up
                        return {
                            "status": "error",
                            "error": f"Failed to process completed operation: {str(e)}",
                            "operation_name": operation_name,
                            "user_id": operation_data['user_id'],
                            "session_id": operation_data['session_id'],
                            "created_at": operation_data['created_at']
                        }
                else:
                    # Operation still in progress
                    return {
                        "status": "in_progress",
                        "operation_name": operation_name,
                        "user_id": operation_data['user_id'],
                        "session_id": operation_data['session_id'],
                        "created_at": operation_data['created_at']
                    }

            except Exception as e:
                logger.error(f"Error getting operation status: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Failed to get operation status: {str(e)}",
                    "operation_name": operation_name,
                    "user_id": operation_data['user_id'],
                    "session_id": operation_data['session_id'],
                    "created_at": operation_data['created_at']
                }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error checking video status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/cancel-video/{operation_name}")
async def cancel_video_generation(operation_name: str, request: Request):
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        if MOCK_MODE:
            if operation_name not in mock_operations:
                raise HTTPException(status_code=404, detail="Operation not found")
            
            operation_data = mock_operations[operation_name]
            mock_operations.pop(operation_name)
            
            return {
                "status": "cancelled",
                "operation_name": operation_name,
                "user_id": operation_data['user_id'],
                "session_id": operation_data['session_id'],
                "created_at": operation_data['created_at'],
                "message": "Video generation cancelled successfully"
            }
        else:
            # Original cancel code
            # Get operation data from memory
            operation_data = operations.get(operation_name)
            if not operation_data:
                raise HTTPException(status_code=404, detail="Operation not found")

            # Initialize Google GenAI client
            client = genai.Client()
            
            try:
                # Get latest operation status
                operation = client.operations.get(name=operation_name)
                
                # Try to cancel the operation
                operation.cancel()
                
                # Clean up operation from memory
                operations.pop(operation_name, None)
                
                return {
                    "status": "cancelled",
                    "operation_name": operation_name,
                    "user_id": operation_data['user_id'],
                    "session_id": operation_data['session_id'],
                    "created_at": operation_data['created_at'],
                    "message": "Video generation cancelled successfully"
                }
                
            except Exception as e:
                logger.error(f"Error cancelling operation: {str(e)}")
                # Clean up operation from memory even if cancel fails
                operations.pop(operation_name, None)
                return {
                    "status": "error",
                    "error": f"Failed to cancel operation: {str(e)}",
                    "operation_name": operation_name,
                    "user_id": operation_data['user_id'],
                    "session_id": operation_data['session_id'],
                    "created_at": operation_data['created_at']
                }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in cancel request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 