from google.adk import Agent
from .sub_agents.guide.agent import guide_agent
from .sub_agents.search.tools.search_tool import SearchEnhancementTool
from .prompts import ROOT_PROMPT
from .callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# Create the root agent focused on prompt generation
root_agent = Agent(
    name="drop_agent",
    model="gemini-2.0-flash",
    instruction=ROOT_PROMPT,
    sub_agents=[guide_agent],  # Only use guide_agent as sub-agent
    tools=[SearchEnhancementTool()],  # Use search enhancement tool
    output_key="prompt_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback
) 