# 🧪 OAuth Minimal Test Plan - Don't Break Claude!

**Date:** August 15, 2025  
**Goal:** Fix React SDK OAuth without breaking existing Claude OAuth  
**Status:** ⚠️ INVESTIGATION MODE - Test Before Making Changes

---

## 🔍 **Current State Analysis**

### ✅ **What's Working (DON'T BREAK):**
- **Claude OAuth**: Uses bridge pattern at `https://jeanmemory.com/oauth-bridge.html`
- **Supabase Site URL**: Already set to `https://jeanmemory.com/oauth-bridge.html`
- **Main OAuth system**: `/oauth/authorize` handles Claude flows via bridge

### ❓ **What's Unknown:**
- **SDK OAuth flow**: `/sdk/oauth/authorize` → forwards to → `/oauth/authorize` 
- **localhost:3005 support**: Should be auto-registered by dynamic validation
- **Bridge interference**: Does the bridge pattern block direct localhost flows?

---

## 📋 **Test Plan (10 Minutes)**

### **Test 1: Verify Current OAuth Setup (2 min)**

**Check if main OAuth system is accessible:**
```bash
# Test 1A: Main OAuth discovery
curl -I https://jean-memory-api-virginia.onrender.com/oauth/.well-known/oauth-authorization-server

# Test 1B: SDK OAuth forwards properly  
curl -I https://jean-memory-api-virginia.onrender.com/sdk/oauth/authorize?test=1
```

**Expected:** Both should return 200 OK, not 404

### **Test 2: Verify Bridge Pattern Still Works (2 min)**

**Test Claude OAuth flow:**
```bash
# Check bridge page exists and works
curl -I https://jeanmemory.com/oauth-bridge.html

# Check MCP OAuth callback
curl -I https://jean-memory-api-virginia.onrender.com/oauth/auth-redirect?flow=mcp_oauth
```

**Expected:** Bridge page loads, MCP callback exists

### **Test 3: Test React SDK v1.2.12 (5 min)**

**Install latest SDK and test:**
```bash
npm install @jeanmemory/react@1.2.12
```

**Create minimal test:**
```jsx
import { JeanProvider, JeanChat } from '@jeanmemory/react';

// Test 1: Test API key (should work)
<JeanProvider apiKey="jean_sk_test_demo_key_for_ui_testing">
  <JeanChat />
</JeanProvider>

// Test 2: Production API key (currently broken)
<JeanProvider apiKey="jean_sk_live_your_production_key">
  <JeanChat />
</JeanProvider>
```

**Run on localhost:3005 and check:**
1. **Test key**: Should auto-initialize test user ✅
2. **Production key**: Should show "Sign In" button
3. **Click Sign In**: Check console for the exact error

---

## 🔧 **Expected Findings**

### **Scenario A: OAuth Endpoint Missing (Most Likely)**
**Console Error:** `GET /sdk/oauth/authorize 404`  
**Cause:** Backend deployment didn't include SDK OAuth router  
**Fix:** Verify deployment, check logs

### **Scenario B: Redirect URI Rejected**
**Console Error:** `GET /oauth/authorize 400 - Invalid redirect URI`  
**Cause:** localhost:3005 not in allowed list  
**Fix:** Backend auto-registration not working

### **Scenario C: Bridge Pattern Conflict**
**Console Error:** Bridge page loads but can't handle SDK flows  
**Cause:** Bridge only handles MCP flows, not SDK flows  
**Fix:** Extend bridge or create separate SDK OAuth flow

---

## 🚨 **Safety Checks**

### **Before Any Changes:**
1. ✅ **Verify Claude OAuth still works** (test in Claude Desktop)
2. ✅ **Verify main app login still works** (test at jeanmemory.com)
3. ✅ **Check Supabase Site URL unchanged** (`oauth-bridge.html`)

### **After Any Changes:**
1. ✅ **Re-test Claude OAuth** (most important!)
2. ✅ **Re-test main app login**
3. ✅ **Test React SDK OAuth**

---

## 📞 **What to Tell the Dev**

### **Immediate Testing (5 minutes):**

1. **Update SDK:** `npm install @jeanmemory/react@1.2.12`

2. **Test Setup:**
   ```jsx
   // Test with production API key on localhost:3005
   <JeanProvider apiKey="jean_sk_live_your_production_key">
     <JeanChat />
   </JeanProvider>
   ```

3. **Click "Sign In" and report:**
   - **Exact console error message**
   - **Network tab:** Which URL returns 404?
   - **Does it redirect anywhere or just fail immediately?**

### **Key Questions:**
- Does `/sdk/oauth/authorize` return 404 or redirect to `/oauth/authorize`?
- Does `/oauth/authorize` return 404 or some other error?
- What's the exact redirect URI being used?

### **If You Want to Test Bridge Extension:**
```jsx
// Try this - forces bridge pattern for SDK
const signInUrl = 'https://jean-memory-api-virginia.onrender.com/oauth/authorize?response_type=code&client_id=test&redirect_uri=https://jeanmemory.com/oauth-bridge.html&final_redirect=' + encodeURIComponent(window.location.href);
window.location.href = signInUrl;
```

---

## 🎯 **Success Criteria**

### **Minimal Success:**
- ✅ React SDK OAuth works on localhost:3005
- ✅ Claude OAuth still works (bridge pattern intact)
- ✅ Main app login still works

### **Optimal Success:**
- ✅ React SDK works on ALL localhost ports
- ✅ No breaking changes to existing flows
- ✅ Clear documentation of OAuth flows

---

## 🔄 **Quick Rollback Plan**

**If anything breaks:**
1. **Revert React SDK:** Use previous working version
2. **Revert backend:** Git revert to previous OAuth configuration
3. **Keep Supabase unchanged:** Don't touch Site URL (`oauth-bridge.html`)

**The existing Claude OAuth setup works, so don't change the bridge pattern unless absolutely necessary!**

---

*Test first, understand the problem, then fix minimally. The bridge pattern took effort to implement and shouldn't be changed unless it's definitely the issue.*