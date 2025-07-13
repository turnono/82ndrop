# IAM Setup Guide: Taajirah Users → 82ndrop Agent Access

This guide shows how to set up Google Cloud IAM permissions so that users authenticated through your Taajirah Firebase project can access the 82ndrop agent system.

## IAM and Service Account Configuration

### Service Account Setup

1. Main Service Account

```
Name: taajirah-agents-service-account.json
Location: Project root directory
Purpose: Firebase authentication and Vertex AI operations
```

### Required Permissions

1. Firebase Admin SDK

- `firebase.auth.admin` - Verify Firebase ID tokens
- `firebase.projects.get` - Access project configuration

2. Vertex AI

- `aiplatform.endpoints.predict` - Access Veo 3.0 model
- `aiplatform.operations.get` - Check operation status

3. Google Cloud Storage

- `storage.objects.create` - Upload generated videos
- `storage.objects.get` - Read video files
- `storage.objects.list` - List bucket contents

### Environment Configuration

1. Production Environment

```
Project: taajirah
Region: us-central1
Storage Bucket: 82ndrop-videos-taajirah
```

2. Staging Environment

```
Project: taajirah
Region: us-central1
Storage Bucket: 82ndrop-videos-staging-taajirah
```

### Service Account Initialization

1. Backend Service

```python
# Service account loading
try:
    firebase_admin.initialize_app(
        credentials.Certificate('taajirah-agents-service-account.json')
    )
    print("Firebase initialized with service account")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
```

### Security Best Practices

1. Service Account Management

- Store service account key securely
- Regular key rotation
- Limit service account permissions
- Use separate accounts for different environments

2. Access Control

- Follow principle of least privilege
- Regular permission audits
- Monitor service account usage
- Remove unused permissions

3. Environment Isolation

- Separate service accounts per environment
- Different storage buckets per environment
- Proper IAM bindings per environment

### Common Issues and Solutions

1. Authentication Failures

```
Error: Firebase ID token has incorrect "aud" (audience) claim
Solution: Verify service account is from correct Firebase project
```

2. Permission Issues

```
Error: Permission denied accessing storage bucket
Solution: Check IAM roles and bucket permissions
```

### Monitoring and Maintenance

1. Regular Tasks

- Key rotation schedule
- Permission audits
- Usage monitoring
- Access reviews

2. Security Monitoring

- Failed authentication attempts
- Unauthorized access attempts
- Service account key usage
- Resource access patterns

### Deployment Checklist

1. Service Account Setup

- [ ] Create service account
- [ ] Assign required roles
- [ ] Download and secure key file
- [ ] Configure application

2. Permission Verification

- [ ] Test Firebase authentication
- [ ] Verify Vertex AI access
- [ ] Check storage permissions
- [ ] Validate environment isolation

3. Security Review

- [ ] Audit permissions
- [ ] Review security settings
- [ ] Check access controls
- [ ] Verify monitoring setup

### Emergency Procedures

1. Key Compromise

- Immediately revoke compromised key
- Generate new service account key
- Update application configuration
- Review security logs

2. Access Issues

- Check IAM permissions
- Verify service account status
- Review recent changes
- Check quota limits

## 🏗️ Architecture Overview

```
Taajirah Users (Firebase Auth) → Custom Claims → 82ndrop Agent API → ADK Agent System
```

Since both Taajirah and 82ndrop are in the same Google Cloud project (`taajirah`), we use Firebase Custom Claims for access control.

## 📋 Prerequisites

1. **Google Cloud Project**: `taajirah` (already configured)
2. **Firebase Project**: `taajirah` (already configured)
3. **82ndrop Agent**: Deployed or ready to deploy
4. **Firebase Admin SDK**: Access to set custom claims

## ⚙️ Setup Steps

### 1. Install Dependencies

```bash
pip install firebase-admin
```

### 2. Set Up Service Account (if not already done)

