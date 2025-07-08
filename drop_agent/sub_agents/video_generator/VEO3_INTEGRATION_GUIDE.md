# 🚀 Veo 3 Integration Guide

This document outlines the enhanced video generation capabilities using Google's cutting-edge **Veo 3** model (`veo-3.0-generate-preview`).

## 🆕 What's New with Veo 3

### Enhanced Features

- **🎵 Synchronized Audio Generation**: Veo 3 can generate audio that matches the video content
- **⚡ 8-Second Optimized Videos**: Fixed duration for highest quality output
- **🧠 Advanced Prompt Understanding**: Superior interpretation of complex, detailed prompts
- **🎬 Enhanced Cinematic Controls**: Better camera movement and visual effects understanding

### Technical Specifications

- **Model ID**: `veo-3.0-generate-preview`
- **Video Quality**: 720p, 24fps ultra-high-quality
- **Duration**: 8 seconds (optimized)
- **Aspect Ratios**: 16:9 (landscape), 9:16 (portrait)
- **Sample Count**: 1-4 video variations per request
- **Audio**: Synchronized audio generation capability

## 🛠️ API Parameters

### Required Parameters

```python
submit_veo_generation_job(
    prompt="Your detailed video prompt",
    user_id="user123",
    generate_audio=True  # New Veo 3 feature
)
```

### Optional Parameters

- `aspect_ratio`: "16:9" or "9:16" (default: "9:16")
- `duration_seconds`: 8 (fixed for Veo 3)
- `sample_count`: 1-4 (default: 1)
- `person_generation`: "dont_allow", "allow_adult", "allow_all" (default: "allow_adult")
- `negative_prompt`: Text describing what to avoid
- `generate_audio`: Boolean for audio generation (default: True)

## 📝 Prompt Engineering for Veo 3

### Essential Elements

Veo 3 excels with prompts that include:

1. **Subject**: Primary focus of the video
2. **Action**: What's happening in the scene
3. **Setting**: Environment and context
4. **Camera Work**: Shot composition, movement, angles
5. **Lighting**: Mood and atmosphere
6. **Style/Mood**: Overall aesthetic
7. **Audio Considerations**: Sound design elements

### Example Prompt Structure

```
"Cinematic close-up shot of a barista carefully crafting latte art in a modern coffee shop.
Steam rises from the milk as intricate patterns form in the cream.
Warm morning light filters through large windows, creating soft shadows.
The camera slowly pulls back to reveal the bustling café atmosphere.
Ambient coffee shop sounds with gentle background music."
```

## 🔧 Implementation Details

### Firebase Job Tracking

Each Veo 3 job is tracked in Firebase with enhanced metadata:

```json
{
  "status": "processing",
  "model": "veo-3.0-generate-preview",
  "parameters": {
    "aspectRatio": "9:16",
    "durationSeconds": 8,
    "generateAudio": true,
    "personGeneration": "allow_adult"
  },
  "createdAt": "timestamp",
  "userId": "user123"
}
```

### Status Monitoring

Use the `get_video_job_status` tool to check progress:

```python
get_video_job_status(job_id="your-job-id")
```

## 🎯 Best Practices

### For Optimal Results

1. **Be Specific**: Include detailed descriptions of visual elements
2. **Camera Language**: Use cinematic terminology (close-up, wide shot, dolly, pan)
3. **Audio Integration**: Mention desired sounds when `generate_audio=True`
4. **Style Keywords**: Reference specific aesthetics (film noir, documentary, commercial)
5. **Technical Details**: Specify lighting, depth of field, color palette

### Example Effective Prompts

#### Commercial Style

```
"Professional product showcase of a luxury watch on a marble surface.
Macro lens extreme close-up revealing intricate dial details.
Soft key lighting with subtle reflections. Camera orbits slowly around the watch.
Elegant ambient soundscape with subtle ticking."
```

#### Cinematic Scene

```
"Wide establishing shot of a lone figure walking through a misty forest at dawn.
Golden sunlight filters through tall trees creating volumetric lighting.
Camera tracks alongside with shallow depth of field.
Atmospheric forest sounds with distant bird calls."
```

## 🚀 Getting Started

1. **Update Dependencies**: Ensure latest versions are installed
2. **Environment Variables**: Set up Google Cloud project credentials
3. **Test Integration**: Start with simple prompts and build complexity
4. **Monitor Jobs**: Use Firebase dashboard to track generation progress

## 📊 Performance Expectations

- **Generation Time**: 2-3 minutes average
- **Quality**: Ultra-high 720p at 24fps
- **Audio Sync**: Perfectly synchronized when enabled
- **Success Rate**: High with well-structured prompts

## 🔍 Troubleshooting Guide

### Firebase Database Connection

If you encounter database region mismatch errors:

1. **Environment Setup**:

   ```bash
   export FIREBASE_DATABASE_URL=https://taajirah-default-rtdb.europe-west1.firebasedatabase.app
   export GOOGLE_APPLICATION_CREDENTIALS=./taajirah-agents-service-account.json
   ```

2. **Firebase Initialization**:

   ```python
   # In custom_tools.py
   database_url = os.getenv("FIREBASE_DATABASE_URL", "https://taajirah-default-rtdb.europe-west1.firebasedatabase.app")

   cred = credentials.Certificate(cred_path)
   firebase_admin.initialize_app(cred, {
       'databaseURL': database_url
   })
   ```

