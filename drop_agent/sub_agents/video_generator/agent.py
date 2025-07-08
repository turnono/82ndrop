# drop_agent/sub_agents/video_generator/agent.py

from google.adk import Agent
from .prompt import VIDEO_GENERATOR_PROMPT
from ...custom_tools import generate_video_complete, get_video_job_status
from ...callbacks import (
    before_agent_callback,
    after_agent_callback,
    before_model_callback,
    after_model_callback,
    before_tool_callback,
    after_tool_callback,
)

# Video generation agent that handles actual video creation using VEO 3
# This agent is responsible for taking refined prompts and generating videos with Veo 3

# VEO 3 integration using direct Vertex AI API calls
# FE-Dev Note: This agent now uses Veo 3 (veo-3.0-generate-preview) which includes
# advanced features like synchronized audio generation and enhanced video quality.
# The agent communicates directly with Vertex AI and returns actual MP4 video URLs.

# --- Agent Definition ---
video_generator_agent = Agent(
    name="video_generator_agent",
    model="gemini-2.0-flash",
    description="Specialist agent for submitting finalized video scripts to Google's Veo 3 video generation engine and returning actual MP4 video files.",
    instruction=VIDEO_GENERATOR_PROMPT,
    tools=[generate_video_complete, get_video_job_status],
    output_key="video_generation_response",
    # Callbacks for logging and monitoring
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
