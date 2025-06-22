# 82ndrop - AI Video Composition Generator

**Transform your ideas into layered video composition templates instantly with AI-powered assistance.**

## 🎯 What This Project Does

82ndrop is a production-ready AI application that helps content creators generate intelligent video composition templates for modern short-form content. Users describe their video ideas through a conversational chat interface, and our multi-agent AI system returns professionally crafted layered composition structures optimized for video editing and content creation.

### Core Functionality

- **💬 Interactive Chat Interface**: Clean, mobile-optimized chat UI for natural conversation with AI agents
- **🤖 Multi-Agent AI System**: Specialized AI agents work together to analyze, enhance, and generate video compositions
- **🎬 Layered Video Composition**: Generates intelligent layer templates with positioning, timing, and visual styling
- **🎯 Smart Layer Management**: Automatic layer count recommendations (2-5 layers) with z-index stacking
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

- **Task Master Agent**: Orchestrates the entire video composition generation workflow
- **Guide Agent**: Analyzes and structures user ideas into video concepts
- **Search Agent**: Enriches concepts with web research and trending topics
- **Prompt Writer Agent**: Creates intelligent layered composition templates with positioning and styling

## 🚀 Live Demo

**Website**: https://82ndrop.web.app

### How to Use:

1. Sign in with your Google account
2. Click "Start Creating" to open the chat interface
3. Describe your video idea (e.g., "Create a morning routine video for busy people")
4. Receive layered composition templates ready for video editing
5. Copy JSON output to use in your video editing workflow

## 🎬 Output Format

82ndrop generates intelligent **layered video composition templates** that specify how to structure your video with multiple overlapping layers. Each layer has specific positioning, timing, and visual styling instructions.

