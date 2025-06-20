import os
import vertexai
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
APP_NAME = "82nddrop_app"

_runner = None

def get_runner():
    """Initialize and return the ADK Runner."""
    global _runner
    if _runner is None:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        session_service = VertexAiSessionService()
        memory_service = InMemoryMemoryService()

        from .agent import task_master_agent

        _runner = Runner(
            app_name=APP_NAME,
            agent=task_master_agent,
            session_service=session_service,
            memory_service=memory_service,
        )
        print("Runner initialized successfully.")
    return _runner
