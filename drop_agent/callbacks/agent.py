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

# Configure logging for callbacks
logger = logging.getLogger(__name__)


def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback executed before the agent starts processing a request.

    This callback is called at the start of each agent interaction.
    Use this for logging, metrics collection, and preparing context.

    Args:
        callback_context: Context object containing request information

    Returns:
        Optional content to inject into the conversation
    """
    try:
        # Log the start of agent processing
        logger.info("Agent processing started")

        # Extract session and user info if available
        session_id = getattr(callback_context, "session_id", "unknown")
        user_id = getattr(callback_context, "user_id", "unknown")

        logger.info(f"Processing request for user: {user_id}, session: {session_id}")

        # Add timestamp for performance tracking
        if hasattr(callback_context, "state"):
            callback_context.state["processing_start_time"] = datetime.now().isoformat()

    except Exception as e:
        logger.error(f"Error in before_agent_callback: {e}")

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
        user_id = getattr(callback_context, "user_id", "unknown")

        logger.info(f"Completed processing for user: {user_id}, session: {session_id}")

        # Here you could add additional functionality like:
        # - Updating user conversation history
        # - Storing metrics to analytics systems
        # - Triggering follow-up actions
        # - Updating user preferences based on interaction

    except Exception as e:
        logger.error(f"Error in after_agent_callback: {e}")

    return None
