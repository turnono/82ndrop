# 82ndrop Deployment Summary

## Overview

All deployments for 82ndrop must be performed through GitHub Actions workflows. Manual deployments using `make` commands are strictly prohibited.

## Deployment Environments

### Production

- **Backend URL:** `https://drop-agent-service-855515190257.us-central1.run.app`
- **Frontend URL:** `https://82ndrop.web.app`
- **Video Storage:** `gs://82ndrop-videos-taajirah`

### Staging

- **Frontend URL:** `https://82ndrop-staging.web.app`
- **Video Storage:** `gs://82ndrop-videos-staging-taajirah`

## Branch Protection Policy

### Protected Branches

1. `master` (production)
2. `staging`

### Rules

- ✅ All changes must go through Pull Requests
- ✅ Required status checks must pass
- ✅ Only authorized users can approve/merge
- ❌ Direct pushes are blocked

## Deployment Workflows

### 1. Production Deployment

**Workflow:** `.github/workflows/deploy.yml`

**Triggers:**

- Push to `master`
- Manual trigger via `workflow_dispatch`

**Jobs:**

1. `deploy-backend`

   - Authenticates with Google Cloud
   - Deploys to Cloud Run
   - 60-second verification wait
   - Uses production environment variables

2. `deploy-frontend`
   - Builds Angular app with production config
   - Deploys to Firebase Hosting (82ndrop target)

### 2. Staging Deployment

**Workflow:** `.github/workflows/deploy-staging.yml`

**Triggers:**

- Pull request to `staging`
- Manual trigger via `workflow_dispatch`

**Jobs:**

1. `deploy-backend`

   - Uses staging-specific secrets
   - Deploys to staging Cloud Run service
   - Uses staging environment variables

2. `deploy-frontend`
   - Builds with staging configuration
   - Deploys to staging Firebase target

## Environment Variables

### Production

```bash
GOOGLE_CLOUD_PROJECT=taajirah
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=true
ENV=production
```

### Staging

```bash
STAGING_GOOGLE_CLOUD_PROJECT=taajirah
STAGING_GOOGLE_CLOUD_LOCATION=us-central1
STAGING_GOOGLE_GENAI_USE_VERTEXAI=true
ENV=staging
```

## Deployment Verification

### Backend Health Check

```bash
# Production
curl https://drop-agent-service-855515190257.us-central1.run.app/health

# Staging
curl https://drop-agent-service-staging-855515190257.us-central1.run.app/health
```

### Frontend Verification

1. Test Google Sign-In
2. Verify Firebase token audience ("taajirah")
3. Check API connectivity
4. Verify CORS headers

## ❌ Prohibited Actions

The following actions are strictly prohibited:

1. Manual deployments using `make deploy`
2. Direct pushes to protected branches
3. Bypassing PR reviews
4. Using ADK authentication commands

## Rollback Procedure

1. **Identify the last good deployment:**

   ```bash
   gcloud run revisions list --service=drop-agent-service
   ```

2. **Create rollback PR:**

   - Target the affected branch (`master` or `staging`)
   - Reference the last good commit
   - Mark as "ROLLBACK" in title

3. **Emergency Rollback:**
   If needed, manually trigger the workflow with the last good commit.
