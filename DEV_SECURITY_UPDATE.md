# 🚨 CRITICAL SECURITY UPDATE - SDK v1.9.1

**Priority:** HIGH  
**Action Required:** Update immediately  
**Affects:** All applications using Jean Memory SDKs

---

## 🔥 What Changed (Breaking Changes)

### 1. **Removed user_id from Client Interface**
```typescript
// ❌ OLD (v1.9.0 and below):
interface JeanUser {
  user_id: string;    // ← REMOVED for security
  email: string;
  name?: string;
  access_token: string;
}

// ✅ NEW (v1.9.1):
interface JeanUser {
  email: string;      // ← Only client-safe fields
  name?: string;
  access_token: string;
}
```

**Why:** Applications should NOT have access to internal user IDs. The user_id is now extracted server-side from the JWT token.

### 2. **Fixed Authentication Headers**
```http
❌ OLD (Wrong):
Authorization: Bearer jean_sk_api_key

✅ NEW (Correct):
Authorization: Bearer <user_jwt_token>
X-API-Key: jean_sk_your_app_key
```

**Why:** This follows OAuth 2.1 best practices and properly separates user authentication from application identification.

---

## 🚀 How to Update Your App

### Step 1: Install Latest SDK
```bash
npm install @jeanmemory/react@1.9.1
```

### Step 2: Update Your Code
```typescript
// ✅ This still works (no changes needed):
import { JeanProvider, SignInWithJean, useJean } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_api_key">
      <SignInWithJean onSuccess={(user) => {
        // ✅ user.email and user.name still available
        // ❌ user.user_id no longer exists
        console.log('User:', user.email, user.name);
      }}>
        Sign In with Jean
      </SignInWithJean>
    </JeanProvider>
  );
}
```

### Step 3: Remove Any user_id References
```typescript
// ❌ Remove code like this:
const userId = user.user_id;  // Will cause TypeScript error

// ✅ Use email for display purposes:
const userDisplay = user.email || user.name || 'User';
```

---

## 🧪 Testing Your Update

### 1. **Check Authentication Flow**
- User clicks "Sign In with Jean"
- Should redirect to Google OAuth (not Supabase)
- Should return with JWT token
- Console should show user object with `email`, `name`, `access_token` only

### 2. **Check Network Requests**
Open browser DevTools → Network tab:
```http
✅ Should see:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-API-Key: jean_sk_your_api_key

❌ Should NOT see:
Authorization: Bearer jean_sk_your_api_key
```

### 3. **Test Chat Functionality**
- Try sending a message: "What did I work on yesterday?"
- Should work normally
- Response should contain relevant memories

---

## 🔍 Troubleshooting

### Problem: TypeScript errors about user_id
**Solution:** Remove all references to `user.user_id` in your code

### Problem: Authentication not working
**Check:**
1. Using SDK v1.9.1: `npm list @jeanmemory/react`
2. No console errors about CORS
3. Network requests show JWT tokens, not API keys

### Problem: User data missing
**Note:** Only `email`, `name`, and `access_token` are now available. If you need user identification, use `user.email`.

---

## 🔒 Security Benefits

### What This Fixes:
1. **No Internal ID Leakage**: Apps can't access internal user IDs
2. **Proper OAuth Flow**: JWT tokens authenticate users, API keys identify apps
3. **Better Privacy**: User identity handled server-side only
4. **Standards Compliant**: Follows OAuth 2.1 best practices

### Two-Layer Security:
```
🔑 Layer 1: Application (API Key)
   - Identifies your app to Jean Memory
   - Handles billing and permissions
   
👤 Layer 2: User (JWT Token)  
   - Identifies the specific user
   - Accesses their personal memories
```

---

## 📞 Need Help?

### If You See Issues:
1. **Clear browser cache/localStorage**
2. **Check you're using v1.9.1**: `npm list @jeanmemory/react`
3. **Look for console errors** and report them
4. **Check Network tab** for failed requests

### Report Problems:
Include this info:
- SDK version: `npm list @jeanmemory/react`  
- Console errors (screenshot)
- Network requests (screenshot)
- What you were trying to do

---

## ⏰ Timeline

- **Now**: Update to v1.9.1 immediately
- **Testing**: Verify auth flow works correctly  
- **Production**: Deploy when testing passes

**This is a security fix that should be deployed ASAP.** The old versions had authentication header issues that could cause problems.

---

## 📋 Checklist

- [ ] Updated to SDK v1.9.1
- [ ] Removed any `user.user_id` references  
- [ ] Tested authentication flow
- [ ] Verified network requests show JWT tokens
- [ ] Tested chat functionality
- [ ] Ready for production deployment

**Bottom line:** Update to v1.9.1, remove `user_id` references, test auth flow. Everything else should work the same but more securely! 🔐