import os
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
APP_NAME = "82ndrop_app"

_runner = None

def get_runner():
    """Initialize and return the ADK Runner."""
    global _runner
    if _runner is None:
        # Initialize session service with app name and initial state
        initial_state = {
            "app:language": "en",
            "app:video_format": "9:16",
            "app:voice_style": "South African"
        }
        session_service = InMemorySessionService()  # No app_name parameter needed
        memory_service = InMemoryMemoryService()

        from .agent import root_agent

        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=session_service,
            memory_service=memory_service,
        )
        print("Runner initialized successfully.")
    return _runner
