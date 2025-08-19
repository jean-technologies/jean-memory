# SDK Authentication Fix - Update for Dev Team

**Date:** December 18, 2024  
**Status:** ✅ FIXED AND DEPLOYED  
**Version:** All SDKs at v1.9.0

---

## 🔥 The Problem We Fixed

The React SDK was using the **OLD Supabase OAuth bridge** instead of the **NEW Universal OAuth 2.1 system**. This caused a complete disconnect between what was documented and what was actually happening.

### What Was Broken:
- React SDK v1.8.7 was redirecting to `https://jeanmemory.com/oauth-bridge.html` 
- This used Supabase tokens instead of Jean Memory JWT tokens
- User IDs were inconsistent across applications
- The documented flow in `authentication.mdx` didn't match reality

---

## ✅ What We Fixed

### 1. **React SDK Now Uses Universal OAuth 2.1**
```javascript
// OLD (BROKEN):
const bridgeUrl = `https://jeanmemory.com/oauth-bridge.html?oauth_session=${sessionId}`;

// NEW (FIXED):
await initiateOAuth({ 
  apiKey,
  redirectUri: window.location.origin + window.location.pathname
});
// Now correctly hits: /v1/sdk/oauth/authorize
```

### 2. **Removed All Supabase Dependencies**
- Deleted Supabase client initialization
- Removed Supabase session management
- Now uses pure OAuth 2.1 PKCE flow

### 3. **Unified User Interface**
```typescript
// All SDKs now use this consistent interface:
interface JeanUser {
  user_id: string;  // NOT 'id' or 'sub'
  email: string;
  name?: string;
  access_token: string;
}
```

### 4. **Version Alignment**
All SDKs are now at **v1.9.0**:
- `@jeanmemory/react@1.9.0` ✅
- `@jeanmemory/node@1.9.0` ✅
- `jeanmemory@1.9.0` (Python) ✅

---

## 🧪 Testing Instructions

### For React Apps:

1. **Update to latest SDK:**
```bash
npm install @jeanmemory/react@1.9.0
```

2. **Test the authentication flow:**
```jsx
import { JeanProvider, SignInWithJean, useJean } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_api_key">
      <SignInWithJean onSuccess={(user) => {
        console.log('✅ Authenticated:', user);
        // Should see: { user_id: "...", email: "...", access_token: "..." }
      }}>
        Sign In with Jean
      </SignInWithJean>
    </JeanProvider>
  );
}
```

3. **Verify the OAuth flow:**
   - Click "Sign In with Jean"
   - Should redirect to Google OAuth (NOT Supabase)
   - Should return with JWT token (check Network tab)
   - Token should work with API calls

### For Node.js Apps:

```javascript
const { JeanMemoryClient } = require('@jeanmemory/node');

const client = new JeanMemoryClient({ 
  apiKey: 'jean_sk_your_api_key' 
});

// Test OAuth flow
const auth = client.createAuth();
const user = await auth.authenticate();
console.log('✅ User:', user);
```

### For Python Apps:

```python
from jean_memory import JeanMemoryClient

client = JeanMemoryClient(api_key="jean_sk_your_api_key")

# Test with OAuth token
response = client.get_context(
    user_token="oauth_token_from_frontend",
    message="What did I work on yesterday?"
)
print(response.text)
```

---

## 🔍 What to Look For

### ✅ GOOD Signs:
1. OAuth redirects to `/v1/sdk/oauth/authorize`
2. JWT tokens have format: `eyJ...` (not Supabase tokens)
3. Same email = same user_id across all apps
4. API calls work with the token

### ❌ BAD Signs (Should NOT happen):
1. Redirects to `oauth-bridge.html`
2. Seeing Supabase in network requests
3. Different user_ids for same email
4. Token validation failures

---

## 📊 Key Changes Made

### Files Modified:
- `sdk/react/provider.tsx` - Removed Supabase, added Universal OAuth
- `sdk/react/oauth.ts` - Fixed user interface, improved session handling
- `sdk/react/config.ts` - Removed Supabase config, added OAuth endpoints
- All `package.json` / `setup.py` - Version 1.9.0

### Git Commit:
```
c3fd54d0 - fix: Update React SDK to use Universal OAuth 2.1 instead of Supabase bridge
```

---

## 🚨 Breaking Changes

**For React SDK users upgrading from < 1.9.0:**

1. **JeanUser interface changed:**
   - Old: `id`, `sub` properties
   - New: `user_id` property

2. **No more Supabase:**
   - Remove any Supabase environment variables
   - Remove Supabase client code

3. **OAuth flow changed:**
   - Now uses backend Universal OAuth
   - No client-side Supabase needed

---

## 💡 Next Steps

1. **Test in your development environment**
2. **Update any production apps to v1.9.0**
3. **Report any issues immediately**
4. **Update your local documentation if needed**

---

## 📞 Support

If you encounter ANY issues:
1. Check the browser console for errors
2. Check Network tab for failed requests
3. Verify you're using v1.9.0: `npm list @jeanmemory/react`
4. Report with full error details

---

**Bottom Line:** This should work now. The React SDK finally uses the same Universal OAuth 2.1 system as our backend, exactly as documented. Test it and let us know! 🚀