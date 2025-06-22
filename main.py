import os
import firebase_admin
from firebase_admin import credentials, auth
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        # Try to initialize with service account key if available
        try:
            cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized with service account key")
            else:
                # Use default credentials (for Cloud Run)
                cred = credentials.ApplicationDefault()
                firebase_admin.initialize_app(cred)
                print("Firebase initialized with application default credentials")
        except Exception as e:
            print(f"Warning: Failed to initialize Firebase Admin SDK: {e}")
            print("Authentication will be disabled")
            return False
    return True

# Verify Firebase ID token
def verify_firebase_token(token: str):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

# Initialize Firebase
firebase_initialized = initialize_firebase()

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Example session DB URL (e.g., SQLite)
SESSION_DB_URL = "sqlite:///./sessions.db"
# CORS allowed origins - including frontend domains
ALLOWED_ORIGINS = [
    "http://localhost:4200",  # Angular dev server
    "https://82ndrop.web.app",       # Production frontend
]
# Set web=False to use our custom Firebase authentication instead of ADK's auth
SERVE_WEB_INTERFACE = False

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('drop_agent') matches your agent folder
app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Add Firebase authentication middleware
@app.middleware("http")
async def firebase_auth_middleware(request: Request, call_next):
    # Allow CORS preflight requests to pass through
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip authentication for health checks and static files
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"] or request.url.path.startswith("/static"):
        return await call_next(request)
    
    # Skip authentication if Firebase is not initialized (for local dev)
    if not firebase_initialized:
        print("Warning: Firebase not initialized, skipping authentication")
        return await call_next(request)
    
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={"detail": "Authorization header required"}
        )
    
    # Extract token from Bearer header
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid authorization header format"}
        )
    
    token = auth_header.split(" ")[1]
    
    # Verify Firebase token
    try:
        decoded_token = verify_firebase_token(token)
        # Add user info to request state for use in endpoints
        request.state.user = decoded_token
        request.state.user_id = decoded_token.get('uid')
        request.state.user_email = decoded_token.get('email')
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    except Exception as e:
        print(f"Unexpected error during token verification: {e}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication failed"}
        )
    
    return await call_next(request)

# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "firebase_initialized": firebase_initialized,
        "service": "82ndrop-agent"
    }

# User profile endpoint
@app.get("/user/profile")
async def get_user_profile(request: Request):
    # Get user info from middleware
    user_token = getattr(request.state, 'user', None)
    if not user_token:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Extract user information and custom claims
    uid = user_token.get('uid')
    email = user_token.get('email')
    name = user_token.get('name', user_token.get('display_name'))
    
    # Get custom claims
    agent_access = user_token.get('agent_access', False)
    access_level = user_token.get('access_level', 'none')
    agent_permissions = user_token.get('agent_permissions', {})
    
    return {
        "uid": uid,
        "email": email,
        "display_name": name,
        "agent_access": agent_access,
        "access_level": access_level,
        "permissions": agent_permissions
    }

# You can add more FastAPI routes or configurations below if needed
# Example:
# @app.get("/hello")
# async def read_root():
#     return {"Hello": "World"}

if __name__ == "__main__":
    # Use port 8000 to avoid conflict with Jenkins on 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) 