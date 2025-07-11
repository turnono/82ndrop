# CORS Fix Documentation

## Problem

ADK 1.5.0 has a bug where OPTIONS requests (CORS preflight) return 405 "Method Not Allowed" instead of proper CORS headers. This prevents browsers from making authenticated requests to session endpoints.

## Error Symptoms

```
Access to XMLHttpRequest at 'https://drop-agent-service-855515190257.us-central1.run.app/apps/drop_agent/users/.../sessions'
from origin 'https://82ndrop.web.app' has been blocked by CORS policy:
Response to preflight request doesn't pass access control check:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Solution

Added a custom OPTIONS handler in `main.py` to work around the ADK bug:

```python
# Custom OPTIONS handler to fix ADK CORS bug
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests for CORS preflight"""
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        return JSONResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Max-Age": "86400",
            }
        )
    return JSONResponse(status_code=400, content={"detail": "Origin not allowed"})
```

## Deployment Commands

### ✅ Use These Commands (Firebase Authentication + CORS Fix)

- **`make deploy-gcloud`** - For development/testing deployments
- **`make deploy-production`** - For production deployments

Both include the CORS fix and use Firebase authentication.

### ❌ Don't Use These Commands (ADK Authentication)

- **`make deploy`** - Uses ADK authentication (not compatible with our Firebase setup)
- **`make deploy-include-vertex-session-storage`** - Uses ADK authentication

## Testing the Fix

Test CORS preflight with:

```bash
curl -X OPTIONS \
  -H "Origin: https://82ndrop.web.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  -v https://drop-agent-service-855515190257.us-central1.run.app/apps/drop_agent/users/test/sessions
```

**Expected Response:**

```
HTTP/2 200
access-control-allow-origin: https://82ndrop.web.app
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-allow-headers: Authorization,Content-Type
```

## Allowed Origins

The following origins are allowed for CORS:

```python
ALLOWED_ORIGINS = [
    "https://82ndrop.web.app",      # Production frontend
    "http://localhost:4200",         # Local development
    "http://localhost:8080",         # Local development
    "http://localhost"               # Local development
]
```

## Frontend Integration

The frontend should now be able to:

1. ✅ Create sessions via POST to `/apps/drop_agent/users/{userId}/sessions`
2. ✅ Send messages via POST to `/run`
3. ✅ Use Server-Sent Events via `/run_sse`
4. ✅ Include Authorization headers with Firebase ID tokens

## Troubleshooting

### If CORS errors persist:

1. **Clear browser cache** - CORS errors can be cached
2. **Check deployment** - Ensure you used `make deploy-gcloud` or `make deploy-production`
3. **Verify origin** - Check that your frontend origin is in `ALLOWED_ORIGINS`
4. **Test with curl** - Use the curl command above to verify the fix is deployed

### If authentication errors occur:

1. **Check Firebase token** - Ensure the user has `agent_access` custom claim
2. **Verify service account** - Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set
3. **Check logs** - Use `make logs` to view Cloud Run logs

## Future Considerations

- This is a workaround for ADK 1.5.0 bug
- When ADK is updated, this custom handler may be removed
- Monitor ADK releases for CORS fixes
- Consider reporting this issue to ADK maintainers

## Related Files

- `main.py` - Contains the CORS fix
- `makefile` - Updated with deployment documentation
- `frontend/src/app/services/agent.service.ts` - Frontend API calls
- `ai_docs/CORS_FIX_DOCUMENTATION.md` - This documentation