### Example Output:

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
      "content_prompt": "Create animated text: 'POV: You have 5 minutes before work'",
      "visual_style": "bold_animated_text",
      "duration": "full_video",
      "z_index": 3
    },
    {
      "layer_id": 2,
      "layer_type": "main_content",
      "position": "center_main",
      "content_prompt": "Film quick morning routine - wake up, hydrate, set intention",
      "visual_style": "clean_handheld_footage",
      "duration": "full_video",
      "z_index": 1
    },
    {
      "layer_id": 3,
      "layer_type": "caption_layer",
      "position": "bottom_third",
      "content_prompt": "Create caption overlay: 'What's your coffee ritual? #coffee #coffeetime'",
      "visual_style": "subtitle_style",
      "duration": "last_5_seconds",
      "z_index": 2
    }
  ],
  "final_video": {
    "title": "5-Minute Morning Reset",
    "description": "Realistic morning routine for busy people",
    "hashtags": ["#MorningRoutine", "#ProductivityHacks", "#BusyLife"],
    "call_to_action": "What's your morning hack?",
    "engagement_hook": "POV: You overslept again..."
  }
}
```

### Layer Types:

- **main_content**: Primary filmed content (background layer)
- **text_overlay**: Animated text, titles, hooks
- **caption_layer**: Subtitles, captions, CTAs
- **graphic_overlay**: Icons, animations, visual elements
- **reaction_layer**: Picture-in-picture content

### Positioning Options:

- **top_third**: Upper portion of screen
- **center_main**: Primary content area
- **bottom_third**: Lower portion for captions
- **floating_overlay**: Flexible positioning
- **split_screen**: Side-by-side layouts

## 🛠️ Technical Stack

| Component          | Technology                   | Purpose                     |
| ------------------ | ---------------------------- | --------------------------- |
| **Frontend**       | Angular 19, TypeScript, SCSS | Modern web interface        |
| **Backend**        | FastAPI, Python, Google ADK  | AI agent orchestration      |
| **Authentication** | Firebase Auth                | User management & security  |
| **Database**       | Firestore                    | User data & session storage |
| **AI Models**      | Gemini 2.0 Flash             | Natural language processing |
| **Hosting**        | Firebase Hosting             | Frontend deployment         |
| **API Hosting**    | Google Cloud Run             | Backend deployment          |
| **Functions**      | Firebase Functions           | User access management      |

## 🎨 Key Features

### 🔒 **Enterprise Security (Production-Ready)**

- **Multi-Layer Authentication**: Firebase Auth + JWT validation + middleware protection
- **Role-Based Access Control**: Basic/Premium/Admin levels with custom claims
- **Mobile Security**: iOS Safari compatibility with secure token handling
- **API Protection**: All endpoints secured with 401 unauthorized responses
- **Security Testing**: Comprehensive authentication flow validation
- **Production Hardened**: CORS, domain authorization, and error handling implemented

### 🤖 **Intelligent AI Workflow**

- Multi-agent system with specialized roles
- Context-aware composition generation
- Web search integration for trending topics
- Layered JSON composition templates
- Smart layer count recommendations (2-5 layers)
- Automatic z-index stacking and positioning

### 📱 **Mobile-Optimized UI**

- Responsive chat interface
- Touch-friendly interactions
- iOS Safari compatibility
- Auto-scroll and typing indicators

### 📊 **Analytics & Monitoring**

- User activity tracking
- API performance monitoring
- Error logging and debugging
- Usage analytics dashboard

## 🔐 Security Implementation

### **Enterprise-Grade Security Architecture**

Our security implementation demonstrates production-ready authentication and authorization:

#### **Multi-Layer Authentication**

- **Firebase Authentication**: Google Sign-In with OAuth 2.0
- **JWT Token Validation**: Firebase ID tokens validated on every API request
- **Middleware Protection**: Custom FastAPI middleware validates tokens before processing
- **Session Management**: Secure session handling with automatic token refresh

#### **Access Control System**

- **Role-Based Access**: Basic, Premium, and Admin access levels
- **Custom Claims**: Firebase custom claims for granular permissions
- **Automatic Provisioning**: New users automatically granted appropriate access
- **Permission Validation**: API endpoints protected by user permission checks

#### **Security Fixes Implemented**

- **✅ Authentication Middleware**: Fixed token validation in FastAPI backend
- **✅ CORS Configuration**: Proper cross-origin resource sharing setup
- **✅ Domain Authorization**: Firebase authorized domains configured for production
- **✅ Mobile Compatibility**: iOS Safari auth issues resolved
- **✅ Token Refresh**: Automatic token renewal for seamless user experience

#### **Security Testing**

- **Comprehensive Test Suite**: Authentication flow testing implemented
- **Unauthorized Access Prevention**: 401 errors for invalid/missing tokens
- **Token Validation**: Proper Firebase ID token verification
- **Error Handling**: Secure error responses without sensitive data exposure

### **Production Security Status: ✅ SECURED**

- **🔒 All API endpoints protected** with Firebase authentication
- **🛡️ User data encrypted** in transit and at rest
- **🔑 Access control** implemented with role-based permissions
- **📱 Mobile security** optimized for iOS/Android browsers
- **⚡ Real-time validation** of authentication tokens

## 🎨 Development Setup

### Prerequisites

- Node.js 18+
- Python 3.9+
- Firebase CLI
- Google Cloud SDK

### Frontend Setup

```bash
cd frontend
npm install
ng serve
```

### Backend Setup

```bash
pip install -r requirements.txt
python main.py
```

### Environment Configuration

- Firebase project setup required
- Google Cloud project with ADK enabled
- Environment variables for API keys and credentials

## 📈 Current Status

### ✅ **Completed Features**

- [x] Full-stack application with authentication
- [x] Multi-agent AI system operational
- [x] Mobile-responsive chat interface
- [x] Firebase integration complete
- [x] Cloud deployment active
- [x] User access control implemented
- [x] Analytics and monitoring system
- [x] Production-ready deployment

### 🎯 **Use Cases**

- **Content Creators**: Generate layered composition templates for short-form videos
- **Video Editors**: Get structured layer plans before filming/editing
- **Marketing Teams**: Create engaging social media content strategies
- **Educators**: Develop educational video composition structures
- **Businesses**: Generate promotional video layer templates
- **Social Media Managers**: Plan multi-layer content for platforms

## 🎨 **What Makes 82ndrop Unique**

Unlike traditional prompt generators that give you simple text descriptions, 82ndrop creates **intelligent composition blueprints** that tell you:

- **How many layers** your video should have
- **Where to position** each element on screen
- **What type of content** goes in each layer
- **How long** each layer should appear
- **Visual styling** recommendations for each layer
- **Z-index stacking** for proper layer ordering

This approach bridges the gap between having an idea and actually creating the video, giving creators a clear roadmap for their content production.

## 📊 Performance Metrics

- **Response Time**: < 3 seconds for prompt generation
- **Uptime**: 99.9% availability on Cloud Run
- **Mobile Compatibility**: iOS Safari, Chrome, Firefox
- **User Experience**: Seamless authentication and chat flow

## 🔮 Future Enhancements

- **Video Generation**: Direct integration with Sora/Veo APIs
- **Template Library**: Pre-built prompt templates for different niches
- **Collaboration**: Team workspaces and shared prompts
- **Advanced Analytics**: Detailed user insights and prompt performance

## 🏆 Project Achievements

This project demonstrates:

- **Modern Full-Stack Development**: Angular + FastAPI + Firebase
- **AI Agent Architecture**: Multi-agent system with Google ADK
- **Production Deployment**: Cloud-native with auto-scaling
- **User Experience**: Mobile-first design with authentication
- **Enterprise Features**: Analytics, monitoring, and access control

---

**Built for the Google ADK Hackathon** | **Live at https://82ndrop.web.app**