```bash
# Create service account for Firebase Admin
gcloud iam service-accounts create firebase-admin-sa \
    --description="Service account for Firebase Admin SDK" \
    --display-name="Firebase Admin Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding taajirah \
    --member="serviceAccount:firebase-admin-sa@taajirah.iam.gserviceaccount.com" \
    --role="roles/firebase.admin"

# Create and download key
gcloud iam service-accounts keys create firebase-admin-key.json \
    --iam-account=firebase-admin-sa@taajirah.iam.gserviceaccount.com
```

### 3. Set Environment Variables

Add to your `.env` file:

```bash
# Firebase Admin
GOOGLE_APPLICATION_CREDENTIALS=./firebase-admin-key.json

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Deploy Cloud Functions (Optional)

If you want to automate user access granting:

```bash
# Deploy the Cloud Functions
firebase deploy --only functions
```

### 5. Grant Agent Access to Users

#### Option A: Programmatically (Recommended)

```python
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred)

# Grant access to a user
def grant_agent_access(uid, access_level='basic'):
    custom_claims = {
        'agent_access': True,
        'access_level': access_level,
        'agent_permissions': {
            '82ndrop': True,
            'video_prompts': True,
            'search_agent': access_level != 'basic',
            'guide_agent': True,
            'prompt_writer': True
        },
        'granted_at': datetime.now().isoformat()
    }

    auth.set_custom_user_claims(uid, custom_claims)
    print(f"Agent access granted to user {uid}")

# Usage
grant_agent_access('user-uid-here', 'premium')
```

#### Option B: Via Cloud Function HTTP Endpoint

```bash
curl -X POST https://your-region-taajirah.cloudfunctions.net/grantAgentAccess \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "user-uid-here",
    "accessLevel": "basic"
  }'
```

### 6. Start the API Server

```bash
# Start the FastAPI server
python api/main.py

# Or with uvicorn directly
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Test the Integration

```bash
# Check API health
curl http://localhost:8000/health

# Test with authenticated user (requires valid Firebase ID token)
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_FIREBASE_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Create a video prompt about space exploration"
  }'
```

## 🔐 Access Levels

### Basic Access

- ✅ Guide Agent (schema creation)
- ✅ Prompt Writer Agent
- ✅ Basic video prompts
- ❌ Search Agent (premium feature)

### Premium Access

- ✅ All Basic features
- ✅ Search Agent (web search, enrichment)
- ✅ Advanced prompt features
- ✅ Priority processing

### Admin Access

- ✅ All Premium features
- ✅ User management
- ✅ System monitoring
- ✅ Analytics access

## 🚀 Production Deployment

### 1. Update API URL in Frontend

```typescript
// frontend/src/app/services/agent.service.ts
private apiUrl = 'https://your-api-domain.com'; // Update this
```

### 2. Deploy API to Cloud Run

```bash
# Build and deploy
gcloud run deploy 82ndrop-api \
    --source ./api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --project taajirah
```

### 3. Update CORS Origins

Update the CORS configuration in `api/main.py` to include your production domains.

## 🔍 Monitoring & Troubleshooting

### Check User Claims

```python
user_record = auth.get_user('user-uid')
print(user_record.custom_claims)
```

### Common Issues

1. **"User does not have access"**: User lacks custom claims
2. **"Invalid authentication token"**: Firebase ID token expired/invalid
3. **CORS errors**: Update allowed origins in FastAPI

### Logs

```bash
# View Cloud Run logs
gcloud logs read --project=taajirah --resource-names="cloud_run_revision"

# View Cloud Function logs
gcloud logs read --project=taajirah --resource-names="cloud_function"
```

## 📊 Usage Analytics

Track usage with Firebase Analytics and Cloud Monitoring:

```python
# Add to your API endpoints
from google.cloud import monitoring_v3

client = monitoring_v3.MetricServiceClient()
# Record custom metrics
```

## 🔒 Security Best Practices

1. **Token Validation**: Always verify Firebase ID tokens
2. **Rate Limiting**: Implement request rate limiting
3. **Access Logs**: Log all agent interactions
4. **Regular Audits**: Review user permissions regularly
5. **Secure Environment**: Keep service account keys secure

---

Your Taajirah users now have secure, controlled access to the 82ndrop agent system! 🎉
