"""
FastAPI Middleware for automatic logging and analytics tracking
"""

import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

try:
    from .logging_config import api_logger, analytics_tracker, UserAnalytics
except ImportError:
    from logging_config import api_logger, analytics_tracker, UserAnalytics


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and track analytics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Extract request info
        method = request.method
        url = str(request.url)
        path = request.url.path
        user_agent = request.headers.get("user-agent", "")
        ip_address = self._get_client_ip(request)
        
        # Initialize user info (will be populated if authenticated)
        user_id = None
        email = None
        access_level = "anonymous"
        
        try:
            # Process the request
            response = await call_next(request)
            status_code = response.status_code
            error_message = None
            
        except Exception as e:
            # Handle exceptions
            status_code = 500
            error_message = str(e)
            
            # Log the error
            api_logger.log_error(e, user_id, {
                "endpoint": path,
                "method": method,
                "ip_address": ip_address,
                "user_agent": user_agent
            })
            
            # Return error response
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Extract user info from request state (set by auth middleware)
        if hasattr(request.state, "current_user"):
            user = request.state.current_user
            user_id = user.uid
            email = user.email
            access_level = user.access_level
            
            # Log successful authentication
            if path not in ["/health", "/", "/docs", "/openapi.json"]:
                api_logger.log_authentication(user_id, email or "", True)
        
        # Create analytics record
        analytics = UserAnalytics(
            user_id=user_id or "anonymous",
            email=email,
            access_level=access_level,
            endpoint=path,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        # Log the request
        api_logger.log_api_request(analytics)
        
        # Track analytics (only for authenticated users)
        if user_id and user_id != "anonymous":
            analytics_tracker.track_usage(analytics)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (if behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"


class ChatLoggingMiddleware:
    """Specialized middleware for chat endpoint logging"""
    
    @staticmethod
    async def log_chat_interaction(request: Request, response_data: dict, user_analytics: UserAnalytics):
        """Log detailed chat interactions"""
        
        # Extract message from request body
        try:
            body = await request.body()
            import json
            request_data = json.loads(body)
            message = request_data.get("message", "")
        except:
            message = ""
        
        # Extract response from response data
        agent_response = response_data.get("response", "")
        
        # Log the chat interaction
        api_logger.log_chat_interaction(user_analytics, message, agent_response)
        
        # Update analytics with message details
        user_analytics.message_length = len(message)
        user_analytics.agent_response_length = len(agent_response)
        user_analytics.session_id = response_data.get("session_id")
        
        # Track in analytics
        analytics_tracker.track_usage(user_analytics)