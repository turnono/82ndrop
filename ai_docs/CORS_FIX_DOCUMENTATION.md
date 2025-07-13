# CORS Fix Documentation

## CORS Configuration

### Allowed Origins

#### Production Environment

- Frontend: `https://82ndrop.web.app`
- Staging: `https://82ndrop-staging.web.app`

#### Development Environment

- Local Frontend: `http://localhost:4200` (Angular default)
- Local Backend: `http://127.0.0.1:8000` (Uvicorn default)

### Backend CORS Setup

The backend service (running on Cloud Run) is configured to accept requests from the following origins:

```python
origins = [
    "https://82ndrop.web.app",
    "https://82ndrop-staging.web.app",
    "http://localhost:4200",
    "http://127.0.0.1:4200"
]
```

### Security Headers

All responses include the following security headers:

- `Access-Control-Allow-Credentials: true`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Authorization, Content-Type`

### Common CORS Issues

1. Development Environment

- Ensure local Angular development server runs on port 4200
- Backend Uvicorn server should run on port 8000
- Check that both origins are properly configured in CORS middleware

2. Production Environment

- Verify Firebase hosting domains are whitelisted
- Ensure all API requests use HTTPS
- Check for any subdomain variations

### Testing CORS Configuration

1. Local Development

```bash
# Start backend server
uvicorn main:app --reload --port 8000

# In another terminal, start Angular dev server
cd frontend
ng serve
```

2. Verify CORS Headers

```bash
curl -I -H "Origin: http://localhost:4200" \
  http://127.0.0.1:8000/video-status/123
```

### Troubleshooting

1. CORS Preflight Failures

- Check if OPTIONS requests are being handled
- Verify all required headers are included
- Ensure origin matches exactly (including protocol and port)

2. Authentication Issues

- Confirm Authorization header is in allowed headers list
- Check for proper token format in requests
- Verify CORS configuration doesn't interfere with auth

3. Production Issues

- Validate SSL certificates
- Check for proper domain configuration
- Ensure all services use HTTPS in production
