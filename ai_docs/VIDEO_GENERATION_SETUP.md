# Video Generation Setup

This document explains how to set up the video generation functionality using Veo3 on Vertex AI.

## Prerequisites

1. A Google Cloud Project with Vertex AI API enabled
2. A Firebase project for authentication
3. A Google Cloud Storage bucket for storing generated videos
4. The Veo3 API enabled in your project

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Google Cloud Project settings
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Storage settings
VIDEO_BUCKET=your-video-bucket-name

# Firebase settings
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_PRIVATE_KEY=your-firebase-private-key
FIREBASE_CLIENT_EMAIL=your-firebase-client-email

# Server settings
PORT=8080
DEBUG=True
```

## API Endpoints

### 1. Generate Video

**Endpoint:** `POST /generate-video`

**Request Body:**

```json
{
  "prompt": "Your video prompt",
  "api_key": "Your Vertex AI API key",
  "user_id": "Firebase user ID",
  "session_id": "Current session ID"
}
```

**Response:**

```json
{
  "jobId": "operation-name",
  "status": "processing",
  "message": "Video generation started successfully"
}
```

### 2. Check Video Status

**Endpoint:** `GET /video-status/{job_id}`

**Response:**

```json
{
  "status": "processing|completed|error",
  "progress": 50, // Only for processing status
  "videoUrl": "gs://bucket/path/to/video.mp4", // Only for completed status
  "error": "Error message" // Only for error status
}
```

### 3. Cancel Video Generation

**Endpoint:** `POST /cancel-video/{job_id}`

**Response:**

```json
{
  "status": "cancelled",
  "message": "Video generation cancelled successfully"
}
```

## Video Generation Parameters

The video generation is configured with the following default parameters:

- **Aspect Ratio:** 9:16 (vertical format for TikTok)
- **Duration:** 8 seconds (maximum allowed)
- **Sample Count:** 1 video per request
- **Person Generation:** Allows adult people only
- **Negative Prompt:** "blurry, low quality, distorted, unrealistic"

## Storage Structure

Generated videos are stored in Google Cloud Storage with the following path structure:

```
gs://{VIDEO_BUCKET}/users/{user_id}/sessions/{session_id}/video.mp4
```

## Error Handling

The API endpoints handle the following error cases:

1. **Authentication Errors:**

   - 401: User not authenticated
   - 403: User not authorized

2. **Input Validation Errors:**

   - 400: Missing required fields
   - 400: Invalid parameters

3. **Processing Errors:**
   - 500: Video generation failed
   - 500: Operation status check failed
   - 500: Operation cancellation failed

## Logging

The application logs important events with the following levels:

- **INFO:** Operation progress, successful completions
- **ERROR:** Failed operations, API errors
- **DEBUG:** Detailed operation information (when DEBUG=True)

## Security Considerations

1. **API Key Protection:**

   - API keys are only used server-side
   - Keys are never logged or exposed in responses

2. **Access Control:**

   - All endpoints require Firebase authentication
   - Users can only access their own videos
   - Storage paths are scoped to user ID

3. **Resource Limits:**
   - One video generation at a time per user
   - Maximum video duration: 8 seconds
   - Storage quota monitoring recommended

## Testing

For local development:

1. Set up environment variables
2. Run the FastAPI server: `uvicorn main:app --reload`
3. Use the frontend application or test with curl:

```bash
# Generate video
curl -X POST http://localhost:8080/generate-video \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test prompt","api_key":"key","user_id":"uid","session_id":"sid"}'

# Check status
curl -X GET http://localhost:8080/video-status/{job_id} \
  -H "Authorization: Bearer $FIREBASE_TOKEN"

# Cancel generation
curl -X POST http://localhost:8080/cancel-video/{job_id} \
  -H "Authorization: Bearer $FIREBASE_TOKEN"
```
