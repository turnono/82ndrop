# 82ndrop Logging & Analytics Guide

## Overview

The 82ndrop platform includes comprehensive logging and analytics tracking to monitor API usage, user behavior, and system performance. This guide details the current logging and analytics implementation.

## Log Categories

### 1. Authentication Logs

- **Location**: `logs/auth.log`
- **Content**:
  - Login attempts
  - Token validations
  - Permission checks
  - Access grants/revokes

Example log entry:

```json
{
  "timestamp": "2024-03-15T10:30:45Z",
  "level": "INFO",
  "event": "token_validation",
  "user_id": "user123",
  "status": "success",
  "audience": "taajirah"
}
```

### 2. API Request Logs

- **Location**: `logs/api.log`
- **Content**:
  - Endpoint access
  - Request parameters
  - Response status
  - Performance metrics

Example log entry:

```json
{
  "timestamp": "2024-03-15T10:31:00Z",
  "level": "INFO",
  "endpoint": "/video-status/123",
  "method": "GET",
  "status_code": 200,
  "response_time_ms": 150
}
```

### 3. Error Logs

- **Location**: `logs/error.log`
- **Content**:
  - Authentication failures
  - API errors
  - System exceptions
  - Integration issues

Example log entry:

```json
{
  "timestamp": "2024-03-15T10:32:15Z",
  "level": "ERROR",
  "error": "Firebase token has incorrect audience claim",
  "expected": "taajirah",
  "received": "taajirah-agents",
  "stack_trace": "..."
}
```

### 4. Video Operation Logs

- **Location**: `logs/video_ops.log`
- **Content**:
  - Video generation requests
  - Status checks
  - Storage operations
  - Bucket access

Example log entry:

```json
{
  "timestamp": "2024-03-15T10:33:30Z",
  "level": "INFO",
  "operation": "video_status_check",
  "operation_id": "8938233757571758123",
  "status": "completed",
  "bucket": "82ndrop-videos-staging-taajirah"
}
```

## Analytics Implementation

### 1. Firebase Analytics

#### User Analytics

```typescript
// frontend/src/app/services/analytics.service.ts
export class AnalyticsService {
  logEvent(eventName: string, params: any) {
    analytics().logEvent(eventName, {
      ...params,
      environment: environment.production ? "prod" : "staging",
    });
  }
}
```

#### Tracked Events

- User sign-in
- Session creation
- Video generation
- Feature usage
- Error occurrences

### 2. Custom Analytics

#### API Usage Metrics

```python
# backend/analytics/metrics.py
def track_api_usage(endpoint: str, user_id: str, status_code: int):
    metrics = {
        "timestamp": datetime.utcnow(),
        "endpoint": endpoint,
        "user_id": user_id,
        "status": status_code
    }
    save_metrics(metrics)
```

#### Performance Metrics

- Response times
- Error rates
- Resource usage
- API latency

## Monitoring Setup

### 1. Local Development

```bash
# View real-time logs
tail -f logs/api.log

# Filter error logs
grep ERROR logs/error.log

# Monitor auth logs
tail -f logs/auth.log | grep token_validation
```

### 2. Production Monitoring

#### Cloud Logging

```bash
# View production logs
gcloud logging read "resource.type=cloud_run_revision" --project=taajirah

# Filter auth errors
gcloud logging read "severity>=ERROR resource.type=cloud_run_revision" --project=taajirah
```

#### Analytics Dashboard

- Access: Firebase Console > Analytics
- Key metrics displayed
- Custom reports available

## Log Management

### 1. Retention Policy

- **Authentication Logs**: 30 days
- **API Logs**: 14 days
- **Error Logs**: 90 days
- **Analytics Data**: 1 year

### 2. Log Rotation

```python
# logging_config.py
LOGGING = {
    'handlers': {
        'auth_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/auth.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    }
}
```

## Security Considerations

### 1. Sensitive Data

- No tokens in logs
- No personal info
- No credentials
- Masked user IDs

### 2. Access Control

- Log access restricted
- Analytics access controlled
- Role-based dashboard access
- Audit trail maintained

## Best Practices

### 1. Logging

```python
# Good: Structured logging with context
logger.info("Video status check", extra={
    "operation_id": op_id,
    "bucket": bucket_name,
    "status": status
})

# Bad: Unstructured logging
logger.info(f"Checked video {op_id} in {bucket_name}")
```

### 2. Analytics

```typescript
// Good: Consistent event naming
analyticsService.logEvent("video_generation_started", {
  userId: user.id,
  sessionId: session.id,
});

// Bad: Inconsistent naming
analyticsService.logEvent("started-video", {
  user: user.id,
});
```

## Troubleshooting

### 1. Missing Logs

1. Check log levels
2. Verify log paths
3. Check permissions
4. Monitor disk space

### 2. Analytics Issues

1. Check Firebase config
2. Verify event parameters
3. Check network connectivity
4. Validate user sessions

## Integration Points

### 1. Backend Integration

```python
# main.py
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info("API Request", extra={
        "endpoint": request.url.path,
        "method": request.method,
        "duration": duration,
        "status": response.status_code
    })
    return response
```

### 2. Frontend Integration

```typescript
// app.module.ts
import { AnalyticsService } from './services/analytics.service';

@NgModule({
  providers: [
    AnalyticsService,
    {
      provide: APP_INITIALIZER,
      useFactory: (analytics: AnalyticsService) => {
        return () => analytics.initialize();
      },
      deps: [AnalyticsService],
      multi: true
    }
  ]
})
```

## Monitoring Alerts

### 1. Error Rate Alerts

- Threshold: >1% error rate
- Window: 5 minutes
- Channel: Email + Slack

### 2. Performance Alerts

- Response time: >500ms
- API errors: >5 in 1 minute
- Auth failures: >10 in 5 minutes

## Dashboard Access

### 1. Firebase Analytics

- URL: Firebase Console
- Access: Team leads + Admin
- Custom reports available
- Real-time monitoring

### 2. Custom Dashboard

- URL: Internal monitoring
- Access: Development team
- API metrics
- Error tracking

## Error Logging Patterns

### Vertex AI Errors

Errors from Vertex AI are logged at ERROR level with detailed error response:

```python
ERROR:root:Error from Vertex AI: {
  "error": {
    "code": 404,
    "message": "Get async operation failed...",
    "status": "NOT_FOUND"
  }
}
```

### Authentication Errors

Authentication failures are logged with detailed error messages:

```
Firebase token verification failed: Firebase ID token has incorrect "aud" (audience) claim...
```

### Success Logging

Successful operations are logged at INFO level:

- Video found in GCS: `INFO:root:Found video in GCS test directory: gs://...`
- HTTP requests: `INFO: 127.0.0.1:51738 - "GET /video-status/... HTTP/1.1" 200 OK`

### System Events

System events are logged at INFO level:

- Server startup/shutdown
- Application state changes
- File watch events during development

## Log Levels Usage

- ERROR: Used for operational errors (API failures, authentication errors)
- WARNING: Used for non-critical issues (file changes during development)
- INFO: Used for normal operations and request logging
