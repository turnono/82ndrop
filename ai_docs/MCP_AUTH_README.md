# 🔐 MCP Authentication Solution for 82ndrop

## Overview

This solution implements proper authentication for your 82ndrop agent system using **Model Context Protocol (MCP)** - a much cleaner and more scalable approach than trying to hack Firebase into ADK callbacks.

## 🎯 Problem Solved

- **Cost Control**: Prevents unlimited usage leading to high bills
- **User Management**: Only allows authenticated Firebase users
- **Usage Tracking**: Monitors and tracks user activity
- **Scalable Architecture**: Uses industry-standard MCP protocol

## 🏗️ Architecture

```
Frontend (Angular)
    ↓ (Firebase ID Token)
ADK Agent with MCP Client
    ↓ (MCP Protocol)
Firebase Auth MCP Server
    ↓ (Firebase Admin SDK)
Firebase Project
```

### Components

1. **Firebase Auth MCP Server** (`firebase_auth_mcp_server.py`)

   - Dedicated MCP server for Firebase authentication
   - Handles token verification, user access checks
   - Exposes authentication tools via MCP protocol

2. **Authenticated ADK Agent** (`drop_agent/agent_with_mcp_auth.py`)

   - Your main agent with MCP authentication integration
   - Uses authentication tools before processing requests
   - Provides secure video prompt assistance

3. **Test Suite** (`test_mcp_auth.py`)
   - Comprehensive testing of the authentication flow
   - Validates both authenticated and unauthenticated requests

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r mcp_auth_requirements.txt
```

### 2. Set Environment Variables

### 3. Test the System

```bash
python test_mcp_auth.py
```

This will:

- Start the Firebase Auth MCP Server (port 8002)
- Start the Authenticated Agent API (port 8003)
- Run comprehensive tests
- Show you exactly what's working

## 🔧 Manual Setup

### Start Firebase Auth MCP Server

```bash
# Stdio transport (for direct MCP client connections)
python firebase_auth_mcp_server.py

# SSE transport (for web-based connections)
python firebase_auth_mcp_server.py sse
```

### Start Authenticated Agent

```bash
# As API server
python drop_agent/agent_with_mcp_auth.py api

# Direct testing
python drop_agent/agent_with_mcp_auth.py
```

## 🔍 How It Works

### 1. Authentication Flow

```
User Request → Agent → MCP Auth Server → Firebase → Response
```

1. User sends request with Firebase ID token
2. Agent receives request and calls MCP auth server
3. MCP server validates token with Firebase Admin SDK
4. MCP server checks user's custom claims for agent access
5. Agent processes request only if authenticated and authorized

### 2. MCP Tools Available

The Firebase Auth MCP Server exposes these tools:

- **`validate_request_auth`**: Complete request authentication
- **`verify_firebase_token`**: Token verification only
- **`check_user_access`**: Access permission checking
- **`get_user_info`**: Detailed user information

### 3. Agent Behavior

- **Unauthenticated**: Politely asks user to authenticate
- **Authenticated but No Access**: Explains access requirements
- **Authenticated with Access**: Processes request normally

## 📝 Usage Examples

### Frontend Integration

```typescript
// In your Angular service
async callAgent(query: string) {
  const token = await this.auth.currentUser?.getIdToken();

  return this.http.post('/agent/query',
    { query },
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  ).toPromise();
}
```

### Direct API Usage

```bash
# Unauthenticated request
curl -X POST http://localhost:8003/agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a video prompt about cats"}'

# Authenticated request
curl -X POST http://localhost:8003/agent/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -d '{"query": "Create a video prompt about cats"}'
```

## 🛠️ Configuration

### Environment Variables

- `FIREBASE_SERVICE_ACCOUNT_PATH`: Path to Firebase service account JSON
- `GOOGLE_GENAI_USE_VERTEXAI`: Set to "False" for API key usage
- `GOOGLE_API_KEY`: Your Google AI API key

### Firebase Setup

Ensure your Firebase users have the `agentAccess` custom claim:

```javascript
// Cloud Function to grant access
admin.auth().setCustomUserClaims(uid, {
  agentAccess: true,
  role: "user",
});
```

## 🔒 Security Features

- **Token Validation**: Full Firebase ID token verification
- **Custom Claims**: Role-based access control
- **Request Isolation**: Each request is independently authenticated
- **No Token Storage**: Tokens are verified per-request, not stored
- **Audit Trail**: All authentication attempts are logged

## 🎉 Benefits Over Previous Approach

### ✅ What Works Now

- **Clean Architecture**: Standard MCP protocol
- **Proper Separation**: Auth logic isolated in dedicated server
- **Scalable**: Can add more auth providers easily
- **Testable**: Comprehensive test suite included
- **Firebase Integration**: Proper Firebase Admin SDK usage
- **Cost Control**: Only authenticated users can access agent

### ❌ Previous Issues Solved

- No more ADK callback hacks
- No more Firebase SDK initialization issues
- No more request header access problems
- No more anonymous user fallbacks
- No more uncontrolled public access

## 🚀 Deployment

### Local Development

```bash
python test_mcp_auth.py
```

### Production Deployment

1. Deploy Firebase Auth MCP Server to Cloud Run
2. Deploy Authenticated Agent to Cloud Run
3. Update frontend to use production endpoints
4. Configure proper environment variables

## 🐛 Troubleshooting

### Common Issues

1. **Firebase SDK Not Found**

   ```bash
   pip install firebase-admin
   ```

2. **MCP Dependencies Missing**

   ```bash
   pip install mcp>=1.5.0
   ```

3. **Service Account Issues**

   - Ensure exists
   - Check file permissions
   - Verify Firebase project ID

4. **Port Conflicts**
   - Auth server uses port 8002
   - Agent API uses port 8003
   - Ensure ports are available

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

This MCP authentication solution can be extended with:

- Additional auth providers (Auth0, Stytch, WorkOS)
- More sophisticated access controls
- Usage tracking and analytics
- Rate limiting
- Session management

## 📚 References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Google ADK MCP Integration](https://google.github.io/adk-docs/tools/mcp-tools/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [ADK Authentication Guide](https://google.github.io/adk-docs/tools/authentication/)

---

🎯 **Result**: Your 82ndrop agent now has proper authentication, cost control, and user management through a clean, scalable MCP architecture!
