from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool

from .prompts import PROMPT
from .sub_agents import (
    guide_agent,
    taskmaster_agent,
    search_agent,
    prompt_writer_agent,
)

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction=PROMPT,
    tools=[
        AgentTool(agent=guide_agent),
        AgentTool(agent=taskmaster_agent),
        AgentTool(agent=search_agent),
        AgentTool(agent=prompt_writer_agent),
    ],
)
