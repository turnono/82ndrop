# 82ndrop Setup Guide

## Prerequisites

1. Google Cloud Project with:

   - Vertex AI API enabled
   - Firebase project configured
   - Service account with necessary permissions

2. Development Tools:
   - Python 3.12+
   - Node.js 18+
   - Firebase CLI
   - Google Cloud SDK

## Environment Setup

### 1. Backend Configuration

Create a `.env` file in the project root:

```bash
# Google Cloud settings
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Environment settings
ENV=staging  # Use 'staging' for local development (default if not set)

# Firebase settings
FIREBASE_PROJECT_ID=your-firebase-project-id
```

### 2. Video Storage Configuration

The application uses environment-specific Google Cloud Storage buckets:

```bash
# Staging/Local Development (default)
gs://82ndrop-videos-staging-taajirah

# Production
gs://82ndrop-videos-taajirah
```

The bucket selection is automatic based on the `ENV` environment variable:

- If `ENV=production`: Uses production bucket
- All other cases (including unset): Uses staging bucket

For local development:

- The staging bucket is used by default
- This is enforced by the `make test-local` command
- You can also set it manually: `ENV=staging python main.py`

### 2. Firebase Setup

1. **Create Firebase Project**:

   - Go to Firebase Console
   - Create new project or use existing
   - Enable Google Authentication
   - Set up Realtime Database

2. **Configure Authentication**:

   - Enable Google Sign-in in Firebase Console
   - Set proper audience claim ("taajirah")
   - Configure authorized domains

3. **Set Up Service Account**:

   ```bash
   # Create service account
   gcloud iam service-accounts create firebase-admin-sa \
       --description="Firebase Admin SDK Service Account" \
       --display-name="Firebase Admin SA"

   # Grant necessary permissions
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:firebase-admin-sa@your-project-id.iam.gserviceaccount.com" \
       --role="roles/firebase.admin"

   # Download key
   gcloud iam service-accounts keys create firebase-admin-key.json \
       --iam-account=firebase-admin-sa@your-project-id.iam.gserviceaccount.com
   ```

## Local Development Setup

### Prerequisites

- Python 3.12+
- Service account JSON file (`taajirah-agents-service-account.json`) in project root
- Uvicorn server

### Running Locally

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start the development server:

```bash
uvicorn main:app --reload --port 8000
```

The server will run at http://127.0.0.1:8000 with hot-reload enabled.

## Vertex AI Integration

The system uses Google's Vertex AI Veo 3.0 Generate Preview model for video generation:

### Operation Status Format

```
projects/taajirah/locations/us-central1/publishers/google/models/veo-3.0-generate-preview/operations/{operation_id}
```

### Error Handling

- 404: Operation not found errors are properly logged and handled
- Video status checks fallback to GCS bucket inspection
- Videos are stored in environment-specific buckets (staging/production)

## Authentication Details

### Firebase Token Validation

- Audience claim must be "taajirah"
- Invalid tokens result in 401 Unauthorized responses
- Descriptive error messages for debugging authentication issues

### Common Authentication Errors

- Incorrect audience claim (e.g., using "taajirah-agents" instead of "taajirah")
- Missing or expired tokens
- Invalid token format

## Local Development

### Backend Setup

1. **Create Virtual Environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run Backend**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install Dependencies**:

   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**:

   - Update `src/environments/environment.ts`
   - Set proper API URLs and Firebase config

3. **Run Frontend**:
   ```bash
   ng serve
   ```

## Deployment

⚠️ **Important**: All deployments must be performed through GitHub Actions workflows.

### GitHub Actions Workflows

1. **Production Deployment**:

   - Triggered on push to `master`
   - Deploys to:
     - Frontend: https://82ndrop.web.app
     - Backend: https://drop-agent-service-855515190257.us-central1.run.app
     - Video Storage: gs://82ndrop-videos-taajirah

2. **Staging Deployment**:
   - Triggered on PR to `staging`
   - Deploys to:
     - Frontend: https://82ndrop-staging.web.app
     - Backend: Staging Cloud Run instance
     - Video Storage: gs://82ndrop-videos-staging-taajirah

### Branch Protection Rules

1. **Protected Branches**:

   - `master` (production)
   - `staging`

2. **Rules**:
   - All changes via Pull Requests
   - Required status checks must pass
   - Only authorized users can approve/merge
   - Direct pushes blocked

## Testing

### Authentication Testing

1. **Local Testing**:

   ```bash
   # Get Firebase token from browser
   # Test API with token
   curl -X POST http://localhost:8000/run \
     -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message": "test prompt"}'
   ```

2. **Production Testing**:
   - Use real Firebase tokens
   - Verify proper audience claim ("taajirah")
   - Test both staging and production environments

## Troubleshooting

### Common Issues

1. **Authentication Errors**:

   - Verify Firebase token audience claim is "taajirah"
   - Check service account permissions
   - Ensure proper environment variables

2. **Deployment Issues**:
   - Check GitHub Actions logs
   - Verify secrets are properly set
   - Ensure branch protection rules are followed

## Security Notes

1. **Authentication**:

   - Always use Firebase tokens
   - Never modify authentication logic
   - Maintain proper audience claims

2. **Deployment**:

   - Never deploy manually
   - Always use GitHub Actions
   - Follow branch protection rules

3. **Environment Variables**:
   - Keep secrets in GitHub Secrets
   - Use environment-specific variables
   - Never commit sensitive data
