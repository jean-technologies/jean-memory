# OAuth Bridge Testing Guide - Jean Memory MCP

**Date:** July 31, 2025  
**Status:** Ready for Deployment Testing

## Quick Start: Deploy & Test in 15 Minutes

### Step 1: Deploy Bridge Page (5 minutes)

**Upload `oauth-bridge.html` to your main website hosting:**

1. **Find where jeanmemory.com is hosted** (Vercel/Netlify/etc.)
2. **Upload the file** `oauth-bridge.html` to the root directory
3. **Verify accessibility** at: `https://jeanmemory.com/oauth-bridge.html`

### Step 2: Update Supabase Configuration (2 minutes)

1. **Go to Supabase Dashboard** → Your Project → Authentication → URL Configuration
2. **Update Site URL** from:
   ```
   OLD: https://jeanmemory.com
   NEW: https://jeanmemory.com/oauth-bridge.html
   ```
3. **Click "Save changes"**

### Step 3: Test OAuth Bridge Locally (3 minutes)

**Test bridge page functionality:**

1. **Open in browser:** `https://jeanmemory.com/oauth-bridge.html`
2. **Check console logs** - should show "OAuth Bridge loaded"
3. **Test with OAuth parameters:**
   ```
   https://jeanmemory.com/oauth-bridge.html?oauth_session=test123&code=abc
   ```
4. **Expected behavior:** Should redirect to API callback with parameters preserved

### Step 4: Test Claude Web MCP Connection (5 minutes)

1. **Open Claude Web** → Settings → Features → MCP Servers
2. **Add new server:**
   ```
   Server URL: https://jean-memory-api-virginia.onrender.com/mcp
   Authentication: OAuth 2.1
   ```
3. **Click "Connect"** 
4. **Expected flow:**
   - Redirect to OAuth login page
   - Login with Google/existing account
   - Brief redirect through bridge page
   - Return to Claude with connection established

## Detailed Testing Steps

### Pre-Deployment Verification

**Check current Supabase config:**
```
Current Site URL: https://jeanmemory.com ✅
Additional Redirect URLs: [your current list] ✅
Bridge file ready: oauth-bridge.html ✅
```

### Bridge Page Testing

**Test 1: Basic Page Load**
```bash
# Should return 200 OK with HTML content
curl -I https://jeanmemory.com/oauth-bridge.html
```

**Test 2: OAuth Parameter Detection**
Visit with different parameter types:
```
# Test OAuth session parameter
https://jeanmemory.com/oauth-bridge.html?oauth_session=test123

# Test authorization code
https://jeanmemory.com/oauth-bridge.html?code=abc123&state=xyz

# Test access token (fragment)
https://jeanmemory.com/oauth-bridge.html#access_token=token123
```

**Expected console output:**
```javascript
🌉 OAuth Bridge loaded
URL params: {oauth_session: "test123"}
🔄 OAuth callback detected, redirecting to API...
🎯 Redirecting to: https://jean-memory-api-virginia.onrender.com/oauth/callback?oauth_session=test123
```

### End-to-End OAuth Flow Testing

**Test 3: Complete OAuth Flow**

1. **Start Claude Web MCP connection**
2. **Monitor network traffic** in browser DevTools
3. **Expected requests:**
   ```
   1. GET /.well-known/oauth-authorization-server → 200 OK
   2. POST /oauth/register → 200 OK  
   3. GET /oauth/authorize → 302 redirect to Supabase
   4. Supabase OAuth → redirect to bridge page
   5. Bridge redirect → GET /oauth/callback → API processes session
   6. GET /oauth/callback → 302 redirect to Claude
   7. POST /oauth/token → 200 OK (JWT token)
   8. POST /mcp (initialize) → 200 OK with mcp-session-id header
   ```

**Test 4: Connection Persistence**
- **Claude UI should show:** "Connected" status with green indicator
- **Tools should be available:** Jean Memory tools in Claude sidebar
- **MCP requests should work:** Try asking about memories/prompts

## Troubleshooting

### Issue: Bridge Page 404
**Problem:** `https://jeanmemory.com/oauth-bridge.html` returns 404
**Solution:** Ensure file uploaded to correct directory on hosting platform

### Issue: Infinite Redirect Loop  
**Problem:** Page keeps redirecting
**Solution:** Check console logs - may be detecting false OAuth parameters

### Issue: Main App Users Affected
**Problem:** Normal users hitting bridge page
**Solution:** Bridge auto-redirects to main app after 2s if no OAuth params

### Issue: OAuth Still Goes to Main App
**Problem:** Supabase Site URL not updated properly
**Solution:** Verify Site URL is exactly: `https://jeanmemory.com/oauth-bridge.html`

## Success Criteria

### ✅ Bridge Deployment Success
- [ ] Bridge page loads at `https://jeanmemory.com/oauth-bridge.html`
- [ ] Console shows OAuth detection working
- [ ] Parameter preservation functional
- [ ] Redirect to API callback working

### ✅ Supabase Configuration Success  
- [ ] Site URL updated to bridge page
- [ ] OAuth flows redirect to bridge (not main app)
- [ ] Existing users unaffected

### ✅ Claude Web MCP Success
- [ ] Connection shows "Connected" status
- [ ] Jean Memory tools available in sidebar
- [ ] MCP requests processed successfully
- [ ] Session persistence working

## Rollback Plan

**If anything breaks:**

1. **Revert Supabase Site URL** back to: `https://jeanmemory.com`
2. **Remove bridge page** from hosting
3. **System returns to previous state** (OAuth broken but main app working)

## Monitoring

**After deployment, monitor:**
- **API logs** for OAuth callback requests
- **Bridge page** console logs for parameter detection  
- **User reports** of any main app access issues
- **Claude Web** connection success rate

## Expected Timeline

- **Deploy bridge:** 5 minutes
- **Update Supabase:** 2 minutes  
- **Test locally:** 3 minutes
- **Test Claude Web:** 5 minutes
- **Total time:** 15 minutes

**Result:** Working Claude Web MCP connection with Jean Memory tools accessible.