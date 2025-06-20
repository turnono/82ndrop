"""
Callback functions for the 82ndrop Agent System.

This module provides callback hooks for:
- Agent lifecycle (before/after agent processing)
- Model interactions (before/after model calls)
- Tool executions (before/after tool invocations)
"""

from .agent import before_agent_callback, after_agent_callback
from .model import before_model_callback, after_model_callback
from .tool import before_tool_callback, after_tool_callback

__all__ = [
    "before_agent_callback",
    "after_agent_callback",
    "before_model_callback",
    "after_model_callback",
    "before_tool_callback",
    "after_tool_callback",
]
