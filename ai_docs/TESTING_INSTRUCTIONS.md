# 🧪 Testing Instructions for 82ndrop

## Prerequisites

- Python 3.12+
- Node.js 18+
- Firebase CLI
- Google Cloud SDK
- Access to Firebase project
- Access to Google Cloud project

## 1. Environment Setup

### Backend Setup

1. **Create Virtual Environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:

   ```bash
   # Copy example env file
   cp .env.example .env

   # Edit .env with your settings
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ENV=staging  # Default for local development and testing
   FIREBASE_PROJECT_ID=your-firebase-project-id
   ```

### Environment-Specific Testing

1. **Local Development/Testing**:

   ```bash
   # Using make (recommended)
   make test-local  # Automatically uses staging environment

   # Or manually
   ENV=staging python main.py
   ```

2. **Storage Testing**:

   ```bash
   # Test video generation in staging
   ENV=staging python main.py

   # Verify videos are stored in:
   gs://82ndrop-videos-staging-taajirah/users/{user_id}/sessions/{session_id}/videos/
   ```

### Frontend Setup

1. **Install Dependencies**:

   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**:
   Update `src/environments/environment.ts`:
   ```typescript
   export const environment = {
     production: false,
     apiUrl: "http://localhost:8000",
     firebase: {
       // Your Firebase config
       authDomain: "taajirah.firebaseapp.com", // Important for audience claim
     },
   };
   ```

## 2. Authentication Testing

### Local Testing

1. **Start Services**:

   ```bash
   # Terminal 1: Backend
   uvicorn main:app --reload --port 8000

   # Terminal 2: Frontend
   cd frontend && ng serve
   ```

2. **Test Authentication Flow**:

   - Navigate to http://localhost:4200
   - Click "Sign in with Google"
   - Verify successful authentication
   - Check browser console for token

3. **Test API Authentication**:
   ```bash
   # Get token from browser
   curl -X POST http://localhost:8000/run \
     -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "test prompt"}'
   ```

### Common Auth Issues

1. **Audience Claim Mismatch**:

   - Error: "Firebase ID token has incorrect 'aud' claim"
   - Fix: Ensure token audience is "taajirah"

2. **Invalid Token**:

   - Error: "Token verification failed"
   - Fix: Get fresh token from browser

3. **Missing Permissions**:
   - Error: "User lacks required permissions"
   - Fix: Grant necessary custom claims

## 3. Video Storage Testing

### Test Video Status Endpoint

1. **Valid Operation ID**:

   ```bash
   curl -X GET "http://localhost:8000/video-status/8938233757571758123" \
     -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
   ```

   Expected: Returns video status or location

2. **Invalid Operation ID**:
   ```bash
   curl -X GET "http://localhost:8000/video-status/invalid_id" \
     -H "Authorization: Bearer YOUR_FIREBASE_TOKEN"
   ```
   Expected: Returns appropriate error

### Test Storage Buckets

1. **Production Bucket**:

   - Location: `gs://82ndrop-videos-taajirah`
   - Test with ENV=production

2. **Staging Bucket**:
   - Location: `gs://82ndrop-videos-staging-taajirah`
   - Test with ENV=staging

## 4. Integration Testing

### Frontend to Backend Integration

1. **Chat Flow**:

   - Start new chat session
   - Send test message
   - Verify response
   - Check session persistence

2. **Video Generation Flow**:
   - Submit video generation request
   - Check status updates
   - Verify storage location
   - Test video retrieval

### Error Handling

1. **Authentication Errors**:

   - Test expired tokens
   - Test invalid tokens
   - Test missing tokens
   - Verify error messages

2. **API Errors**:
   - Test invalid requests
   - Test missing parameters
   - Test rate limiting
   - Verify error responses

## 5. Deployment Testing

### Staging Environment

1. **Frontend**: https://82ndrop-staging.web.app

   - Test authentication
   - Test all features
   - Verify CORS settings

2. **Backend**: Staging Cloud Run instance
   - Test API endpoints
   - Verify environment variables
   - Check logging/monitoring

### Production Environment

1. **Frontend**: https://82ndrop.web.app

   - Verify authentication
   - Test all features
   - Check analytics

2. **Backend**: https://drop-agent-service-855515190257.us-central1.run.app
   - Test API endpoints
   - Monitor performance
   - Check error rates

## 6. Security Testing

### Authentication & Authorization

1. **Token Validation**:

   - Test token expiration
   - Test audience claims
   - Test custom claims

2. **Access Control**:
   - Test role-based access
   - Test feature permissions
   - Test admin functions

### CORS & Security Headers

1. **CORS Rules**:

   - Test allowed origins
   - Test blocked origins
   - Test allowed methods

2. **Security Headers**:
   - Verify CORS headers
   - Check CSP settings
   - Test auth headers

## 7. Monitoring & Logging

### Local Logs

1. **Backend Logs**:

   - Check authentication logs
   - Monitor API requests
   - Track error rates

2. **Frontend Logs**:
   - Check console errors
   - Monitor performance
   - Track user actions

### Production Monitoring

1. **Cloud Logging**:

   - Monitor error rates
   - Track API usage
   - Check authentication issues

2. **Analytics**:
   - Track user sessions
   - Monitor feature usage
   - Check error patterns

## Troubleshooting Guide

### Common Issues

1. **Authentication Problems**:

   - Check token audience ("taajirah")
   - Verify Firebase config
   - Check service account

2. **API Issues**:

   - Verify endpoints
   - Check CORS settings
   - Validate requests

3. **Storage Issues**:
   - Check bucket permissions
   - Verify environment
   - Check file paths

### Getting Help

1. **Documentation**:

   - Check this guide
   - Review other docs
   - Check Firebase docs

2. **Support**:
   - File GitHub issues
   - Contact team lead
   - Check error logs
