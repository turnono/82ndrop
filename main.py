import os
import asyncio
from dotenv import load_dotenv

from drop_agent.services import get_runner


async def main():
    """Simple REPL to interact with the 82ndDrop agent system."""
    load_dotenv()
    runner = get_runner()
    user_id = "test-user"
    session_id = None

    print("Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        response = await runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_input,
        )

        if session_id is None:
            session_id = response.session.id

        print(f"Agent: {response.content}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
