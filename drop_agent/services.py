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
_session_service = None
_memory_service = None

def get_session_service():
    """Get or create the session service."""
    global _session_service
    if _session_service is None:
        _session_service = VertexAiSessionService()
    return _session_service

def get_memory_service():
    """Get or create the memory service."""
    global _memory_service
    if _memory_service is None:
        _memory_service = InMemoryMemoryService()
    return _memory_service

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
            memory_service=memory_service
        )
        logger.info("ADK Runner initialized successfully")
    return _runner

def get_or_create_session(user_id: str, session_id: str | None = None) -> str:
    """Get an existing session ID or create a new one."""
    session_service = get_session_service()
    
    if session_id:
        try:
            # Try to get existing session
            if session_service.get_session(session_id):
                return session_id
        except:
            pass  # Session not found, create new one
    
    # Create new session with a unique ID
    new_session_id = str(uuid.uuid4())
    return new_session_id

class QueueProcessorService:
    """Background service to process queued video jobs"""
    
    def __init__(self):
        self.running = False
        self.process_interval = 60  # Check queue every minute
        
    def start(self):
        """Start the queue processor"""
        if self.running:
            return
            
        self.running = True
        self._process_loop()
        
    def stop(self):
        """Stop the queue processor"""
        self.running = False
        
    def _process_loop(self):
        """Main processing loop"""
        import threading
        from .custom_tools import process_queued_jobs, get_quota_status
        
        def run():
            while self.running:
                try:
                    # Check quota status
                    quota = get_quota_status()
                    if "error" not in quota:
                        # Only process if we have quota available
                        if quota["daily"]["remaining"] > 0 and quota["monthly"]["remaining"] > 0:
                            process_queued_jobs()
                    
                    # Wait for next check
                    time.sleep(self.process_interval)
                    
                except Exception as e:
                    print(f"Error in queue processor: {e}")
                    time.sleep(self.process_interval)
        
        # Start processing thread
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

# Initialize queue processor
queue_processor = QueueProcessorService()
