# 82ndrop - AI Video Prompt Generator

**Transform your ideas into professional video prompts instantly with AI-powered Master Prompt Templates.**

## 🎯 What This Project Does

82ndrop is a production-ready AI application that helps content creators generate intelligent video prompts using the Master Prompt Template strategy. Users describe their video ideas through a conversational chat interface, and our multi-agent AI system returns professionally crafted natural language video prompts optimized for vertical short-form content creation.

### Core Functionality

- **💬 Interactive Chat Interface**: Professional session-based chat with conversation history and real-time sync
- **📚 Session Management**: Complete conversation persistence with sidebar navigation and session controls
- **🎬 Master Prompt Templates**: AI generates natural language video prompts using the proven Master Prompt strategy
- **🤖 Multi-Agent AI System**: Specialized AI agents work together to analyze, enhance, and generate video prompts
- **📱 Vertical-First Design**: All prompts automatically optimized for TikTok, Instagram Reels, YouTube Shorts (9:16 format)
- **🎯 Layer-Based Composition**: Top Third/Center/Bottom Third structure for mobile viewing
- **🔐 Firebase Authentication**: Secure user authentication with Google Sign-In and access control
- **📊 Analytics & Monitoring**: Comprehensive logging and user analytics tracking
- **☁️ Cloud-Native**: Deployed on Google Cloud Run with Firebase hosting

## 🏗️ Architecture

### Frontend (Angular 19)

- **Modern UI**: Responsive design with mobile-first approach
- **Real-time Chat**: Interactive chat interface with auto-scroll and typing indicators
- **Authentication**: Firebase Auth integration with Google Sign-In
- **Progressive Web App**: Optimized for mobile and desktop usage
- **Hosted on**: Firebase Hosting at https://82ndrop.web.app

### Backend (FastAPI + Google ADK)

- **AI Agent Framework**: Built with Google Agent Development Kit (ADK)
- **Authentication Middleware**: Firebase ID token validation
- **RESTful API**: Clean endpoints for chat, sessions, and user management
- **Cloud Deployment**: Google Cloud Run with auto-scaling
- **API URL**: https://drop-agent-service-855515190257.us-central1.run.app

### AI Agent System

- **Task Master Agent**: Orchestrates the entire video prompt generation workflow
- **Guide Agent**: Analyzes user ideas and structures them for vertical composition
- **Search Agent**: Enriches concepts with web research and trending topics
- **Prompt Writer Agent**: Creates Master Prompt Templates in natural language format

## 🚀 Live Demo

**Website**: https://82ndrop.web.app

### How to Use:

1. **Sign in** with your Google account
2. **Start chatting** - click "Start Creating" or the "+" button to begin a new session
3. **Describe your video idea** (e.g., "Create a morning routine video for busy people")
4. **Receive Master Prompt Templates** - natural language video prompts optimized for vertical format
5. **Access conversation history** - all sessions saved with smart titles in the sidebar
6. **Switch between sessions** - click any previous conversation to continue
7. **Refine and iterate** - add dialogue, modify scenes, adjust timing directly in chat

## 🎬 Master Prompt Template Output

82ndrop generates **natural language Master Prompt Templates** specifically optimized for TikTok, Instagram Reels, and YouTube Shorts. Each prompt uses a structured three-layer approach (Top Third/Center/Bottom Third) designed for 9:16 vertical video creation.

### 📱 **Vertical-First Design (9:16 Format):**

- **Mobile Optimization**: Every prompt structured for phone screen viewing
- **TikTok Standards**: Follows platform best practices for engagement
- **Three-Layer Structure**: Top Third (titles), Center (main content), Bottom Third (captions)
- **Built-in Branding**: @82ndrop automatically included

### Example Master Prompt Output:

```
Generate a single, cohesive vertical short-form video (9:16 aspect ratio, optimized for TikTok mobile viewing), 30 seconds long. The screen is a composite of the following layers:

Top Third:
Display the static text: "Morning Routine That Changed My Life" in a bold, white Montserrat font with subtle drop shadow. This stays visible for the full duration.

Center (Main Scene):
Show a productive professional in a bright, minimalist bedroom demonstrating their optimized morning routine. Use smooth tracking shots and close-ups of key actions like meditation, journaling, and coffee preparation. Frame vertically to show full body movements while maintaining intimate feel. Include soft morning lighting and upbeat background music. Camera work includes close-up of alarm at 5:30 AM, medium shot of meditation pose, overhead shot of journal writing, and tracking shot of coffee preparation.

Bottom Third:
Over a motion B-roll of time-lapse sunrise, display the following captions:
0-8s: "Wake up at 5:30 AM"
8-15s: "10 minutes meditation"
15-22s: "Gratitude journaling"
22-28s: "Ready to conquer the day"
28-30s: "@82ndrop | #morningroutine"

All visual layers should feel cinematic, coherent, and aligned with the TikTok 9:16 format.
```

