import os
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv

# Import logging and middleware
try:
    from .logging_config import api_logger, analytics_tracker, UserAnalytics
    from .middleware import LoggingMiddleware
except ImportError:
    from logging_config import api_logger, analytics_tracker, UserAnalytics
    from middleware import LoggingMiddleware

# Load environment
load_dotenv()

# Initialize Firebase Admin
if not firebase_admin._apps:
    # Use default credentials (service account key should be in environment)
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

# Import 82ndrop agent
from drop_agent.services import get_runner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="82ndrop Agent API",
    description="API for accessing the 82ndrop video prompt agent system",
    version="1.0.0"
)

# Add logging middleware first
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev server
        "https://82ndrop.web.app",  # Firebase hosting
        "https://82ndrop.firebaseapp.com",
        "https://www.82ndrop.web.app",
        "https://taajirah.web.app",
        "https://taajirah.firebaseapp.com",
        "https://www.taajirah.web.app",
        "https://www.taajirah.firebaseapp.com",
        "https://drop-agent-service-855515190257.us-central1.run.app"  # Backend service URL (for health checks)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: str
    timestamp: str

class UserInfo(BaseModel):
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    agent_access: bool
    access_level: str
    permissions: Dict[str, Any]

# Authentication dependency
async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInfo:
    """
    Verify Firebase ID token and extract user information
    """
    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(credentials.credentials)
        uid = decoded_token['uid']
        
        # Get user record to access custom claims
        user_record = auth.get_user(uid)
        custom_claims = user_record.custom_claims or {}
        
        # Check if user has agent access
        if not custom_claims.get('agent_access', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to the agent system"
            )
        
        user_info = UserInfo(
            uid=uid,
            email=decoded_token.get('email'),
            display_name=decoded_token.get('name'),
            agent_access=custom_claims.get('agent_access', False),
            access_level=custom_claims.get('access_level', 'basic'),
            permissions=custom_claims.get('agent_permissions', {})
        )
        
        # Store user info in request state for middleware access
        request.state.current_user = user_info
        
        return user_info
        
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Initialize agent runner
runner = get_runner()

# API Routes
@app.get("/")
async def root():
    return {"message": "82ndrop Agent API", "status": "active"}

@app.get("/user/profile")
async def get_user_profile(current_user: UserInfo = Depends(get_current_user)):
    """Get current user profile and permissions"""
    return current_user

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(
    request: Request,
    chat_message: ChatMessage,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Send a message to the 82ndrop agent system
    """
    start_time = time.time()
    
    try:
        user_id = current_user.uid
        session_id = chat_message.session_id
        
        # If no session_id provided, create a new session
        if not session_id:
            session = await runner.session_service.create_session(
                user_id=user_id, 
                app_name=runner.app_name
            )
            session_id = session.id
        
        # Run the agent
        final_response = None
        for response in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=chat_message.message,
        ):
            final_response = response
        
        if not final_response or not final_response.content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agent failed to generate a response"
            )
        
        # Create response
        chat_response = ChatResponse(
            response=final_response.content,
            session_id=session_id,
            user_id=user_id,
            timestamp=datetime.now().isoformat()
        )
        
        # Log detailed chat interaction
        response_time_ms = (time.time() - start_time) * 1000
        user_analytics = UserAnalytics(
            user_id=user_id,
            email=current_user.email,
            access_level=current_user.access_level,
            endpoint="/chat",
            method="POST",
            status_code=200,
            response_time_ms=response_time_ms,
            message_length=len(chat_message.message),
            agent_response_length=len(final_response.content),
            session_id=session_id
        )
        
        # Log the chat interaction
        api_logger.log_chat_interaction(user_analytics, chat_message.message, final_response.content)
        analytics_tracker.track_usage(user_analytics)
        
        return chat_response
        
    except Exception as e:
        # Log error with detailed context
        response_time_ms = (time.time() - start_time) * 1000
        api_logger.log_error(e, current_user.uid, {
            "endpoint": "/chat",
            "message_length": len(chat_message.message) if chat_message else 0,
            "session_id": chat_message.session_id if chat_message else None,
            "response_time_ms": response_time_ms
        })
        
        logger.error(f"Chat error for user {current_user.uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )

@app.get("/sessions")
async def get_user_sessions(current_user: UserInfo = Depends(get_current_user)):
    """Get user's chat sessions"""
    try:
        # This would depend on your session service implementation
        # For now, return a placeholder
        return {
            "user_id": current_user.uid,
            "sessions": [],
            "message": "Session history not implemented yet"
        }
    except Exception as e:
        logger.error(f"Error fetching sessions for user {current_user.uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch sessions"
        )

@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """Delete a user's chat session"""
    try:
        # Implement session deletion logic here
        return {
            "message": f"Session {session_id} deleted",
            "user_id": current_user.uid
        }
    except Exception as e:
        logger.error(f"Error deleting session {session_id} for user {current_user.uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_status": "ready"
    }

# Analytics endpoints
@app.get("/analytics/daily")
async def get_daily_analytics(
    date: Optional[str] = None,
    current_user: UserInfo = Depends(get_current_user)
):
    """Get daily analytics summary (admin only)"""
    
    # Check admin permissions
    if current_user.access_level != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    summary = analytics_tracker.get_daily_summary(date)
    return {"daily_analytics": summary}

@app.get("/analytics/user/{user_id}")
async def get_user_analytics(
    user_id: str,
    current_user: UserInfo = Depends(get_current_user)
):
    """Get user-specific analytics"""
    
    # Users can only view their own analytics, admins can view any
    if current_user.uid != user_id and current_user.access_level != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own analytics"
        )
    
    summary = analytics_tracker.get_user_summary(user_id)
    return {"user_analytics": summary}

@app.get("/analytics/export")
async def export_analytics(
    current_user: UserInfo = Depends(get_current_user)
):
    """Export all analytics data (admin only)"""
    
    # Check admin permissions
    if current_user.access_level != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    filename = analytics_tracker.export_analytics()
    return {"message": f"Analytics exported to {filename}", "filename": filename}

@app.get("/analytics/overview")
async def get_analytics_overview(
    current_user: UserInfo = Depends(get_current_user)
):
    """Get analytics overview for current user"""
    
    user_summary = analytics_tracker.get_user_summary(current_user.uid)
    
    # If admin, also include daily summary
    overview = {"user_stats": user_summary}
    
    if current_user.access_level == "admin":
        daily_summary = analytics_tracker.get_daily_summary()
        overview["daily_stats"] = daily_summary
    
    return {"analytics_overview": overview}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 