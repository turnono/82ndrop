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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080))) 