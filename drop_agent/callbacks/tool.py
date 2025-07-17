"""
Tool execution callbacks for the 82ndrop Agent System

Monitors tool executions and integrates with RAG Memory Service 
for enhanced user experience.
"""

import time
import logging
from typing import Dict, Any, Optional, Union
from google.adk.tools.tool_context import ToolContext
from google.adk.tools import BaseTool

logger = logging.getLogger(__name__)


def before_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, **kwargs
) -> Optional[Dict]:
    """
    Called before a tool is executed.

    Args:
        tool: The tool about to be executed
        args: Arguments passed to the tool
        tool_context: The tool execution context from ADK
        **kwargs: Additional arguments from the framework

    Returns:
        Optional[Dict]: Return None to proceed, or dict to override tool execution
    """
    try:
        # Get tool information
        tool_name = getattr(tool, "name", getattr(tool, "__name__", str(tool)))
        function_call_id = getattr(tool_context, "function_call_id", "unknown_call")

        # Store start time for performance tracking
        if not hasattr(tool_context, "state"):
            tool_context.state = {}

        tool_context.state[f"{tool_name}_start_time"] = time.time()
        tool_context.state["current_tool_name"] = tool_name
        tool_context.state["current_function_call_id"] = function_call_id

        # Log tool execution start
        logger.info(
            f"🔧 Starting tool execution: {tool_name} (call_id: {function_call_id})"
        )
        logger.debug(f"Tool arguments: {args}")

        # Track tool usage patterns
        _track_tool_usage(tool_name, tool_context)

        # Return None to proceed with normal tool execution
        return None

    except Exception as e:
        logger.error(f"Error in before_tool_callback: {e}")
        # Don't raise - callbacks should be non-blocking
        return None


def after_tool_callback(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    response: Any = None,
    **kwargs,
) -> Optional[Dict]:
    """
    Called after a tool is executed.

    Args:
        tool: The executed tool
        args: Arguments that were passed to the tool
        tool_context: The tool execution context from ADK
        response: The tool's response (may also be passed in kwargs)
        **kwargs: Additional arguments from the framework

    Returns:
        Optional[Dict]: Return None to use original response, or dict to override response
    """
    try:
        # Handle cases where response or tool_context might be in kwargs (fallback)
        if response is None and "response" in kwargs:
            response = kwargs["response"]
        if response is None and "tool_response" in kwargs:
            response = kwargs["tool_response"]

        # Validate tool_context is a proper object, not a string
        if tool_context is not None and (
            isinstance(tool_context, str) or not hasattr(tool_context, "__dict__")
        ):
            logger.debug(
                f"Invalid tool_context type: {type(tool_context)}, creating minimal context"
            )
            tool_context = None

        # Get tool information
        tool_name = getattr(tool, "name", getattr(tool, "__name__", str(tool)))
        function_call_id = (
            getattr(tool_context, "function_call_id", "unknown_call")
            if tool_context
            else "unknown_call"
        )

        # Ensure context has state (only if we have a valid tool_context)
        if tool_context and not hasattr(tool_context, "state"):
            try:
                tool_context.state = {}
            except (AttributeError, TypeError):
                logger.debug(
                    f"Cannot set state on tool_context of type {type(tool_context)}"
                )
                tool_context = None

        # Calculate execution time
        start_time = None
        execution_time = 0.0

        if (
            tool_context
            and hasattr(tool_context, "state")
            and isinstance(tool_context.state, dict)
        ):
            start_time = tool_context.state.get(f"{tool_name}_start_time", time.time())
            execution_time = time.time() - start_time
        elif (
            tool_context
            and hasattr(tool_context, "state")
            and isinstance(tool_context.state, str)
        ):
            # If state is a string, we can't get the start time, so estimate a small execution time
            execution_time = 0.01
        else:
            # Fallback: estimate a small execution time
            execution_time = 0.01

        # Determine success based on response
        success = response is not None and not (
            isinstance(response, str) and response.startswith("Error:")
        )

        # Log tool completion
        logger.info(
            f"🔧 Completed tool execution: {tool_name} ({'✅' if success else '❌'}) in {execution_time:.2f}s"
        )
        logger.info(f"Tool response: {response}")

        # Store performance metrics (only if we have a valid tool_context with state)
        if (
            tool_context
            and hasattr(tool_context, "state")
            and isinstance(tool_context.state, dict)
        ):
            try:
                if "tool_metrics" not in tool_context.state:
                    tool_context.state["tool_metrics"] = []

                tool_context.state["tool_metrics"].append(
                    {
                        "tool_name": tool_name,
                        "function_call_id": function_call_id,
                        "execution_time": execution_time,
                        "success": success,
                        "timestamp": time.time(),
                        "args_count": len(args) if args else 0,
                        "response_type": type(response).__name__
                        if response
                        else "None",
                    }
                )

                # Store the duration for this specific tool
                tool_context.state[f"{tool_name}_last_duration"] = execution_time
            except (AttributeError, TypeError) as e:
                logger.debug(f"Could not store tool metrics: {e}")

        # Memory handling is now done automatically by ADK

        logger.debug(
            f"Tool response type: {type(response).__name__ if response else 'None'}"
        )

        # Return None to use the original response
        return None

    except Exception as e:
        logger.error(f"Error in after_tool_callback: {e}")
        # Don't raise - callbacks should be non-blocking
        return None


def _track_tool_usage(tool_name: str, context: ToolContext) -> None:
    """
    Track tool usage patterns for insights.

    Args:
        tool_name: Name of the tool being used
        context: Tool execution context (may be None or invalid)
    """
    try:
        # Skip if context is invalid
        if not context or isinstance(context, str) or not hasattr(context, "__dict__"):
            logger.debug("Skipping tool usage tracking - invalid context")
            return

        if not hasattr(context, "state"):
            try:
                context.state = {}
            except (AttributeError, TypeError):
                logger.debug(f"Cannot create state on context of type {type(context)}")
                return

        if not isinstance(context.state, dict):
            logger.debug(f"Context state is not a dict: {type(context.state)}")
            return

        if "tool_usage_history" not in context.state:
            context.state["tool_usage_history"] = []

        context.state["tool_usage_history"].append(
            {
                "tool_name": tool_name,
                "timestamp": time.time(),
                "session_id": getattr(context, "session_id", "unknown"),
                "agent_name": getattr(context, "agent_name", "unknown"),
                "invocation_id": getattr(context, "invocation_id", "unknown"),
            }
        )

        # Keep only recent history (last 50 tool uses)
        if len(context.state["tool_usage_history"]) > 50:
            context.state["tool_usage_history"] = context.state["tool_usage_history"][
                -50:
            ]

    except Exception as e:
        logger.debug(f"Could not track tool usage: {e}")


