# Quick Guide: Building a Hierarchical Agent System with ADK

This guide provides a template for setting up a modular, multi-agent AI system similar to `sim-memory`, using the Google Agent Development Kit (ADK). The goal is to create a structure that you can easily "plug into" another project.

## Core Idea: A Team of Specialists

Instead of one monolithic agent, we create a "team" of agents.

1.  A **Root Agent** (or "manager") that acts as the primary coordinator.
2.  Multiple **Sub-Agents** (or "specialists"), each with a specific domain of expertise (e.g., memory, business analysis, web search).

The Root Agent's main job is to understand a user's request and delegate it to the correct Sub-Agent.

## 1. Project Structure Blueprint

Here is the essential directory structure you can replicate:

```
your_project_name/
├── main.py                     # Main application entry point
├── requirements.txt
├── .env                        # Environment variables
│
└── your_agent_package/         # Your main agent Python package
    ├── __init__.py
    ├── agent.py                # Defines the Root Agent
    ├── prompts.py              # Prompts for the Root Agent
    ├── services.py             # Configuration for memory/session services
    │
    └── sub_agents/             # Directory for specialist agents
        ├── __init__.py
        │
        ├── memory_manager/
        │   ├── __init__.py
        │   ├── agent.py
        │   └── prompt.py
        │
        └── another_specialist/
            ├── __init__.py
            ├── agent.py
            ├── prompt.py
            └── tools/
                ├── __init__.py
                └── custom_tools.py
```

## 2. Step-by-Step Setup

### Step 1: Environment and Dependencies

Create a `requirements.txt` file with the core dependency:

```txt
# requirements.txt
google-cloud-aiplatform
google-adk
```

Then, set up your environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Define a Sub-Agent (Specialist)

It's easiest to start with a specialist. Let's create a simple `web_search_agent`.

**`your_agent_package/sub_agents/web_search/prompt.py`**:

```python
DESCRIPTION = "Specialist agent for performing web searches using Google Search"
INSTRUCTION = "You are a web search specialist. Your role is to find current, accurate information from the web. Use your search tool to answer the user's query."
```

**`your_agent_package/sub_agents/web_search/agent.py`**:

```python
from google.adk import Agent
from google.adk.tools import google_search
from .prompt import DESCRIPTION, INSTRUCTION

web_search_agent = Agent(
    name="web_search_agent",
    model="gemini-2.0-flash", # A model that supports built-in tools
    description=DESCRIPTION,
    instruction=INSTRUCTION,
    tools=[google_search],
)
```

### Step 3: Define the Root Agent (Manager)

The Root Agent's job is to delegate. You must instruct it to do so in its prompt.

**`your_agent_package/prompts.py`**:

```python
PROMPT = """You are the root agent. You have a team of specialists.
Your job is to understand the user's request and delegate to the correct specialist.

- For questions about current events or real-time information, use the 'web_search_agent'.

When you delegate, the specialist will handle the task.
"""
```

**`your_agent_package/agent.py`**:

```python
from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from .prompts import PROMPT

# Import your sub-agent(s)
from .sub_agents.web_search.agent import web_search_agent

root_agent = Agent(
    name="root_agent",
    model="gemini-2.0-flash",
    instruction=PROMPT,
    # ADK uses AgentTool to wrap a sub-agent so it can be called like a tool
    tools=[
        AgentTool(agent=web_search_agent),
    ],
)
```

_Note_: For sub-agents with built-in tools like `google_search`, they must be exposed to the root agent as an `AgentTool`. For other sub-agents with custom tools, you can add them to the `sub_agents` list instead.

### Step 4: Configure Services

Create a file to handle the setup of ADK's session and memory services.

**`your_agent_package/services.py`**:

```python
import os
import vertexai
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import InMemoryMemoryService # Or VertexAiRagMemoryService
from google.adk.runners import Runner

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
APP_NAME = "my_hierarchical_app"

_runner = None

def get_runner():
    """Initializes and returns the ADK Runner."""
    global _runner
    if _runner is None:
        # 1. Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # 2. Choose your services
        session_service = VertexAiSessionService()
        memory_service = InMemoryMemoryService() # Simple in-memory, no setup needed

        # 3. Import your root agent
        from .agent import root_agent

        # 4. Create the Runner
        _runner = Runner(
            app_name=APP_NAME,
            agent=root_agent,
            session_service=session_service,
            memory_service=memory_service,
        )
        print("Runner initialized successfully.")
    return _runner
```

### Step 5: Create the Entry Point

Finally, create the `main.py` file that starts the application. This file can be a simple command-line interface for testing.

**`main.py`**:

```python
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the runner from your package
from your_agent_package.services import get_runner

async def main():
    """A simple REPL to interact with the agent."""
    runner = get_runner()
    user_id = "test-user"
    session_id = None # Let the runner create a new session

    print("Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # This is the main interaction point
        response = await runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_input,
        )

        # The first time we run, we get the session_id
        if session_id is None:
            session_id = response.session.id

        # Print the agent's final response
        print(f"Agent: {response.content}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")

```

### Step 6: Run It!

1.  Create a `.env` file in your root directory:
    ```
    GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
    GOOGLE_CLOUD_LOCATION="us-central1"
    ```
2.  Run the application:
    ```bash
    python main.py
    ```

You now have a working, hierarchical agent system.

## How to "Plug Into" Another Project

Because the entire agent logic is contained within the `your_agent_package/` directory, you can treat it as a self-contained module.

In another project, you could simply:

1.  Copy the `your_agent_package/` directory into your new project.
2.  Ensure the dependencies from `requirements.txt` are installed.
3.  Import the `get_runner` function from `your_agent_package.services` and use `await runner.run(...)` to interact with the agent system, just like in `main.py`.

This structure provides a clean separation between the agent's complex internal logic and the application that uses it.
