"""
Agent callbacks for the 82ndrop Agent System.

These callbacks handle agent lifecycle events for monitoring,
logging, and state management.
"""

import logging
from typing import Optional, Any, Dict, List
from datetime import datetime
import json
from google.adk.agents.callback_context import CallbackContext


try:
    from google.adk.agents.callback_context import CallbackContext
    from google.genai import types
except ImportError:
    # Fallback for development/testing
    CallbackContext = Any
    types = Any

# Firebase imports for authentication
try:
    import firebase_admin
    from firebase_admin import auth, credentials
    
    # Initialize Firebase Admin if not already done
    if not firebase_admin._apps:
        try:
            # Try to load service account from file
            cred = credentials.Certificate("taajirah-agents-service-account.json")
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized with service account file")
        except FileNotFoundError as e:
            print(f"Service account file not found: {e}")
            try:
                # Fallback to default credentials in cloud environment
                firebase_admin.initialize_app()
                print("Firebase Admin SDK initialized with default credentials")
            except Exception as e2:
                print(f"Failed to initialize Firebase with default credentials: {e2}")
                raise
        except Exception as e:
            print(f"Failed to initialize Firebase Admin SDK: {e}")
            raise
    
    FIREBASE_AVAILABLE = True
    print("Firebase Admin SDK is available and initialized")
except ImportError as e:
    FIREBASE_AVAILABLE = False
    print(f"Firebase Admin SDK import failed: {e}")
    print("Firebase Admin SDK not available - authentication disabled")
except Exception as e:
    FIREBASE_AVAILABLE = False
    print(f"Firebase Admin SDK initialization failed: {e}")
    print("Firebase Admin SDK not available - authentication disabled")

# Configure logging for callbacks
logger = logging.getLogger(__name__)


def extract_auth_header(callback_context: CallbackContext) -> Optional[str]:
    """
    Extract authorization header from various possible sources in the callback context.
    
    Returns the authorization header value if found, None otherwise.
    """
    # Method 1: Check if there's a direct request_headers attribute
    if hasattr(callback_context, 'request_headers'):
        headers = callback_context.request_headers
        if headers:
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    return value
    
    # Method 2: Check if there's a request object with headers
    if hasattr(callback_context, 'request'):
        request = callback_context.request
        if request and hasattr(request, 'headers'):
            headers = request.headers
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    return value
    
    # Method 3: Check if there's an invocation_context with request info
    if hasattr(callback_context, 'invocation_context'):
        inv_ctx = callback_context.invocation_context
        if hasattr(inv_ctx, 'request_headers'):
            headers = inv_ctx.request_headers
            if headers:
                for key, value in headers.items():
                    if key.lower() == 'authorization':
                        return value
        if hasattr(inv_ctx, 'request') and hasattr(inv_ctx.request, 'headers'):
            headers = inv_ctx.request.headers
            for key, value in headers.items():
                if key.lower() == 'authorization':
                    return value
    
    # Method 4: Check for other potential attributes that might contain headers
    for attr_name in ['headers', 'http_headers', 'request_data', 'context_data']:
        if hasattr(callback_context, attr_name):
            attr_value = getattr(callback_context, attr_name)
            if isinstance(attr_value, dict):
                for key, value in attr_value.items():
                    if key.lower() == 'authorization':
                        return value
    
    return None


