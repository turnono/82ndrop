# drop_agent/sub_agents/video_generator/agent.py

from google.adk import Agent
from .prompt import VIDEO_GENERATOR_PROMPT
from ...custom_tools import submit_veo_generation_job
from ...callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# Video generation agent that handles actual video creation using VEO 3
# This agent is responsible for taking refined prompts and generating videos

# VEO 3 integration using MCP Server
# FE-Dev Note: This is the ADK's MCPToolset that connects to our VEO MCP server
# The MCP server handles all the VEO 3 API communication.
# veo_toolset = MCPToolset(
#     server_parameters=StdioServerParameters(
#         command="python",
#         args=["veo_mcp_server.py"],
#         env=None
#     )
# )  # Temporarily commented out due to parameter name issue

# --- Agent Definition ---
video_generator_agent = Agent(
    name="video_generator_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for submitting a finalized video script to the Veo video generation engine.",
    instruction=VIDEO_GENERATOR_PROMPT,
    tools=[submit_veo_generation_job],
    output_key="video_generation_response",
    # Callbacks for logging and monitoring
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
