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
firebase_auth_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='python3',
        args=['firebase_auth_mcp_server.py'],
    ),
    tool_filter=['validate_request_auth', 'verify_firebase_token', 'check_user_access']
)

# Create sub-agent tools
guide_tool = AgentTool(guide_agent)
search_tool = AgentTool(search_agent)
prompt_writer_tool = AgentTool(prompt_writer_agent)

# Create the authenticated root agent
root_agent = Agent(
    name="authenticated_drop_agent",
    model="gemini-2.0-flash",
    instruction=f"""You are the 82ndrop video prompt assistant with authentication.

AUTHENTICATION REQUIRED:
Before processing any user request, you MUST:
1. Use the 'validate_request_auth' tool to validate the user's authentication
2. Check that the user has agent access permissions  
3. Only proceed if authentication is successful

If authentication fails:
- Inform the user they need to authenticate
- Do not process their request
- Do not access any sensitive functionality

If authentication succeeds:
- Welcome the user by name
- Process their video prompt request using the available tools
- Provide helpful video creation assistance

{PROMPT}

Always authenticate first, then use the appropriate tools to help users create amazing video prompts.""",
    
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