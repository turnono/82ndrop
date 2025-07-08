from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from .prompts import SYSTEM_PROMPT

# Import sub-agents
from .sub_agents.guide.agent import guide_agent
from .sub_agents.prompt_writer.agent import prompt_writer_agent
from .sub_agents.search.agent import search_agent

def create_root_agent():
    """Create the root agent following ADK's pattern."""
    return Agent(
        name="drop_agent",
        model="gemini-2.0-flash",  # Using Gemini for optimal performance
        instruction=SYSTEM_PROMPT,
        tools=[
            # Add sub-agents as tools
            AgentTool(agent=guide_agent),
            AgentTool(agent=prompt_writer_agent),
            AgentTool(agent=search_agent),
        ]
    )

# Create singleton instance
root_agent = create_root_agent() 