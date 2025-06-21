import os
import time
import uvicorn
from google.adk.cli.fast_api import get_fast_api_app
from fastapi import Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Initialize Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials

# Initialize Firebase (only if not already initialized)
if not firebase_admin._apps:
    # Use the service account key file
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', './taajirah-agents-service-account.json')
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        # For Cloud Run, use default credentials
        firebase_admin.initialize_app()

# Import our custom modules
try:
    from .logging_config import APILogger, AnalyticsTracker
    from .middleware import firebase_auth_dependency
except ImportError:
    from logging_config import APILogger, AnalyticsTracker
    from middleware import firebase_auth_dependency

# Get the directory where main.py is located
AGENT_DIR = "./drop_agent"  # In Docker container, drop_agent is copied to /app/drop_agent
# Session DB URL (using SQLite for now)
SESSION_DB_URL = "sqlite:///./sessions.db"
# CORS origins
ALLOWED_ORIGINS = [
    "https://82ndrop.web.app",
    "https://82ndrop.firebaseapp.com", 
    "http://localhost:4200",
    "http://localhost:8080",
    "*"
]

# Initialize our custom logging and analytics
api_logger = APILogger()
analytics_tracker = AnalyticsTracker()

# Create the ADK FastAPI app
app = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_DB_URL,
    allow_origins=ALLOWED_ORIGINS,
    web=True,  # Enables the built-in dev UI at /dev-ui/
)

# Add our custom analytics endpoints
@app.get("/analytics/overview")
async def get_analytics_overview(user_data=Depends(firebase_auth_dependency)):
    """Get analytics overview for authenticated user"""
    try:
        user_id = user_data["uid"]
        user_email = user_data.get("email", "unknown")
        
        # Get user-specific analytics
        stats = analytics_tracker.get_user_analytics(user_id)
        
        api_logger.log_api_usage(
            user_id=user_id,
            user_email=user_email,
            endpoint="/analytics/overview",
            method="GET",
            status_code=200,
            response_time=0.1
        )
        
        return {
            "user_id": user_id,
            "total_requests": stats.get("total_requests", 0),
            "success_rate": stats.get("success_rate", 0.0),
            "avg_response_time": stats.get("avg_response_time", 0.0),
            "last_active": stats.get("last_active"),
            "total_message_length": stats.get("total_message_length", 0)
        }
    except Exception as e:
        api_logger.log_error(f"Analytics overview error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/daily")
async def get_daily_analytics(user_data=Depends(firebase_auth_dependency)):
    """Get daily system analytics (admin only)"""
    access_level = user_data.get("access_level", "basic")
    
    if access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        daily_stats = analytics_tracker.get_daily_stats()
        
        api_logger.log_api_usage(
            user_id=user_data["uid"],
            user_email=user_data.get("email", "unknown"),
            endpoint="/analytics/daily",
            method="GET",
            status_code=200,
            response_time=0.1
        )
        
        return daily_stats
    except Exception as e:
        api_logger.log_error(f"Daily analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/analytics/user/{user_id}")
async def get_user_analytics(user_id: str, user_data=Depends(firebase_auth_dependency)):
    """Get analytics for specific user (admin only)"""
    access_level = user_data.get("access_level", "basic")
    
    if access_level != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        user_stats = analytics_tracker.get_user_analytics(user_id)
        
        api_logger.log_api_usage(
            user_id=user_data["uid"],
            user_email=user_data.get("email", "unknown"),
            endpoint=f"/analytics/user/{user_id}",
            method="GET",
            status_code=200,
            response_time=0.1
        )
        
        return user_stats
    except Exception as e:
        api_logger.log_error(f"User analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    try:
        return {"status": "healthy", "service": "82ndrop-api-adk", "timestamp": str(time.time())}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Add our logging middleware
try:
    from .middleware import LoggingMiddleware, ChatLoggingMiddleware
except ImportError:
    from middleware import LoggingMiddleware, ChatLoggingMiddleware

app.add_middleware(LoggingMiddleware, api_logger=api_logger, analytics_tracker=analytics_tracker)
app.add_middleware(ChatLoggingMiddleware, api_logger=api_logger, analytics_tracker=analytics_tracker)

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080))) 