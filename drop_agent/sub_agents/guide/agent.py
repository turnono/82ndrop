"""Guide Agent implementation."""

from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from drop_agent.sub_agents.guide.prompt import GUIDE_PROMPT
from drop_agent.sub_agents.prompt_writer.agent import prompt_writer_agent
from drop_agent.callbacks import (
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
    description="Specialist agent for analyzing and structuring user video ideas for vertical (9:16) composition using Master Prompt Template structure.",
    instruction="""You are a video structure specialist that creates detailed vertical (9:16) video concepts.
    
    When you receive input from the search agent:
    1. Extract both the original user request and the trend insights
    2. Create a comprehensive video structure incorporating:
       - User's core requirements
       - Current trends and viral elements
       - Vertical composition best practices
    3. Transfer to the prompt writer agent for final formatting
    
    Focus on blending the user's needs with trending elements in a cohesive 9:16 format.""",
    
    # Include only prompt_writer_agent to avoid tool conflicts
    sub_agents=[prompt_writer_agent],
    
    output_key="guide_analysis_response",
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)
