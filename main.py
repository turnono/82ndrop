import os
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Import the runner and session management
from drop_agent.services import get_runner, APP_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "82ndrop agent is running"}

@app.post("/run")
async def run_agent(request: Request):
    """Run the agent with the given message."""
    try:
        # Basic auth check
        auth_header = request.headers.get("Authorization")
        if not auth_header or auth_header != "Bearer firebase":
            logger.warning("Missing or invalid Authorization header")
            raise HTTPException(status_code=401, detail="Authorization header required")
            
        # Get request body
        body = await request.json()
        logger.info(f"Received request for user {body.get('userId')} with session {body.get('sessionId')}")
        
        # Get message from request
        message = body.get("newMessage", {})
        if not message or not message.get("parts", []):
            logger.error(f"Invalid message format received: {message}")
            raise HTTPException(status_code=400, detail="Invalid message format")
            
        logger.debug(f"Processing message: {message}")
        
        # Get user ID and session ID
        user_id = body.get("userId", "test_user")
        session_id = body.get("sessionId")
        
        # Get the ADK runner
        runner = get_runner()
        
        # Create session if needed
        if not session_id:
            logger.info(f"Creating new session for user {user_id}")
            session = await runner.session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id
            )
            session_id = session.id
            logger.info(f"Created new session {session_id}")
        
        # Set current session
        session = await runner.session_service.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            raise HTTPException(status_code=404, detail="Session not found")
            
        logger.debug(f"Current session state before update: {session.state}")
        
        # Update session state with new message
        if not session.state:
            session.state = {"messages": []}
        session.state["messages"].append(message)
        await runner.session_service.set_current_session(session)
        
        logger.debug(f"Updated session state: {session.state}")
        
        # Run the agent and stream responses
        async def event_generator():
            try:
                logger.info(f"Starting agent run for session {session_id}")
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=message
                ):
                    if isinstance(event, dict):
                        yield f"data: {event}\n\n"
                    else:
                        yield f"data: {event.__dict__}\n\n"
            except Exception as e:
                logger.error(f"Error in event_generator: {str(e)}", exc_info=True)
                yield f"data: {{'error': '{str(e)}'}}\n\n"
            finally:
                logger.info(f"Completed agent run for session {session_id}")
                yield "data: [DONE]\n\n"
                
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error in run_agent: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8888))
    uvicorn.run(app, host="0.0.0.0", port=port) 