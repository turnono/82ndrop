"""Guide Agent implementation."""

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from .prompt import GUIDE_PROMPT
from ...callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

guide_agent = Agent(
    name="guide_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for analyzing and structuring user video ideas for vertical (9:16) composition using Master Prompt Template structure.",
    instruction=GUIDE_PROMPT,
    
    # Flat hierarchy - no sub-agents, just analysis
    # Root agent will coordinate handoffs
    
    output_key="guide_analysis_response",
    # Re-enabling callbacks for production monitoring and analytics
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
