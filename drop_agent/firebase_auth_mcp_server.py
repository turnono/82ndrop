#!/usr/bin/env python3
"""
Firebase Authentication MCP Server

A Model Context Protocol (MCP) server that provides Firebase authentication services
to AI agents and other MCP clients. This server handles user authentication,
token validation, and access control for the 82ndrop system.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import firebase_admin
from firebase_admin import auth, credentials
import mcp.types as mcp_types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseAuthMCPServer:
    """Firebase Authentication MCP Server"""
    
    def __init__(self):
        self.server = Server("firebase-auth-mcp-server")
        self.firebase_app = None
        self._setup_firebase()
        self._register_tools()
    
    def _setup_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Try to initialize Firebase with service account
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'taajirah-agents-service-account.json')
            
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                self.firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with service account")
            else:
                # Try default credentials
                self.firebase_app = firebase_admin.initialize_app()
                logger.info("Firebase Admin SDK initialized with default credentials")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _register_tools(self):
        """Register MCP tools for Firebase authentication"""
        
        @self.server.list_tools()
        async def list_tools() -> List[mcp_types.Tool]:
            """List available authentication tools"""
            return [
                mcp_types.Tool(
                    name="verify_firebase_token",
                    description="Verify a Firebase ID token and return user information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "token": {
                                "type": "string",
                                "description": "Firebase ID token to verify"
                            }
                        },
                        "required": ["token"]
                    }
                ),
                mcp_types.Tool(
                    name="check_user_access",
                    description="Check if a user has access to the agent system",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uid": {
                                "type": "string",
                                "description": "Firebase user UID"
                            }
                        },
                        "required": ["uid"]
                    }
                ),
                mcp_types.Tool(
                    name="get_user_info",
                    description="Get detailed user information from Firebase",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uid": {
                                "type": "string",
                                "description": "Firebase user UID"
                            }
                        },
                        "required": ["uid"]
                    }
                ),
                mcp_types.Tool(
                    name="validate_request_auth",
                    description="Validate authentication for an agent request",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "authorization_header": {
                                "type": "string",
                                "description": "Authorization header from the request (Bearer token)"
                            }
                        },
                        "required": ["authorization_header"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[mcp_types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "verify_firebase_token":
                    return await self._verify_firebase_token(arguments.get("token"))
                
                elif name == "check_user_access":
                    return await self._check_user_access(arguments.get("uid"))
                
                elif name == "get_user_info":
                    return await self._get_user_info(arguments.get("uid"))
                
                elif name == "validate_request_auth":
                    return await self._validate_request_auth(arguments.get("authorization_header"))
                
                else:
                    return [mcp_types.TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Unknown tool: {name}",
                            "success": False
                        })
                    )]
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "success": False
                    })
                )]
    
    async def _verify_firebase_token(self, token: str) -> List[mcp_types.TextContent]:
        """Verify Firebase ID token"""
        if not token:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Token is required",
                    "success": False
                })
            )]
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Verify the token
            decoded_token = auth.verify_id_token(token)
            
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user": {
                        "uid": decoded_token.get('uid'),
                        "email": decoded_token.get('email'),
                        "email_verified": decoded_token.get('email_verified'),
                        "name": decoded_token.get('name'),
                        "picture": decoded_token.get('picture'),
                        "custom_claims": decoded_token.get('custom_claims', {})
                    },
                    "token_valid": True
                })
            )]
            
        except auth.InvalidIdTokenError:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Invalid or expired token",
                    "success": False,
                    "token_valid": False
                })
            )]
        except Exception as e:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Token verification failed: {str(e)}",
                    "success": False,
                    "token_valid": False
                })
            )]
    
    async def _check_user_access(self, uid: str) -> List[mcp_types.TextContent]:
        """Check if user has access to agent system"""
        if not uid:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "User UID is required",
                    "success": False
                })
            )]
        
        try:
            # Get user record
            user_record = auth.get_user(uid)
            custom_claims = user_record.custom_claims or {}
            
            # Check for agent access
            has_agent_access = custom_claims.get('agentAccess', False)
            user_role = custom_claims.get('role', 'user')
            
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "access_granted": has_agent_access,
                    "user_role": user_role,
                    "custom_claims": custom_claims,
                    "uid": uid
                })
            )]
            
        except auth.UserNotFoundError:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "User not found",
                    "success": False,
                    "access_granted": False
                })
            )]
        except Exception as e:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Access check failed: {str(e)}",
                    "success": False,
                    "access_granted": False
                })
            )]
    
    async def _get_user_info(self, uid: str) -> List[mcp_types.TextContent]:
        """Get detailed user information"""
        if not uid:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "User UID is required",
                    "success": False
                })
            )]
        
        try:
            user_record = auth.get_user(uid)
            
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "user": {
                        "uid": user_record.uid,
                        "email": user_record.email,
                        "email_verified": user_record.email_verified,
                        "display_name": user_record.display_name,
                        "photo_url": user_record.photo_url,
                        "disabled": user_record.disabled,
                        "creation_timestamp": user_record.user_metadata.creation_timestamp,
                        "last_sign_in_timestamp": user_record.user_metadata.last_sign_in_timestamp,
                        "custom_claims": user_record.custom_claims or {}
                    }
                })
            )]
            
        except auth.UserNotFoundError:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "User not found",
                    "success": False
                })
            )]
        except Exception as e:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Failed to get user info: {str(e)}",
                    "success": False
                })
            )]
    
    async def _validate_request_auth(self, authorization_header: str) -> List[mcp_types.TextContent]:
        """Validate authentication for a request"""
        if not authorization_header:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Authorization header is required",
                    "success": False,
                    "authenticated": False
                })
            )]
        
        try:
            # Extract token from header
            if not authorization_header.startswith('Bearer '):
                return [mcp_types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Invalid authorization header format. Expected 'Bearer <token>'",
                        "success": False,
                        "authenticated": False
                    })
                )]
            
            token = authorization_header[7:]  # Remove 'Bearer ' prefix
            
            # Verify token and get user info
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token.get('uid')
            
            # Check access
            user_record = auth.get_user(uid)
            custom_claims = user_record.custom_claims or {}
            has_agent_access = custom_claims.get('agentAccess', False)
            
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "authenticated": True,
                    "access_granted": has_agent_access,
                    "user": {
                        "uid": uid,
                        "email": decoded_token.get('email'),
                        "name": decoded_token.get('name'),
                        "role": custom_claims.get('role', 'user')
                    }
                })
            )]
            
        except auth.InvalidIdTokenError:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Invalid or expired token",
                    "success": False,
                    "authenticated": False
                })
            )]
        except Exception as e:
            return [mcp_types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Authentication validation failed: {str(e)}",
                    "success": False,
                    "authenticated": False
                })
            )]

# Server transport setup
async def run_stdio_server():
    """Run MCP server with stdio transport"""
    server_instance = FirebaseAuthMCPServer()
    
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Firebase Auth MCP Server starting with stdio transport...")
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )

async def run_sse_server():
    """Run MCP server with SSE transport"""
    server_instance = FirebaseAuthMCPServer()
    
    # Create SSE transport
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send,
        ) as (reader, writer):
            await server_instance.server.run(
                reader, writer, server_instance.server.create_initialization_options()
            )
    
    # Create Starlette app
    app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    
    logger.info("Firebase Auth MCP Server starting with SSE transport on http://localhost:8002")
    uvicorn.run(app, host="localhost", port=8002)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sse":
        asyncio.run(run_sse_server())
    else:
        asyncio.run(run_stdio_server()) 