import os
import asyncio
from dotenv import load_dotenv

from drop_agent.services import get_runner


def main():
    """Simple REPL to interact with the 82ndDrop agent system."""
    load_dotenv()
    runner = get_runner()
    user_id = "test-user"

    # Create an async function to initialize the session
    async def _initialize_session():
        # This function must be async to `await` the create_session call
        session = await runner.session_service.create_session(
            user_id=user_id, app_name=runner.app_name
        )
        return session.id

    # Run the async function to get the session_id
    session_id = asyncio.run(_initialize_session())

    print("Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # runner.run() is a generator, so we iterate to get the final response
        final_response = None
        for r in runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=user_input,
        ):
            final_response = r

        if final_response and final_response.content:
            print(f"Agent: {final_response.content}")
        else:
            print("Agent: An error occurred or no response was generated.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
