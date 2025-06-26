# drop_agent/sub_agents/video_generator/agent.py

from google.adk import Agent
from google.adk.tools import MCPTool
from .prompt import VIDEO_GENERATOR_PROMPT
from ...callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# FE-Dev Note: This is the ADK's built-in MCPTool. All we have to do is tell it
# the address of our Veo MCP server and the name of the tool we want to use.
# The ADK handles all the complex communication logic for us.
veo_tool = MCPTool(
    name="submit_veo_generation_job", # We keep the same name for the agent to use
    mcp_server="localhost:8004",
    service="veo",
    tool="generate_video",
    description="Submits the final video prompt to the Veo generation engine and streams back progress.",
)

# --- Agent Definition ---
video_generator_agent = Agent(
    name="video_generator_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for submitting a finalized video script to the Veo video generation engine.",
    instruction=VIDEO_GENERATOR_PROMPT,
    tools=[veo_tool], # This agent's primary tool
    output_key="video_generation_response",
    # Callbacks for logging and monitoring
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
