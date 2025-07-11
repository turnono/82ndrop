from google.adk import Agent
from google.adk.tools import google_search
from drop_agent.sub_agents.search.prompt import DESCRIPTION, INSTRUCTION
from drop_agent.callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

search_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    tools=[google_search],  # Only use the google_search tool
    output_key="search_enhancement_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
