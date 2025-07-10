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
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Try to initialize with service account key if available
        try:
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if cred_path and os.path.exists(cred_path):
                print(f"Loading service account from: {cred_path}")
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized with service account")
            else:
                # Use application default credentials
                firebase_admin.initialize_app()
                print("Firebase initialized with application default credentials")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            # Initialize without credentials for development
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
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing or invalid Authorization header"})
        
        try:
            # Extract and verify the token
            token = auth_header.split("Bearer ")[1]
            decoded_token = auth.verify_id_token(token)
            
            # Check if user has agent access
            if not decoded_token.get('agent_access'):
                return JSONResponse(status_code=403, content={"detail": "User does not have agent access"})
            
            # Add user info to request state
            request.state.user = decoded_token
            
        except Exception as e:
            print(f"Firebase token verification failed: {e}")
            return JSONResponse(status_code=401, content={"detail": "Invalid authentication token"})
        
        return await call_next(request)

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]

# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('drop_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agents_dir="drop_agent",
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Firebase authentication middleware
app.add_middleware(FirebaseAuthMiddleware)

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080))) 