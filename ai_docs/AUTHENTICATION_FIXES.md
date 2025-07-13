# Authentication & Permissions System

## Current State

The 82ndrop application uses Firebase Authentication with proper audience claims and custom claims for access control.

### Core Components

1. **Firebase Authentication**

   - Google Sign-In as primary auth method
   - Proper audience claim: "taajirah"
   - Custom claims for access control
   - Token refresh handling

2. **Backend Middleware**

   - Firebase ID token validation
   - Audience claim verification
   - Custom claims checking
   - Error handling for auth failures

3. **Frontend Services**
   - AuthService for token management
   - AuthGuard for route protection
   - Access-pending flow for new users
   - Token refresh mechanism

## Authentication Flow

1. **User Signs In**

   ```typescript
   // frontend/src/app/services/auth.service.ts
   async signInWithGoogle() {
     const userCredential = await signInWithPopup(this.auth, this.googleProvider);
     await this.handlePostSignIn(userCredential.user);
   }
   ```

2. **Token Validation**

   ```python
   # main.py
   try:
       decoded_token = auth.verify_id_token(token)
       if decoded_token['aud'] != 'taajirah':
           raise ValueError("Invalid audience claim")
   except Exception as e:
       raise HTTPException(status_code=401, detail=str(e))
   ```

3. **Access Control**
   ```typescript
   // frontend/src/app/guards/auth.guard.ts
   canActivate(): Observable<boolean> {
     return this.authService.user$.pipe(
       map(user => {
         if (!user) {
           this.router.navigate(['/login']);
           return false;
         }
         if (!user.hasAgentAccess) {
           this.router.navigate(['/access-pending']);
           return false;
         }
         return true;
       })
     );
   }
   ```

## Custom Claims Structure

```json
{
  "agent_access": true,
  "access_level": "basic|premium|admin",
  "agent_permissions": {
    "82ndrop": true,
    "video_prompts": true,
    "search_agent": false,
    "guide_agent": true,
    "prompt_writer": true
  }
}
```

## Access Levels

1. **Basic Access**

   - Guide Agent usage
   - Prompt Writer access
   - Basic video prompts

2. **Premium Access**

   - All Basic features
   - Search Agent access
   - Advanced prompt features

3. **Admin Access**
   - All Premium features
   - User management
   - Analytics access

## Common Issues & Solutions

### 1. Token Audience Mismatch

**Problem**: Firebase ID token has incorrect "aud" claim
**Solution**: Ensure token audience is "taajirah"

```typescript
// frontend/src/environments/environment.ts
export const environment = {
  firebase: {
    // ...other config
    authDomain: "taajirah.firebaseapp.com",
  },
};
```

### 2. Claims Propagation Delay

**Problem**: New claims not immediately available
**Solution**: Force token refresh

```typescript
// frontend/src/app/services/auth.service.ts
async refreshUserToken(): Promise<void> {
  const user = this.auth.currentUser;
  if (user) {
    await user.getIdToken(true);
  }
}
```

### 3. Access Pending State

**Problem**: Users stuck in access-pending state
**Solution**: Implement auto-grant access

```typescript
// functions/auto-grant-access.js
exports.autoGrantAccess = functions.auth.user().onCreate(async (user) => {
  await admin.auth().setCustomUserClaims(user.uid, {
    agent_access: true,
    access_level: "basic",
    agent_permissions: {
      "82ndrop": true,
      video_prompts: true,
      guide_agent: true,
      prompt_writer: true,
    },
  });
});
```

## Security Best Practices

1. **Token Validation**

   - Always verify tokens server-side
   - Check audience claim
   - Validate custom claims
   - Handle errors gracefully

2. **Access Control**

   - Use role-based permissions
   - Implement proper guards
   - Check permissions server-side
   - Log authentication events

3. **Error Handling**
   - Return proper HTTP status codes
   - Provide meaningful error messages
   - Log authentication failures
   - Implement rate limiting

## Testing

### Local Testing

```bash
# Test with curl
curl -X POST http://localhost:8000/run \
  -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Production Testing

1. Get real Firebase token from browser
2. Test API endpoints with token
3. Verify proper error handling
4. Check claims propagation

## Deployment Considerations

1. **Environment Variables**

   - Use proper Firebase project IDs
   - Set correct audience claims
   - Configure service accounts

2. **CI/CD Pipeline**

   - Test authentication in staging
   - Verify token validation
   - Check claims handling

3. **Monitoring**
   - Log authentication events
   - Track failed attempts
   - Monitor token refreshes

## Firebase Authentication Configuration

### Current Setup

- Project: Taajirah
- Required Audience Claim: `taajirah`
- Service Account: `taajirah-agents-service-account.json`

### Important Changes

- Audience claim has been updated from `taajirah-agents` to `taajirah`
- Service account initialization happens at application startup
- Token verification is strictly enforced for all protected endpoints

### Common Issues and Solutions

1. Incorrect Audience Claim

```
Error: Firebase ID token has incorrect "aud" (audience) claim.
Expected "taajirah" but got "taajirah-agents"
```

**Solution**: Ensure your Firebase configuration is using the correct project and audience claim.

2. Token Verification Failures

- Check if token is properly formatted
- Verify token is not expired
- Ensure token comes from the correct Firebase project

### Implementation Details

1. Server Initialization

```python
# Service account loading
Loading service account from: /path/to/taajirah-agents-service-account.json
Firebase initialized with service account
```

2. Protected Endpoints

- All video status endpoints require authentication
- Token must be passed in Authorization header with Bearer prefix
- 401 Unauthorized responses include detailed error messages for debugging

### Testing Authentication

1. Local Development

- Use real Firebase tokens from authenticated users
- Include token in Authorization header: `Bearer <token>`
- Test both successful and failed authentication scenarios

2. Common Response Codes

- 200 OK: Successful authentication
- 401 Unauthorized: Authentication failed
- 403 Forbidden: Insufficient permissions

### Security Best Practices

1. Never expose service account credentials
2. Always use HTTPS for token transmission
3. Implement proper token refresh mechanisms
4. Monitor and log authentication failures
5. Regular rotation of service account keys
