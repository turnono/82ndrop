from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool

from .prompts import PROMPT
from .sub_agents.web_search.agent import web_search_agent

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction=PROMPT,
    tools=[
        AgentTool(agent=web_search_agent),
    ],
)
