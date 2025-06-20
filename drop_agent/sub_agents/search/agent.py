from google.adk import Agent
from google.adk.tools import google_search
from .prompt import DESCRIPTION, INSTRUCTION

search_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    tools=[google_search],
)
