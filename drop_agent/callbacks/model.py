"""
Model callbacks for the 82ndrop Agent System.

These callbacks handle model interaction events for monitoring
LLM performance, token usage, and response quality.
"""

import logging
from typing import Optional, Any, Dict
from datetime import datetime

try:
    from google.adk.agents.callback_context import CallbackContext
    from google.adk.models.llm_request import LlmRequest
    from google.adk.models.llm_response import LlmResponse
except ImportError:
    # Fallback for development/testing
    CallbackContext = Any
    LlmRequest = Any
    LlmResponse = Any

# Configure logging for callbacks
logger = logging.getLogger(__name__)


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest = None
) -> None:
    """
    Callback executed before each model invocation.

    This is called before the agent sends a request to the LLM.
    Use this for logging, request modification, and performance tracking.

    Args:
        callback_context: Context object containing conversation state
        llm_request: The request being sent to the LLM (if available)

    Returns:
        None
    """
    try:
        # Log model interaction start
        logger.info("Model request initiated")

        # Extract session info for context
        session_id = getattr(callback_context, "session_id", "unknown")
        user_id = getattr(callback_context, "user_id", "unknown")

        logger.info(f"Model request for user: {user_id}, session: {session_id}")

        # Track timing for performance metrics
        if hasattr(callback_context, "state"):
            callback_context.state["model_request_start_time"] = (
                datetime.now().isoformat()
            )

        # Log request details if available
        if llm_request:
            # Log message count or other request metrics
            if hasattr(llm_request, "messages"):
                message_count = len(llm_request.messages) if llm_request.messages else 0
                logger.info(f"Sending {message_count} messages to model")

            # Log model settings if available
            if hasattr(llm_request, "model"):
                logger.info(f"Using model: {llm_request.model}")

    except Exception as e:
        logger.error(f"Error in before_model_callback: {e}")


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse = None
) -> None:
    """
    Callback executed after model response generation.

    This is called after receiving a response from the LLM.
    Use this for logging, response analysis, and performance metrics.

    Args:
        callback_context: Context object containing conversation state
        llm_response: The response from the LLM (if available)

    Returns:
        None
    """
    try:
        # Log model interaction completion
        logger.info("Model response received")

        # Calculate model response time
        if (
            hasattr(callback_context, "state")
            and "model_request_start_time" in callback_context.state
        ):
            start_time = datetime.fromisoformat(
                callback_context.state["model_request_start_time"]
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Model response time: {duration:.2f} seconds")

            # Store performance metrics
            callback_context.state["last_model_duration"] = duration

        # Extract session info for logging
        session_id = getattr(callback_context, "session_id", "unknown")
        user_id = getattr(callback_context, "user_id", "unknown")

        logger.info(
            f"Model response completed for user: {user_id}, session: {session_id}"
        )

        # Analyze response if available
        if llm_response:
            # Log response metrics
            if hasattr(llm_response, "content"):
                content_length = (
                    len(str(llm_response.content)) if llm_response.content else 0
                )
                logger.info(f"Model response length: {content_length} characters")

            # Log token usage if available
            if hasattr(llm_response, "usage"):
                usage = llm_response.usage
                if hasattr(usage, "total_tokens"):
                    logger.info(f"Total tokens used: {usage.total_tokens}")
                if hasattr(usage, "prompt_tokens"):
                    logger.info(f"Prompt tokens: {usage.prompt_tokens}")
                if hasattr(usage, "completion_tokens"):
                    logger.info(f"Completion tokens: {usage.completion_tokens}")

            # Here you could add additional functionality like:
            # - Response quality analysis
            # - Content filtering or validation
            # - Custom metrics collection
            # - Response caching logic

    except Exception as e:
        logger.error(f"Error in after_model_callback: {e}")
