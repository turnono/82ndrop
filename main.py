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
from google.generativeai.types import GenerateVideosConfig

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

# Video generation endpoints
@app.post("/generate-video")
async def generate_video(request: Request):
    try:
        # Get user from request state (set by FirebaseAuthMiddleware)
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Check if user is authorized for video generation
        if user.get('email') != 'turnono@gmail.com':
            raise HTTPException(
                status_code=403, 
                detail="Video generation is restricted to authorized users only"
            )

        # Get request body
        body = await request.json()
        prompt = body.get("prompt")
        user_id = body.get("user_id")
        session_id = body.get("session_id")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Initialize Google GenAI client
        genai.configure(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        client = genai.Client()

        # Generate video
        operation = client.models.generate_videos(
            model="veo-3.0-generate-preview",
            prompt=prompt,
            config=GenerateVideosConfig(
                output_gcs_uri=f"gs://{os.getenv('VIDEO_BUCKET')}/{user_id}/{session_id}/",
                person_generation="allow_adult"  # Default setting
            ),
        )

        # Return operation ID for status checking
        return {
            "operation_id": operation.name,
            "status": "processing"
        }

    except Exception as e:
        logging.error(f"Error in video generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video-status/{operation_id}")
async def check_video_status(operation_id: str, request: Request):
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Initialize Google GenAI client
        genai.configure(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
        client = genai.Client()

        # Get operation status
        operation = client.operations.get(operation_id)

        if operation.done:
            if operation.error:
                return {
                    "status": "error",
                    "error": operation.error.message
                }
            else:
                video_uri = operation.result.generated_videos[0].video.uri
                return {
                    "status": "completed",
                    "video_url": video_uri
                }
        else:
            return {
                "status": "processing",
                "operation_id": operation_id
            }

    except Exception as e:
        logging.error(f"Error checking video status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cancel-video/{job_id}")
async def cancel_video_generation(job_id: str, request: Request):
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Initialize Vertex AI
        vertexai.init(
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        )

        # Get the Veo3 model
        model = GenerativeModel("veo-3")

        # Get and cancel the operation
        try:
            operation = model.get_operation(job_id)
            if not operation:
                raise ValueError("Operation not found")
            
            if operation.done:
                logging.warning(f"Operation {job_id} is already completed, cannot cancel")
                return {
                    "status": "completed",
                    "message": "Operation already completed"
                }
            
            operation.cancel()
            logging.info(f"Video generation cancelled: {job_id}")
            return {
                "status": "cancelled",
                "message": "Video generation cancelled successfully"
            }
        except ValueError as ve:
            logging.error(f"Error finding operation: {str(ve)}")
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            logging.error(f"Error cancelling operation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to cancel operation: {str(e)}")

    except Exception as e:
        logging.error(f"Error in cancel_video_generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 