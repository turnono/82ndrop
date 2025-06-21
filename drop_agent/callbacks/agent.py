"""
Agent callbacks for the 82ndrop Agent System.

These callbacks handle agent lifecycle events for monitoring and logging.
"""

import logging
from typing import Optional, Any
from datetime import datetime

try:
    from google.adk.agents.callback_context import CallbackContext
    from google.genai import types
except ImportError:
    # Fallback for development/testing
    CallbackContext = Any
    types = Any

# Configure logging for callbacks
logger = logging.getLogger(__name__)


def before_agent_callback(callback_context: CallbackContext) -> None:
    """
    Before agent callback - logs the start of agent processing
    """
    try:
        logger.info("🚀 Agent processing started")
        
        # Add CORS headers to the response if available
        if hasattr(callback_context, 'response_headers'):
            callback_context.response_headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
                'Access-Control-Max-Age': '86400'
            })
        
        # Store start time for performance monitoring (as timestamp for JSON serialization)
        callback_context.state["start_time"] = datetime.now().timestamp()
        
    except Exception as e:
        logger.error(f"Error in before_agent_callback: {e}")


def after_agent_callback(callback_context: CallbackContext) -> None:
    """
    After agent callback - logs completion and performance metrics
    """
    try:
        start_time_timestamp = callback_context.state.get("start_time")
        if start_time_timestamp:
            duration = datetime.now().timestamp() - start_time_timestamp
            logger.info(f"✅ Agent processing completed in {duration:.2f}s")
        else:
            logger.info("✅ Agent processing completed")
            
    except Exception as e:
        logger.error(f"Error in after_agent_callback: {e}")


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
