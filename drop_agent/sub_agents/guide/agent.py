"""Guide Agent implementation."""

from google.adk import Agent
from .prompt import DESCRIPTION, INSTRUCTION

guide_agent = Agent(
    name="guide_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    # Additional configuration can be added here.
)
