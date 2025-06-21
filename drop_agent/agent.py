from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

from .prompts import PROMPT
from .sub_agents import (
    guide_agent,
    search_agent,
    prompt_writer_agent,
)
from .callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# Create Firebase Auth MCP toolset
import os
firebase_auth_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='python3',
        args=[os.path.join(os.path.dirname(__file__), 'firebase_auth_mcp_server.py')],
        cwd=os.path.dirname(__file__),  # Set working directory to drop_agent folder
    ),
    tool_filter=['validate_request_auth', 'verify_firebase_token', 'check_user_access']
)

# Create sub-agent tools
guide_tool = AgentTool(guide_agent)
search_tool = AgentTool(search_agent)
prompt_writer_tool = AgentTool(prompt_writer_agent)

# Create the authenticated root agent
root_agent = Agent(
    name="drop_agent",
    model="gemini-2.0-flash",
    instruction=f"""You are the 82ndrop video prompt assistant with authentication.

AUTHENTICATION REQUIRED:
Before processing any user request, you MUST validate authentication. 

Check the callback context state for authentication:
- If state.authenticated is True and user_info exists, proceed with the request
- If not authenticated, inform the user they need to authenticate with a Firebase Bearer token
- Only process video prompt requests for authenticated users

When authenticated:
- Welcome the user by their information from the context
- Use the available sub-agents and tools to help create amazing video prompts
- Provide detailed, creative video prompt assistance

{PROMPT}

Always check authentication first, then help users create amazing video prompts.""",
    
    output_key="video_script_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    
    # Use sub_agents for the workflow agents to allow delegation/transfer
    sub_agents=[
        guide_agent,
        search_agent,
        prompt_writer_agent,
    ],
    
    tools=[
        firebase_auth_toolset,  # Authentication tools first
    ],
) 