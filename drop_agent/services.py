import os
import vertexai
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import Session
import uuid
import time

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
APP_NAME = "82ndrop_app"

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
    """Initialize and return the ADK Runner."""
    global _runner
    if _runner is None:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # Get or create services
        session_service = get_session_service()
        memory_service = get_memory_service()

        # Import root agent with all sub-agents
        from .agent import root_agent

        # Initialize runner with proper configuration
        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=session_service,
            memory_service=memory_service
        )
        print("✅ ADK Runner initialized successfully")
        print(f"🔧 Configuration:")
        print(f"  - Project: {PROJECT_ID}")
        print(f"  - Location: {LOCATION}")
        print(f"  - App Name: {APP_NAME}")
        print(f"  - Session Service: {session_service.__class__.__name__}")
        print(f"  - Memory Service: {memory_service.__class__.__name__}")
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
