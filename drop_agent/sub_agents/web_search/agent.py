from google.adk import Agent
from google.adk.tools import google_search
from .prompt import DESCRIPTION, INSTRUCTION

web_search_agent = Agent(
    name="web_search_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    tools=[google_search],
)
