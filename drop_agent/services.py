import os
import uuid
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict
from google.adk import Runner
from google.adk.sessions import BaseSessionService, Session
from google.adk.memory import InMemoryMemoryService
import vertexai

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "taajirah")  # Default to taajirah project
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")  # Default to us-central1
APP_NAME = "drop_agent"  # Use simple name for local development

class CustomSessionService(BaseSessionService):
    """Custom session service for local development."""
    
    def __init__(self):
        self.sessions = {}
        self.current_session = None
        logger.info("Initialized CustomSessionService")
        
    async def create_session(self, app_name: str, user_id: str) -> Session:
        """Create a new session."""
        session = Session(
            id=str(uuid.uuid4()),
            app_name=app_name,
            user_id=user_id,
            state={"messages": []}  # Initialize with empty messages list
        )
        self.sessions[session.id] = session
        logger.info(f"Created new session {session.id} for user {user_id}")
        return session
        
    async def get_session(self, session_id: str, app_name: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Session]:
        """Get a session by ID."""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return None
        if app_name and session.app_name != app_name:
            logger.warning(f"Session {session_id} app_name mismatch: expected {app_name}, got {session.app_name}")
            return None
        if user_id and session.user_id != user_id:
            logger.warning(f"Session {session_id} user_id mismatch: expected {user_id}, got {session.user_id}")
            return None
        # Ensure session state has messages list
        if not session.state:
            logger.debug(f"Initializing empty state for session {session_id}")
            session.state = {"messages": []}
        elif "messages" not in session.state:
            logger.debug(f"Adding messages list to session {session_id} state")
            session.state["messages"] = []
        logger.debug(f"Retrieved session {session_id} with {len(session.state['messages'])} messages")
        return session
        
    async def set_current_session(self, session: Session) -> None:
        """Set the current session."""
        # Ensure session state has messages list
        if not session.state:
            logger.debug(f"Initializing empty state for session {session.id}")
            session.state = {"messages": []}
        elif "messages" not in session.state:
            logger.debug(f"Adding messages list to session {session.id} state")
            session.state["messages"] = []
        self.current_session = session
        self.sessions[session.id] = session  # Update in storage
        logger.info(f"Set current session to {session.id} with {len(session.state['messages'])} messages")
        
    def get_current_session(self) -> Optional[Session]:
        """Get the current session."""
        if self.current_session:
            logger.debug(f"Retrieved current session {self.current_session.id}")
        else:
            logger.debug("No current session set")
        return self.current_session
        
    async def list_sessions(self, user_id: str, app_name: Optional[str] = None) -> List[Session]:
        """List all sessions for a user."""
        sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        if app_name:
            sessions = [s for s in sessions if s.app_name == app_name]
        # Ensure all sessions have proper state
        for session in sessions:
            if not session.state:
                logger.debug(f"Initializing empty state for session {session.id}")
                session.state = {"messages": []}
            elif "messages" not in session.state:
                logger.debug(f"Adding messages list to session {session.id} state")
                session.state["messages"] = []
        logger.info(f"Listed {len(sessions)} sessions for user {user_id}")
        return sessions
        
    async def delete_session(self, session_id: str, app_name: Optional[str] = None, user_id: Optional[str] = None) -> None:
        """Delete a session."""
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"Attempted to delete non-existent session {session_id}")
            return
        if app_name and session.app_name != app_name:
            logger.warning(f"Session {session_id} app_name mismatch during deletion: expected {app_name}, got {session.app_name}")
            return
        if user_id and session.user_id != user_id:
            logger.warning(f"Session {session_id} user_id mismatch during deletion: expected {user_id}, got {session.user_id}")
            return
        del self.sessions[session_id]
        if self.current_session and self.current_session.id == session_id:
            self.current_session = None
        logger.info(f"Deleted session {session_id}")

_runner = None

def get_runner():
    """Initialize and return the ADK Runner singleton."""
    global _runner
    if _runner is None:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        
        # Initialize services
        session_service = CustomSessionService()  # Use custom session service for local development
        memory_service = InMemoryMemoryService()
        
        # Import agent
        from .agent import root_agent
        
        # Create runner
        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=session_service,
            memory_service=memory_service
        )
        logger.info("ADK Runner initialized successfully")
    return _runner
