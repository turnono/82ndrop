# 82ndrop Technical State Documentation

## 🏗️ Current Architecture

### Backend (FastAPI + Google ADK)

#### Core Components

- FastAPI application with Firebase authentication middleware
- Google ADK-based multi-agent system
- Vertex AI integration for video generation
- Google Cloud Storage for video storage

#### Environment-Specific Configuration

- Production API: `https://drop-agent-service-855515190257.us-central1.run.app`
- Video Storage:
  - Production: `gs://82ndrop-videos-taajirah`
  - Staging/Other: `gs://82ndrop-videos-staging-taajirah`

### Frontend (Angular 19)

#### Core Components

- Firebase Authentication with Google Sign-In
- Real-time session management with Firebase Realtime Database
- Analytics tracking with Firebase Analytics
- Responsive design optimized for mobile

#### Environment URLs

- Production: `https://82ndrop.web.app`
- Staging: `https://82ndrop-staging.web.app`

## 🔐 Authentication & Security

### Firebase Authentication

- All endpoints protected by `FirebaseAuthMiddleware`
- Token verification with proper audience claim ("taajirah")
- Custom claims for access control:
  ```json
  {
    "agent_access": true,
    "access_level": "basic|premium|admin",
    "agent_permissions": {
      "82ndrop": true,
      "video_prompts": true,
      "search_agent": false, // Premium only
      "guide_agent": true,
      "prompt_writer": true
    }
  }
  ```

### Access Levels

1. **Basic Access**
   - Guide Agent
   - Prompt Writer Agent
   - Basic video prompts
2. **Premium Access**
   - All Basic features
   - Search Agent
   - Advanced prompt features
3. **Admin Access**
   - All Premium features
   - User management
   - Analytics access

## 🚀 Deployment & CI/CD

### Branch Protection Policy

- All changes must go through Pull Requests
- Direct pushes to `master` and `staging` are blocked
- Required status checks must pass
- Only authorized users can approve/merge

### GitHub Actions Workflows

1. **Production (`deploy.yml`)**

   - Triggers on push to `master`
   - Deploys backend to Cloud Run
   - Deploys frontend to Firebase Hosting
   - 60-second verification wait

2. **Staging (`deploy-staging.yml`)**
   - Triggers on PR to `staging`
   - Uses staging-specific secrets
   - Deploys to staging environments

### Deployment Commands

✅ **Allowed:**

- All deployments must go through GitHub Actions
- PR-based workflow for all changes

❌ **Prohibited:**

- Manual `make deploy` commands
- Direct deployments to production

## 🎥 Video Generation

### Configuration

- Uses Vertex AI's Veo3 model
- 8-second maximum duration
- 9:16 aspect ratio (vertical format)
- Environment-specific GCS buckets

### Endpoints

1. **Generate Video** (`POST /generate-video`)

   ```json
   {
     "prompt": "Video prompt",
     "user_id": "Firebase user ID",
     "session_id": "Current session ID"
   }
   ```

2. **Check Status** (`GET /video-status/{operation_name}`)
   - Supports both short IDs and full operation names
   - Checks both Vertex AI and GCS for video status

### Storage Structure

```
gs://{VIDEO_BUCKET}/
  ├── users/{user_id}/sessions/{session_id}/
  ├── test/{operation_id}/
  └── lake_scene/{operation_id}/
```

## 🤖 AI Agent System

### Agent Workflow

1. **Guide Agent**

   - Analyzes content for vertical composition
   - Structures into Top/Center/Bottom thirds
   - Mobile-first optimization

2. **Search Agent**

   - Web research integration
   - Trend analysis
   - Premium feature only

3. **Prompt Writer Agent**
   - Generates Master Prompt Templates
   - Natural language output
   - TikTok-optimized format

### Master Prompt Template

```
Generate a single, cohesive vertical short-form video (9:16 aspect ratio, optimized for TikTok mobile viewing), [DURATION] seconds long. The screen is a composite of the following layers:

Top Third:
Display the static text: "[TOP_LINE]" in a [FONT_STYLE] font. This stays visible for the full duration.

Center (Main Scene):
Show [MAIN_SCENE_DESCRIPTION, including camera style, mood, and any voice-over]. Frame it vertically for mobile viewing.

Bottom Third:
Over a motion B-roll [BACKGROUND_DESCRIPTION], display the following captions:
[TIME_1]: "[CAPTION_1]"
[TIME_2]: "[CAPTION_2]"
Include the branding text "@82ndrop | #tiktokfilm" in the bottom third.
```

## 📊 Session Management

### Firebase Integration

- Real-time session synchronization
- Cross-device access
- Persistent chat history

### Session Structure

```
firebase/
  ├── sessions/{session_id}/
  │   ├── title
  │   ├── created_at
  │   ├── updated_at
  │   └── messages/
  │       ├── {message_id}/
  │       │   ├── content
  │       │   ├── type (user|agent)
  │       │   └── timestamp
  └── users/{user_id}/
      └── sessions/
          └── {session_id}
```

## 🧪 Testing & Validation

### Backend Tests

- ADK evaluator framework
- Golden test suite for agent validation
- Authentication flow verification

### Frontend Tests

- Angular component testing
- E2E testing with Cypress
- Firebase integration tests

### Deployment Verification

- Health endpoint checks
- Authentication validation
- Cross-origin verification
