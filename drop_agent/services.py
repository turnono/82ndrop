import os
from google.adk.sessions import InMemorySessionService, Session
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
APP_NAME = "drop_app"

_runner = None
_session_service = None
_memory_service = None

def get_session_service():
    """Get or initialize the session service."""
    global _session_service
    if _session_service is None:
        _session_service = InMemorySessionService()
    return _session_service

def get_memory_service():
    """Get or initialize the memory service."""
    global _memory_service
    if _memory_service is None:
        _memory_service = InMemoryMemoryService()
    return _memory_service

async def create_session(user_id: str, session_id: str) -> Session:
    """Create a new session with proper parameters."""
    session_service = get_session_service()
    session = await session_service.create_session(
        user_id=user_id,
        session_id=session_id
    )
    return session

def get_runner():
    """Initialize and return the ADK Runner."""
    global _runner
    if _runner is None:
        # Initialize services
        session_service = get_session_service()
        memory_service = get_memory_service()

        from .agent import root_agent

        _runner = Runner(
            app_name=APP_NAME,
            root_agent=root_agent,
            session_service=session_service,
            memory_service=memory_service
        )

    return _runner