3. **Database Rules**:
   ```json
   {
     "rules": {
       ".read": "auth.token.email.endsWith('@taajirah.iam.gserviceaccount.com')",
       ".write": "auth.token.email.endsWith('@taajirah.iam.gserviceaccount.com')"
     }
   }
   ```

### Authentication

For testing and development:

1. **Test Token Handling**:

   ```python
   # In main.py
   async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
       try:
           if not credentials:
               raise HTTPException(status_code=401, detail="No credentials provided")

           token = credentials.credentials

           # For testing purposes
           if token == "test-token":
               return {
                   "uid": "test-user",
                   "email": "test@example.com",
                   "token": {
                       "email": "taajirah-agents@taajirah.iam.gserviceaccount.com"
                   }
               }

           # Normal token verification...
   ```

2. **Testing Endpoints**:

   ```bash
   # Generate video
   curl -X POST "http://localhost:8000/generate-video" \
       -H "Authorization: Bearer test-token" \
       -H "Content-Type: application/json" \
       -d '{
           "prompt": "test video",
           "user_id": "test_user",
           "aspect_ratio": "9:16",
           "duration_seconds": 8,
           "sample_count": 1,
           "person_generation": "allow_adult",
           "generate_audio": true
       }'

   # Check status
   curl -X GET "http://localhost:8000/video-status/{job_id}" \
       -H "Authorization: Bearer test-token"
   ```

### Common Issues

1. **Database Region Mismatch**: Always use the full database URL including region
2. **Authentication Errors**: Ensure service account has proper permissions
3. **Token Validation**: Use proper JWT format or test token for development
4. **Port Already in Use**: Kill existing processes with `pkill -f "python main.py"`

## 🤖 ADK Multi-Agent Integration

The video generation process is integrated into the ADK multi-agent system with the following workflow:

1. **Guide Agent** (`guide_agent`)

   - Analyzes video request for vertical (9:16) composition
   - Creates structured breakdown for 8-second duration
   - Handles animated captions, audio, and metadata

2. **Search Agent** (`search_agent`)

   - Enriches concept with current trends
   - Adds viral references and hashtags
   - Optimizes for TikTok engagement

3. **Prompt Writer Agent** (`prompt_writer_agent`)

   - Creates final enhanced prompt
   - Uses natural language Master Prompt Template
   - Includes all required elements for Veo 3

4. **Video Generator Agent** (`video_generator_agent`)
   - Handles actual video generation with Veo 3
   - Uses `generate_video_complete` tool
   - Monitors status with `get_video_job_status` tool
   - Returns MP4 video URLs when ready

### Environment Setup

For the ADK system to work properly:

1. **Required Environment Variables**:

   ```bash
   export GOOGLE_CLOUD_PROJECT=taajirah
   export GOOGLE_CLOUD_LOCATION=us-central1
   export FIREBASE_DATABASE_URL=https://taajirah-default-rtdb.europe-west1.firebasedatabase.app
   export GOOGLE_APPLICATION_CREDENTIALS=./taajirah-agents-service-account.json
   ```

2. **Service Account**:

   - Use `taajirah-agents@taajirah.iam.gserviceaccount.com`
   - Ensure it has access to:
     - Vertex AI (for ADK and Veo 3)
     - Firebase Realtime Database
     - Google Cloud Storage (for video files)

3. **ADK Configuration**:

   ```python
   # In services.py
   PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
   LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
   APP_NAME = "82ndrop_app"

   # Initialize Vertex AI
   vertexai.init(project=PROJECT_ID, location=LOCATION)

   # Initialize runner with all agents
   _runner = Runner(
       app_name=APP_NAME,
       agent=root_agent,  # Includes all sub-agents
       session_service=session_service,
       memory_service=memory_service
   )
   ```

### Testing the ADK Pipeline

1. **Start the Server**:

   ```bash
   pkill -f "python main.py" && \
   GOOGLE_APPLICATION_CREDENTIALS=./taajirah-agents-service-account.json \
   FIREBASE_DATABASE_URL=https://taajirah-default-rtdb.europe-west1.firebasedatabase.app \
   GOOGLE_CLOUD_PROJECT=taajirah \
   GOOGLE_CLOUD_LOCATION=us-central1 \
   PYTHONPATH=. python main.py
   ```

2. **Test Video Generation**:

   ```bash
   curl -X POST "http://localhost:8000/generate-video" \
       -H "Authorization: Bearer test-token" \
       -H "Content-Type: application/json" \
       -d '{
           "prompt": "test video",
           "user_id": "test_user",
           "aspect_ratio": "9:16",
           "duration_seconds": 8,
           "sample_count": 1,
           "person_generation": "allow_adult",
           "generate_audio": true
       }'
   ```

3. **Check Status**:
   ```bash
   curl -X GET "http://localhost:8000/video-status/{job_id}" \
       -H "Authorization: Bearer test-token"
   ```

### Best Practices

1. **Error Handling**:

   - Always check Firebase connection before operations
   - Validate service account permissions
   - Handle token validation gracefully
   - Monitor ADK agent callbacks for issues

2. **Performance**:

   - Use the ADK session service for state management
   - Monitor video generation progress
   - Cache frequently used data
   - Clean up completed jobs

3. **Security**:

   - Use service account for Firebase operations
   - Validate all tokens properly
   - Follow least privilege principle
   - Keep credentials secure

4. **Monitoring**:
   - Use ADK callbacks for logging
   - Track video generation success rates
   - Monitor Firebase database usage
   - Check Vertex AI quotas

---

_This integration leverages Google's most advanced video generation technology. For support or questions, refer to the main project documentation._
