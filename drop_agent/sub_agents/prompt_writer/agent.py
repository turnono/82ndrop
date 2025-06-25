"""PromptWriter Agent implementation."""

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from .prompt import PROMPT_WRITER_PROMPT
from ..search import search_agent
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
    description="Final step specialist who creates Master Prompt Template outputs for vertical video generation using structured JSON format.",
    instruction=PROMPT_WRITER_PROMPT,
    tools=[AgentTool(agent=search_agent)],
    output_key="video_prompts_response",
    # Temporarily removing callbacks to debug "multiple tools" error
    # before_agent_callback=before_agent_callback,
    # after_agent_callback=after_agent_callback,
    # before_model_callback=before_model_callback,
    # after_model_callback=after_model_callback,
    # before_tool_callback=before_tool_callback,
    # after_tool_callback=after_tool_callback,
)
