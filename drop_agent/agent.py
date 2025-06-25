from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from .prompts import PROMPT
from .sub_agents import guide_agent, search_agent, prompt_writer_agent
from .callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# Create the authenticated root agent - Hub-and-Spoke Pattern (following proven pattern)
root_agent = Agent(
    name="task_master_agent",
    model="gemini-2.0-flash",
    instruction=f"""You are the 82ndrop task master and orchestrator. 
{PROMPT}""",
    
    output_key="video_script_response",
    # Re-enabling callbacks for production monitoring and analytics
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
    
    # Use sub_agents for agents that can be transferred to
    sub_agents=[guide_agent, prompt_writer_agent],
    
    # Use tools for utility agents (following proven pattern)
    tools=[AgentTool(agent=search_agent)],
) 