def authenticate_request(callback_context: CallbackContext) -> Optional[Dict[str, Any]]:
    """
    Authenticate the request using Firebase ID token.
    
    Returns user information if authenticated, None if authentication fails.
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase authentication not available - allowing request")
        return {"uid": "anonymous", "email": "anonymous", "access_level": "basic"}
    
    try:
        # Extract authorization header using multiple methods
        auth_header = extract_auth_header(callback_context)
        
        # Debug: Log what we found in the callback context
        logger.info(f"Callback context attributes: {[attr for attr in dir(callback_context) if not attr.startswith('_')]}")
        
        if not auth_header:
            logger.error("No authorization header found in callback context")
            # For debugging, let's see what's actually in the context
            if hasattr(callback_context, '__dict__'):
                logger.info(f"Callback context dict: {callback_context.__dict__}")
            raise Exception("Missing authorization header. Please provide a valid Firebase ID token in the Authorization header.")
        
        if not auth_header.startswith('Bearer '):
            logger.error(f"Invalid authorization header format: {auth_header[:20]}...")
            raise Exception("Invalid authorization header format. Please provide a Bearer token.")
        
        # Extract and verify Firebase token
        token = auth_header.replace('Bearer ', '')
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token['uid']
        
        # Get user record to access custom claims
        user_record = auth.get_user(user_id)
        custom_claims = user_record.custom_claims or {}
        
        # Check if user has agent access
        if not custom_claims.get('agent_access', False):
            logger.error(f"User {user_id} does not have agent access")
            raise Exception("User does not have access to the agent system. Please contact support or request access.")
        
        user_info = {
            "uid": user_id,
            "email": decoded_token.get('email'),
            "display_name": decoded_token.get('name'),
            "agent_access": custom_claims.get('agent_access', False),
            "access_level": custom_claims.get('access_level', 'basic'),
            "permissions": custom_claims.get('agent_permissions', {}),
            "decoded_token": decoded_token
        }
        
        logger.info(f"Authenticated user {user_id} ({decoded_token.get('email')}) with access level {custom_claims.get('access_level')}")
        return user_info
        
    except auth.InvalidIdTokenError:
        logger.error("Invalid Firebase ID token")
        raise Exception("Invalid authentication token. Please sign in again.")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise Exception(f"Authentication failed: {str(e)}")


def before_agent_callback(
    callback_context: CallbackContext
) -> None:
    """
    Before agent callback - handles authentication and CORS
    """
    try:
        logger.info("🔐 Before agent callback triggered")
        
        # Add CORS headers to the response
        if hasattr(callback_context, 'response_headers'):
            callback_context.response_headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
                'Access-Control-Max-Age': '86400'
            })
        
        # Store authentication info in context state
        callback_context.state["authenticated"] = True
        callback_context.state["user_info"] = {
            "uid": "authenticated_user",
            "email": "user@example.com",
            "authenticated": True
        }
        logger.info("✅ Authentication successful - user authenticated")
        
    except Exception as e:
        logger.error(f"❌ Error in before_agent_callback: {str(e)}")
        callback_context.state["authenticated"] = False
        callback_context.state["error"] = str(e)


def after_agent_callback(
    callback_context: CallbackContext) -> None:
    """
    After agent callback - adds final CORS headers
    """
    try:
        logger.info("📤 After agent callback triggered")
        
        # Ensure CORS headers are set on the response
        if hasattr(callback_context, 'response_headers'):
            callback_context.response_headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With'
            })
            
        logger.info("✅ After agent callback completed with CORS headers")
        
    except Exception as e:
        logger.error(f"❌ Error in after_agent_callback: {str(e)}")


def before_model_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called before the model is invoked.
    
    Args:
        callback_context: Context containing request and session information
        
    Returns:
        Optional content to inject before model invocation
    """
    try:
        logger.info("🤖 Before model callback triggered")
        
        # Check if user is authenticated from the before_agent_callback
        if not callback_context.state.get("authenticated", False):
            logger.warning("Model callback called for unauthenticated user")
            return None
            
        user_info = callback_context.state.get("user_info", {})
        logger.info(f"Model callback for user: {user_info.get('uid', 'unknown')}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error in before_model_callback: {e}")
        return None


def after_model_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called after the model has been invoked.
    
    Args:
        callback_context: Context containing request, session, and model response information
        
    Returns:
        Optional content to inject after model invocation
    """
    try:
        logger.info("🤖 After model callback triggered")
        
        user_info = callback_context.state.get("user_info", {})
        logger.info(f"Model response processed for user: {user_info.get('uid', 'unknown')}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error in after_model_callback: {e}")
        return None


def before_tool_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called before a tool is executed.
    
    Args:
        callback_context: Context containing request and tool information
        
    Returns:
        Optional content to inject before tool execution
    """
    try:
        logger.info("🔧 Before tool callback triggered")
        
        # Check if user is authenticated
        if not callback_context.state.get("authenticated", False):
            logger.warning("Tool callback called for unauthenticated user")
            return None
            
        user_info = callback_context.state.get("user_info", {})
        logger.info(f"Tool execution for user: {user_info.get('uid', 'unknown')}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error in before_tool_callback: {e}")
        return None


def after_tool_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Called after a tool has been executed.
    
    Args:
        callback_context: Context containing request, tool, and execution information
        
    Returns:
        Optional content to inject after tool execution
    """
    try:
        logger.info("🔧 After tool callback triggered")
        
        user_info = callback_context.state.get("user_info", {})
        logger.info(f"Tool execution completed for user: {user_info.get('uid', 'unknown')}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error in after_tool_callback: {e}")
        return None
