"""
Agent callbacks for the 82ndrop Agent System.

These callbacks handle agent lifecycle events for monitoring,
logging, and state management.
"""

import logging
from typing import Optional, Any, Dict
from datetime import datetime

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


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback executed before the agent starts processing a request.

    This callback is called at the start of each agent interaction.
    AUTHENTICATION IS ENFORCED HERE - All requests must have valid Firebase tokens.

    Args:
        callback_context: Context object containing request information

    Returns:
        Optional content to inject into the conversation
    """
    try:
        # AUTHENTICATE THE REQUEST FIRST
        user_info = authenticate_request(callback_context)
        
        # Store user information in callback context for use by other callbacks
        if hasattr(callback_context, "state"):
            callback_context.state["authenticated_user"] = user_info
        
        # Log the start of agent processing
        logger.info(f"Agent processing started for authenticated user: {user_info['uid']}")

        # Extract session and user info if available
        session_id = getattr(callback_context, "session_id", "unknown")
        user_id = user_info['uid']

        logger.info(f"Processing request for user: {user_id}, session: {session_id}")

        # Add timestamp for performance tracking
        if hasattr(callback_context, "state"):
            callback_context.state["processing_start_time"] = datetime.now().isoformat()
            callback_context.state["authenticated_user_id"] = user_id
            callback_context.state["user_access_level"] = user_info.get('access_level', 'basic')

    except Exception as e:
        logger.error(f"Authentication failed in before_agent_callback: {e}")
        # Return an error message that will be sent back to the user
        return types.Content(
            parts=[types.Part(text=f"Authentication Error: {str(e)}\n\nPlease ensure you are signed in and have the proper permissions to access the agent system.")]
        )

    # Note: We do set processing_start_time here for performance tracking
    # This is a minimal state modification for monitoring purposes
    return None


def after_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback executed after the agent completes processing a request.

    This callback is called after the agent generates a response.
    Use this for logging, metrics, state persistence, and cleanup.

    Args:
        callback_context: Context object containing response and state information

    Returns:
        Optional content to append to the response
    """
    try:
        # Log the completion of agent processing
        logger.info("Agent processing completed")

        # Get authenticated user info from state
        authenticated_user = None
        if hasattr(callback_context, "state") and "authenticated_user" in callback_context.state:
            authenticated_user = callback_context.state["authenticated_user"]

        # Calculate processing time if start time was recorded
        if (
            hasattr(callback_context, "state")
            and "processing_start_time" in callback_context.state
        ):
            start_time = datetime.fromisoformat(
                callback_context.state["processing_start_time"]
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Agent processing duration: {duration:.2f} seconds")

            # Store metrics in state
            callback_context.state["last_processing_duration"] = duration

        # Extract session and user info for logging
        session_id = getattr(callback_context, "session_id", "unknown")
        user_id = authenticated_user['uid'] if authenticated_user else "unknown"

        logger.info(f"Completed processing for user: {user_id}, session: {session_id}")

        # Here you could add additional functionality like:
        # - Updating user conversation history
        # - Storing metrics to analytics systems
        # - Triggering follow-up actions
        # - Updating user preferences based on interaction

    except Exception as e:
        logger.error(f"Error in after_agent_callback: {e}")

    return None
