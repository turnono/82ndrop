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
from vertexai.preview.generative_ai import GenerativeModel
import json

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

        # Get request body
        body = await request.json()
        prompt = body.get("prompt")
        api_key = body.get("api_key")
        user_id = body.get("user_id")
        session_id = body.get("session_id")

        if not all([prompt, api_key, user_id, session_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Initialize Vertex AI with proper credentials
        from google.oauth2 import service_account
        try:
            credentials = service_account.Credentials.from_service_account_info(
                api_key if isinstance(api_key, dict) else json.loads(api_key)
            )
            vertexai.init(
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
                credentials=credentials
            )
        except Exception as e:
            logging.error(f"Failed to initialize Vertex AI with credentials: {str(e)}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid service account credentials provided"
            )

        # Get environment and project settings
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        env = os.getenv("ENV", "development")
        
        if not project_id:
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_CLOUD_PROJECT environment variable is not set"
            )

        # Use the same bucket naming convention as deploy.yml
        video_bucket = f"82ndrop-videos{'-staging' if env != 'production' else ''}-{project_id}"
        output_gcs_uri = f"gs://{video_bucket}/users/{user_id}/sessions/{session_id}/"

        # Get the Veo3 model
        model = GenerativeModel("veo-3.0-generate-preview")

        # Start video generation
        operation = model.generate_video(
            prompt=prompt,
            aspect_ratio="9:16",
            duration=8,
            negative_prompt="blurry, low quality, distorted, unrealistic",
            output_gcs_uri=output_gcs_uri
        )

        # Log the operation details
        logging.info(f"Started video generation for user {user_id}, session {session_id}")
        logging.info(f"Operation name: {operation.name}")

        # Return operation ID for status checking
        return {
            "jobId": operation.name,
            "status": "processing",
            "message": "Video generation started successfully"
        }

    except Exception as e:
        logging.error(f"Error generating video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video-status/{job_id}")
async def check_video_status(job_id: str, request: Request):
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
        model = GenerativeModel("veo-3.0-generate-preview")

        # Get operation status
        operation = model.get_operation(job_id)

        if operation.done:
            if operation.error:
                logging.error(f"Video generation failed: {operation.error.message}")
                return {
                    "status": "error",
                    "error": operation.error.message
                }
            else:
                # Add defensive checks for operation result
                if not operation.result:
                    logging.error("Operation completed but result is missing")
                    return {
                        "status": "error",
                        "error": "Operation result is missing"
                    }
                
                if not hasattr(operation.result, 'generated_videos') or not operation.result.generated_videos:
                    logging.error("Operation completed but no videos were generated")
                    return {
                        "status": "error",
                        "error": "No videos were generated"
                    }
                
                # Get video URL from the response
                video_url = operation.result.generated_videos[0].video.uri
                logging.info(f"Video generation completed: {video_url}")
                return {
                    "status": "completed",
                    "videoUrl": video_url
                }
        else:
            # Still processing - add defensive check for metadata
            if not hasattr(operation, 'metadata'):
                logging.warning("Operation metadata is missing")
                progress = 0
            else:
                progress = operation.metadata.get("progress", 0)
            
            logging.info(f"Video generation in progress: {progress}%")
            return {
                "status": "processing",
                "progress": progress
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
        model = GenerativeModel("veo-3.0-generate-preview")

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