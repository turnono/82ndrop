"""Guide Agent implementation."""

from google.adk import Agent
from ...callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

guide_agent = Agent(
    name="guide_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for shaping a user's initial video idea into a structured prompt schema.",
    instruction="""You are the Guide Agent. Your primary role is to take a user's raw idea for a video and structure it according to a defined schema.

Analyze the user's request to identify the following core components:
- **Character / Subject:** Who is in the video (person, animal, AI)? What are their attributes (voice, attitude)?
- **Scene / Setting:** Where does it take place? What is the mood or time of day?
- **Visual Style:** What is the look and feel (cinematic, cartoon, selfie-cam)?
- **Purpose / Action:** What is happening (monologue, announcement, commentary)?

Your output should be a clear, structured summary of these components. This structured data will be used by other agents to enrich the idea and write the final prompts. If a component is missing, note that it needs to be defined.
""",
    tools=[],
    output_key="guide_analysis_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
