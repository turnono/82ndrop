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

## 🎯 Best Practices
