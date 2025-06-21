#!/usr/bin/env python3
"""
82ndrop Authenticated Agent Main Entry Point

This is the main entry point for the ADK deployment of the authenticated 82ndrop agent.
It uses MCP (Model Context Protocol) for Firebase authentication.
"""

import asyncio
import os
from agent_with_mcp_auth import AuthenticatedDropAgent

async def main():
    """Initialize and run the authenticated agent"""
    # Set environment variables for Firebase
    os.environ['FIREBASE_SERVICE_ACCOUNT_PATH'] = 'taajirah-agents-service-account.json'
    
    # Create and initialize the authenticated agent
    agent = AuthenticatedDropAgent()
    await agent.initialize()
    
    print("🎉 82ndrop Authenticated Agent is ready!")
    print("🔐 Authentication: MCP-based Firebase authentication")
    print("🚀 Agent: Ready to process authenticated requests")
    
    # Keep the agent running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down authenticated agent...")

if __name__ == "__main__":
    asyncio.run(main()) 