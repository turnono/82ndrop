"""PromptWriter Agent implementation."""

from google.adk import Agent
from .prompt import DESCRIPTION, INSTRUCTION

prompt_writer_agent = Agent(
    name="prompt_writer_agent",
    model="gemini-2.0-flash",
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    # Additional configuration can be added here.
)
