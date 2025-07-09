"""PromptWriter Agent implementation."""

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from .prompt import INSTRUCTION
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
    description="Final step specialist who creates Master Prompt Template outputs for vertical video generation using natural language format.",
    instruction=INSTRUCTION,
    tools=[AgentTool(agent=search_agent)],
    output_key="video_prompts_response",
    # Re-enabling callbacks for production monitoring and analytics
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
