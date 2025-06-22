# 🧪 Testing Instructions for 82ndrop

## Overview

82ndrop is an AI video composition generator built with Google's Agent Development Kit. This guide covers local testing, production testing, and verification procedures.

## 🚀 Quick Start Testing

### Prerequisites

- Node.js 18+ and npm
- Python 3.12+
- Firebase CLI
- Google Cloud SDK (optional for advanced testing)

### 1. Local Development Testing

#### Backend Setup

```bash
# Clone and navigate to project
cd 82ndrop

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp drop_agent/.env.example drop_agent/.env
# Edit .env with your API keys and Firebase config

# Start backend server
python main.py
```

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### Verify Local Setup

1. Backend health check: `http://localhost:8080/health`
2. Frontend: `http://localhost:4200`
3. Check console for any errors

### 2. Authentication Testing

#### Google Sign-In Flow

1. **Navigate to app** (local or production)
2. **Click "Sign in with Google"**
3. **Complete OAuth flow**
4. **Verify successful redirect** to chat interface
5. **Check user avatar** appears in header

#### Firebase Token Validation

```bash
# Test with curl (replace TOKEN with actual Firebase token)
curl -X POST http://localhost:8080/run \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test video prompt"}'
```

### 3. Core Functionality Testing

#### Multi-Agent Workflow Test

1. **Sign in** to the application
2. **Enter test prompt**: "Create a morning routine video for busy people"
3. **Verify workflow progression**:
   - Guide Agent analysis
   - Search Agent trend enhancement
   - Prompt Writer Agent composition generation
4. **Check JSON output** contains:
   - `composition` object with layer count
   - `layers` array with proper structure
   - `final_video` metadata

#### Expected JSON Structure

```json
{
  "composition": {
    "layer_count": 3,
    "canvas_type": "vertical_short_form",
    "total_duration": "20-30 seconds",
    "composition_style": "layered_content"
  },
  "layers": [
    {
      "layer_id": 1,
      "layer_type": "text_overlay",
      "position": "top_third",
      "content_prompt": "...",
      "visual_style": "...",
      "duration": "...",
      "z_index": 3
    }
  ],
  "final_video": {
    "title": "...",
    "description": "...",
    "hashtags": [...],
    "call_to_action": "...",
    "engagement_hook": "..."
  }
}
```

### 4. UI/UX Testing

#### Mobile Responsiveness

1. **Open Chrome DevTools**
2. **Toggle device emulation** (iPhone, Android)
3. **Test core features**:
   - Sign in flow
   - Message input (should not zoom on iOS)
   - Copy JSON functionality
   - Navigation buttons

#### Desktop Experience

1. **Test on desktop** (1200px+ width)
2. **Verify enhanced features**:
   - Larger typography and spacing
   - Better layout proportions
   - Enhanced chat interface
   - Improved button sizing

#### Copy Functionality

1. **Generate a video prompt**
2. **Click "Copy JSON" button**
3. **Verify button changes** to "✅ Copied!"
4. **Paste content** elsewhere to confirm copy worked
5. **Test on mobile** to ensure text selection works

### 5. Session Management Testing

#### New Session Creation

1. **Generate a video prompt**
2. **Click the "+" button** in header
3. **Verify chat clears** and new session starts
4. **Confirm previous conversation** is gone

#### Back Navigation

1. **From chat interface**
2. **Click back arrow** (top-left)
3. **Verify navigation** to dashboard
4. **Return to chat** and confirm session persists

### 6. Error Handling Testing

#### Network Errors

1. **Disconnect internet**
2. **Try sending message**
3. **Verify error handling** and user feedback

#### Invalid Prompts

1. **Send empty message** (should be disabled)
2. **Send very long message** (test limits)
3. **Send special characters** and emojis

#### Authentication Errors

1. **Clear browser storage**
2. **Try accessing protected routes**
3. **Verify redirect** to login

### 7. Performance Testing

#### Load Testing

1. **Send multiple rapid requests**
2. **Monitor response times**
3. **Check for memory leaks** in DevTools

#### Large Response Handling

1. **Request complex video prompts**
2. **Verify UI handles** large JSON responses
3. **Test scroll performance** with many messages

### 8. Production Testing

#### Live Environment

- **URL**: `https://82ndrop.web.app`
- **Test all core flows** as in local testing
- **Verify HTTPS** and security headers
- **Check Firebase Analytics** for tracking

#### Cross-Browser Testing

- **Chrome** (primary)
- **Safari** (mobile focus)
- **Firefox**
- **Edge**

### 9. API Testing

#### Direct Backend Testing

```bash
# Health check
curl https://your-backend-url/health

# Authenticated request
curl -X POST https://your-backend-url/run \
  -H "Authorization: Bearer FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a cooking video"}'
```

#### Agent Development Kit Testing

```bash
# Test ADK integration
python -c "
from drop_agent.agent import create_agent
agent = create_agent()
print('ADK integration successful')
"
```

### 10. Security Testing

#### Authentication

- **JWT token validation**
- **Session management**
- **CORS configuration**

#### Data Privacy

- **No sensitive data logging**
- **Proper token handling**
- **GDPR compliance**

## 🔧 Troubleshooting

### Common Issues

#### "Firebase token verification failed"

- Check `.env` file configuration
- Verify service account JSON file
- Ensure proper Firebase project setup

#### "Module not found" errors

- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python virtual environment activation

#### Frontend build errors

- Clear node_modules: `rm -rf node_modules && npm install`
- Check Angular CLI version compatibility

#### Agent workflow failures

- Verify API keys in `.env`
- Check Google Cloud project permissions
- Review ADK configuration

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
python main.py

# Frontend debug
ng serve --verbose
```

## 📊 Test Checklist

### Pre-Deployment

- [ ] All unit tests pass
- [ ] Authentication flow works
- [ ] Multi-agent workflow completes
- [ ] JSON output validates
- [ ] Mobile responsiveness verified
- [ ] Copy functionality works
- [ ] Error handling tested
- [ ] Performance acceptable

### Post-Deployment

- [ ] Production URL accessible
- [ ] SSL certificate valid
- [ ] Firebase Analytics working
- [ ] All core features functional
- [ ] Cross-browser compatibility
- [ ] Mobile app performance

## 📞 Support

For testing issues:

1. Check console logs (browser and server)
2. Verify environment configuration
3. Test with minimal example
4. Review error messages carefully

**Happy Testing! 🚀**
