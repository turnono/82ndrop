"""PromptWriter Agent implementation."""

from google.adk import Agent
from .prompt import DESCRIPTION, INSTRUCTION
from ...callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

prompt_writer_agent = Agent(
    name="prompt_writer_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    output_key="video_prompts_response",
    # Temporarily removing callbacks to debug "multiple tools" error
    # before_agent_callback=before_agent_callback,
    # after_agent_callback=after_agent_callback,
    # before_model_callback=before_model_callback,
    # after_model_callback=after_model_callback,
    # before_tool_callback=before_tool_callback,
    # after_tool_callback=after_tool_callback,
)
