from google.adk import Agent
from .prompt import DESCRIPTION, INSTRUCTION

memory_manager_agent = Agent(
    name="memory_manager_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
)