### Key Features:

- **📝 Natural Language**: Human-readable prompts, not code or JSON
- **🎯 Layer Structure**: Clear Top/Center/Bottom composition
- **⏰ Precise Timing**: Exact caption timing for mobile attention spans
- **📱 Mobile Framing**: Every element positioned for vertical viewing
- **🎬 Cinematic Direction**: Camera angles, lighting, and mood specified
- **🏷️ Auto Branding**: @82ndrop branding automatically included
- **🔄 Interactive Refinement**: Users can modify and enhance prompts in real-time

### Enhanced Features:

- **📚 Session History & Memory**: Complete conversation persistence with real-time sync across devices
- **💬 Professional Chat Interface**: Session sidebar with ChatGPT-style conversation management
- **🔄 Auto-Session Management**: Smart session creation and title generation from first message
- **⚡ Real-time Sync**: Firebase Realtime Database ensures instant updates across all devices
- **🎭 Dialogue Integration**: Add voiceovers and dialogue directly to prompts
- **🎵 Audio Suggestions**: Background music and sound effect recommendations
- **📊 Trending Elements**: Current TikTok trends automatically incorporated

## 🎥 Supported Content Types

- **📱 Social Media Content**: TikTok, Instagram Reels, YouTube Shorts
- **📚 Educational Videos**: Tutorials, how-tos, explainers
- **💼 Business Content**: Product demos, company culture, testimonials
- **🎬 Entertainment**: Viral stories, comedy skits, creative content
- **🎙️ Podcast Clips**: Vertical podcast content with engaging visuals
- **🏃‍♂️ Lifestyle**: Morning routines, fitness, productivity tips

## 🔧 Technical Stack

### Frontend

- **Angular 19** - Modern web framework
- **TypeScript** - Type-safe development
- **Firebase Hosting** - Global CDN deployment
- **Firebase Auth** - Secure authentication
- **Responsive Design** - Mobile-first approach

### Backend

- **Google ADK** - Agent Development Kit
- **Python/FastAPI** - High-performance API
- **Google Cloud Run** - Serverless deployment
- **Firebase Realtime Database** - Real-time data sync
- **Google Search API** - Trend research integration

### AI System

- **Gemini 2.0 Flash** - Advanced language model
- **Multi-Agent Architecture** - Specialized AI agents
- **Natural Language Processing** - Human-readable output
- **Web Search Integration** - Current trends and viral content

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- Google Cloud SDK
- Firebase CLI

### Local Development

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/82ndrop.git
cd 82ndrop
```

2. **Set up backend**

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Run the AI agent locally**

```bash
adk run drop_agent
```

4. **Set up frontend**

```bash
cd frontend
npm install
ng serve
```

5. **Access the application**

- Frontend: http://localhost:4200
- Backend: http://localhost:8080

### Deployment

The application is automatically deployed to:

- **Frontend**: https://82ndrop.web.app
- **Backend**: https://drop-agent-service-855515190257.us-central1.run.app

#### Deployment Commands

**For Firebase Authentication (Recommended):**

```bash
# Development/Testing
make deploy-gcloud

# Production
make deploy-production
```

**For ADK Authentication (Not recommended for this setup):**

```bash
make deploy
```

> **⚠️ Important**: Use `make deploy-gcloud` or `make deploy-production` for Firebase authentication. The `make deploy` command uses ADK authentication which is not compatible with our Firebase setup.

#### CORS Fix

The backend includes a custom CORS fix for ADK 1.5.0 compatibility. See [CORS Fix Documentation](ai_docs/CORS_FIX_DOCUMENTATION.md) for details.

## 📊 System Status

✅ **Production Ready**

- Master Prompt Template system active
- Natural language output working
- Vertical composition optimization enabled
- Multi-agent workflow operational
- Session management functional
- Authentication and monitoring active

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Google Agent Development Kit (ADK)
- Powered by Gemini 2.0 Flash
- Master Prompt Template strategy implementation
- Vertical-first mobile optimization approach

# Branch Protection Policy

Both `master` and `staging` branches are protected:

- All changes must be merged via Pull Request (PR)
- Only authorized users (see CODEOWNERS) can approve and merge
- All required status checks (tests, deploys) must pass before merging
- Direct pushes to these branches are blocked
- Branch protection is enforced in GitHub Settings > Branches

---
