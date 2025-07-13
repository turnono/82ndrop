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

# Configure logging
logging.basicConfig(level=logging.INFO)

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

# Video generation endpoints
@app.post("/generate-video")
async def generate_video(request: Request):
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get request body
        body = await request.json()
        prompt = body.get("prompt")
        user_id = body.get("user_id")
        session_id = body.get("session_id")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Get access token using gcloud
        import subprocess
        access_token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()

        # Generate video using Veo 3.0
        request_body = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "storageUri": f"gs://{get_video_bucket()}/users/{user_id}/sessions/{session_id}/",
                "durationSeconds": 8,
                "aspectRatio": "16:9",
                "sampleCount": 1
            }
        }

        # Get the model endpoint
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/veo-3.0-generate-preview:predictLongRunning"

        # Make the API request
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=request_body
        )

        if not response.ok:
            logging.error(f"Error from Vertex AI: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        operation = response.json()
        operation_name = operation.get("name", "")

        # Return operation name for status checking
        return {
            "operation_id": operation_name,
            "status": "processing"
        }

    except Exception as e:
        logging.error(f"Error generating video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_video_bucket():
    """Get the appropriate GCS bucket based on environment."""
    env = os.getenv('ENV', 'staging')  # Default to staging for safety
    if env == 'production':
        return "82ndrop-videos-taajirah"
    return "82ndrop-videos-staging-taajirah"

@app.get("/video-status/{operation_name:path}")
async def check_video_status(operation_name: str, request: Request):
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Extract operation ID from the full name if provided
        operation_id = operation_name.split('/')[-1] if '/' in operation_name else operation_name
        
        # Construct full operation name if only ID is provided
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        full_operation_name = operation_name if '/' in operation_name else f"projects/{project_id}/locations/us-central1/publishers/google/models/veo-3.0-generate-preview/operations/{operation_id}"

        # Get access token using gcloud
        import subprocess
        access_token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()

        # Make the API request to check operation status using fetchPredictOperation
        endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/veo-3.0-generate-preview:fetchPredictOperation"

        # Make the API request
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "operationName": full_operation_name
            }
        )

        if not response.ok:
            logging.error(f"Error from Vertex AI: {response.text}")
            if response.status_code == 404:
                # If operation not found in Vertex AI, check GCS directly
                try:
                    # Initialize storage client
                    from google.cloud import storage
                    storage_client = storage.Client()
                    bucket_name = get_video_bucket()
                    bucket = storage_client.bucket(bucket_name)
                    
                    # Check test directory first
                    blob = bucket.blob(f"test/{operation_id}/sample_0.mp4")
                    if blob.exists():
                        video_uri = f"gs://{bucket_name}/test/{operation_id}/sample_0.mp4"
                        logging.info(f"Found video in GCS test directory: {video_uri}")
                        return {
                            "status": "completed",
                            "video_uri": video_uri
                        }
                    
                    # Check lake_scene directory
                    blob = bucket.blob(f"lake_scene/{operation_id}/sample_0.mp4")
                    if blob.exists():
                        video_uri = f"gs://{bucket_name}/lake_scene/{operation_id}/sample_0.mp4"
                        logging.info(f"Found video in GCS lake_scene directory: {video_uri}")
                        return {
                            "status": "completed",
                            "video_uri": video_uri
                        }
                        
                    logging.info(f"Video not found in GCS for operation {operation_id}")
                except Exception as e:
                    logging.error(f"Error checking GCS: {str(e)}")
                
                return {
                    "status": "not_found",
                    "error": "Operation not found or expired"
                }
            raise HTTPException(status_code=response.status_code, detail=response.text)

        operation = response.json()
        logging.info(f"Operation response: {operation}")

        # Check if operation is done
        if operation.get("done"):
            if "error" in operation:
                return {
                    "status": "error",
                    "error": operation["error"].get("message", "Unknown error")
                }
            
            if "response" in operation:
                prediction = operation.get("response", {})
                logging.info(f"Prediction response: {prediction}")
                
                if "videos" in prediction:
                    videos = prediction["videos"]
                    if videos:
                        video_uri = videos[0].get("gcsUri")
                        logging.info(f"Found video URI in response: {video_uri}")
                        return {
                            "status": "completed",
                            "video_uri": video_uri
                        }
            
            return {
                "status": "error",
                "error": "No video found in response"
            }

        # Operation is still in progress
        metadata = operation.get("metadata", {})
        logging.info(f"Operation in progress. Metadata: {metadata}")
        return {
            "status": "processing",
            "metadata": metadata
        }

    except Exception as e:
        logging.error(f"Error checking video status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cancel-video/{operation_name}")
async def cancel_video_generation(operation_name: str, request: Request):
    try:
        # Get user from request state
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get access token using gcloud
        import subprocess
        access_token = subprocess.check_output(["gcloud", "auth", "print-access-token"]).decode().strip()

        # Make the API request to cancel operation
        endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/{operation_name}:cancel"

        # Make the API request
        response = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )

        if not response.ok:
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Operation not found")
            logging.error(f"Error from Vertex AI: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return {
            "status": "cancelled",
            "message": "Video generation cancelled successfully"
        }

    except Exception as e:
        logging.error(f"Error in cancel_video_generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 