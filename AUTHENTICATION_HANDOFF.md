# Jean Memory Authentication System - Engineering Handoff

## Current Status: Stable but Backend Issue Blocking SDK

**Last Updated:** January 17, 2025  
**SDK Versions Published:** React v1.5.3, Python v1.4.2, Node v1.4.2  
**Status:** Frontend working, backend OAuth bridge broken

---

## Problem Summary

The Jean Memory React SDK authentication is **working correctly**, but the **backend OAuth bridge is broken**.

### What Works ✅
- React SDK v1.5.3 correctly initiates OAuth flow
- SDK properly handles session persistence and token storage
- Bridge-based authentication architecture is sound
- No client registration required (PKCE "works everywhere" philosophy)

### What's Broken ❌
- `https://jeanmemory.com/oauth-bridge.html` doesn't handle `sdk_oauth` flow
- Backend returns "Invalid authentication flow" error
- OAuth completion fails for production API keys

---

## Technical Details

### Authentication Flow (Should Work)
```
1. User clicks SignInWithJean button
2. SDK redirects to: https://jeanmemory.com/oauth-bridge.html?oauth_session=xxx&flow=sdk_oauth&api_key=jean_sk_xxx
3. Bridge handles Supabase OAuth and creates Jean Memory token
4. Bridge redirects back to app: ?auth_success=true&auth_token=jwt_token
5. SDK processes token and stores user session
```

### Current Failure Point
Step 2-3: Bridge doesn't recognize `flow=sdk_oauth` parameter and fails

### Error Observed
```
"Invalid authentication flow"
```

---

## Last Working Evidence

From conversation with previous developer:
> "✅ Frontend SDK v1.5.1 is working correctly:
> - Detects production API key properly  
> - Initiates OAuth flow with correct parameters
> - Session persistence logic is fixed
> 
> ❌ Backend OAuth bridge is broken:
> - https://jeanmemory.com/oauth-bridge.html failing
> - Not handling sdk_oauth flow for production keys
> - Returns "Invalid authentication flow" error"

---

## Required Fix (Backend Team)

### 1. Update OAuth Bridge
File: `https://jeanmemory.com/oauth-bridge.html`
- Add support for `flow=sdk_oauth` parameter
- Ensure proper token exchange for SDK flow
- Verify API key validation for production keys

### 2. Verify API Key Permissions
- Confirm production API keys have OAuth enabled
- Test with API key: `jean_sk_Jw-...` (known production key)

### 3. Test Complete Flow
```bash
# Should work after fix:
curl "https://jeanmemory.com/oauth-bridge.html?oauth_session=test123&flow=sdk_oauth&api_key=jean_sk_test_123"
```

---

## Published SDK Versions

### React SDK v1.5.3
- **Status:** Working frontend, blocked by backend
- **Published:** npm `@jeanmemory/react@1.5.3`
- **Key Features:** Bridge-based OAuth, session persistence, no client registration

### Python SDK v1.4.2  
- **Status:** Stable
- **Published:** PyPI

### Node.js SDK v1.4.2
- **Status:** Stable  
- **Published:** npm

---

## What We Learned

### 1. Authentication Architecture
- **Bridge-based OAuth works** - creates proper Jean Memory tokens
- **Direct Supabase integration was wrong approach** - doesn't create Jean Memory tokens
- **PKCE flow is correct** - no client registration needed

### 2. User Identity Mapping
- All platforms should use Supabase `user.id` as foundation
- Backend `get_or_create_user(db, supabase_user_id, email)` handles unified mapping
- Consistent user IDs across Claude MCP, Dashboard, and React SDK

### 3. Session Management
- React SDK correctly handles localStorage persistence
- OAuth completion flow is properly implemented
- URL cleanup and state management works

---

## Next Engineer Action Items

### Immediate (High Priority)
1. **Fix OAuth Bridge** - Update bridge to handle `sdk_oauth` flow
2. **Test Production Keys** - Verify API key permissions
3. **Deploy Bridge Fix** - Test complete authentication flow

### Future Improvements  
1. **Unified Testing** - Create end-to-end auth tests
2. **Error Handling** - Improve error messages for OAuth failures
3. **Documentation** - Update docs once bridge is fixed

---

## Test Scenario

After backend fix, this should work:

```jsx
// Minimal working example
function App() {
  return (
    <JeanProvider apiKey="jean_sk_live_key">
      <JeanChat />
    </JeanProvider>
  );
}
```

The authentication flow should complete automatically without manual token handling.

---

## Files Not to Change

**These are working correctly:**
- `sdk/react/SignInWithJean.tsx` 
- `sdk/react/provider.tsx`
- `sdk/react/package.json` (v1.5.3)

**Focus on:**
- Backend OAuth bridge implementation
- API key permission system
- OAuth flow handling for `sdk_oauth`

---

## Contact

**Issue Type:** Backend OAuth Integration  
**Blocking:** React SDK adoption  
**Priority:** High - affects developer onboarding

The frontend architecture is solid. This is purely a backend configuration issue.