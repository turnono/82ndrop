from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
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

# Create sub-agent tools
guide_tool = AgentTool(guide_agent)
search_tool = AgentTool(search_agent)
prompt_writer_tool = AgentTool(prompt_writer_agent)

# Create the authenticated root agent
root_agent = Agent(
    name="drop_agent",
    model="gemini-2.0-flash",
    instruction=f"""You are the 82ndrop video prompt assistant. 
{PROMPT}""",
    
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
        guide_tool,
        search_tool,
        prompt_writer_tool,
    ],
) 