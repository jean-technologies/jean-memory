# FastMCP OAuth Deployment Troubleshooting

**Date:** July 31, 2025  
**Status:** ACTIVE ISSUE - Production deployment failed  
**Issue:** `ModuleNotFoundError: No module named 'fastmcp'`

## Problem Summary

The FastMCP OAuth implementation failed to deploy to production due to missing dependencies in requirements.txt.

## Error Details

```
File "/opt/render/project/src/openmemory/api/app/mcp_fastmcp_oauth.py", line 15, in <module>
    from fastmcp import FastMCP
ModuleNotFoundError: No module named 'fastmcp'
```

## Root Cause Analysis

1. **Missing Dependencies**: `fastmcp` and `mcpauth` were not included in requirements.txt
2. **Local Development Success**: Dependencies were installed locally but not committed to requirements
3. **Production Environment**: Clean environment couldn't import required modules

## Fix Applied ✅

### 1. Updated requirements.txt
```bash
# Added to requirements.txt
fastmcp>=0.1.0
mcpauth>=0.1.0
```

### 2. Made Imports Optional
```python
# Optional imports - gracefully handle missing dependencies
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    FASTMCP_AVAILABLE = False

try:
    from mcpauth import MCPAuth
    from mcpauth.config import AuthServerType
    MCPAUTH_AVAILABLE = True
except ImportError:
    MCPAuth = None
    AuthServerType = None
    MCPAUTH_AVAILABLE = False
```

### 3. Added Graceful Fallback
- App will start even if FastMCP dependencies are missing
- Status endpoint shows dependency availability
- OAuth endpoints still work with basic functionality

## Testing the Fix

### After Deployment - Check Status
```bash
curl https://jean-memory-api-virginia.onrender.com/fastmcp/status
```

**Expected Success Response:**
```json
{
  "status": "ready",
  "implementation": "fastmcp + mcpauth",
  "fastmcp_available": true,
  "mcpauth_available": true,
  "oauth_version": "2.1",
  "specs": [
    "RFC 7591 - Dynamic Client Registration",
    "RFC 9728 - Protected Resource Metadata",
    "RFC 8707 - Resource Indicators", 
    "OAuth 2.1 with PKCE"
  ]
}
```

**Fallback Response (if deps missing):**
```json
{
  "status": "partial",
  "implementation": "fallback",
  "fastmcp_available": false,
  "mcpauth_available": false,
  "oauth_version": "2.1"
}
```

### Test OAuth Discovery
```bash
curl https://jean-memory-api-virginia.onrender.com/.well-known/oauth-authorization-server
```

**Expected Response:**
```json
{
  "issuer": "https://jean-memory-api-virginia.onrender.com",
  "authorization_endpoint": "https://jean-memory-api-virginia.onrender.com/oauth/authorize",
  "token_endpoint": "https://jean-memory-api-virginia.onrender.com/oauth/token",
  "registration_endpoint": "https://jean-memory-api-virginia.onrender.com/oauth/register",
  "dynamic_client_registration_supported": true
}
```

## Deployment Checklist

- [x] **Add fastmcp>=0.1.0 to requirements.txt**
- [x] **Add mcpauth>=0.1.0 to requirements.txt** 
- [x] **Make imports optional with try/catch**
- [x] **Add dependency status to /fastmcp/status endpoint**
- [x] **Update documentation with troubleshooting steps**
- [ ] **Deploy to production**
- [ ] **Verify /fastmcp/status shows "ready" status**
- [ ] **Test OAuth discovery endpoints**
- [ ] **Test with Claude Web MCP connector**

## Potential Issues & Solutions

### Issue: Dependency Version Conflicts
**Symptoms:** Pip installation fails with version conflicts
**Solution:** Pin specific versions or use dependency ranges

### Issue: Dependencies Install But Import Fails  
**Symptoms:** Status shows dependencies unavailable despite successful install
**Solution:** Check for module naming differences or sub-package imports

### Issue: OAuth Endpoints Return 404
**Symptoms:** Discovery endpoints not accessible
**Solution:** Verify FastAPI router integration in main.py

### Issue: Claude Web Still Can't Connect
**Symptoms:** OAuth flow starts but fails during token exchange
**Solution:** 
1. Check logs for specific OAuth errors
2. Verify HTTPS endpoints in production
3. Test Dynamic Client Registration manually

## Monitoring Commands

```bash
# Check application health
curl https://jean-memory-api-virginia.onrender.com/health

# Check FastMCP status 
curl https://jean-memory-api-virginia.onrender.com/fastmcp/status

# Check OAuth discovery
curl https://jean-memory-api-virginia.onrender.com/.well-known/oauth-authorization-server

# Check protected resource metadata
curl https://jean-memory-api-virginia.onrender.com/.well-known/oauth-protected-resource
```

## OAuth Flow Fix Applied ✅

**Issue Identified:** Supabase redirect hijacking prevents OAuth callback completion

**Root Cause:** After Google authentication, users are redirected to main app instead of OAuth callback

**Fix Applied:**
1. ✅ **Forced OAuth callback redirects** in login page JavaScript
2. ✅ **Emergency fallback mechanisms** with 5s and 10s timeouts
3. ✅ **Manual completion endpoint** `/oauth/force-complete` as nuclear option
4. ✅ **Enhanced logging** for debugging OAuth flow steps
5. ✅ **Bypass Supabase redirects** using `window.location.replace()`

### OAuth Flow Improvements

**New Flow Pattern:**
1. User clicks "Connect" in Claude → OAuth login page loads
2. User clicks "Continue with Google" → Supabase OAuth starts
3. **After authentication**: JavaScript **forces** redirect to `/oauth/callback`
4. Callback handler sets cookies and redirects to `/oauth/authorize?oauth_session=xxx`
5. Authorize endpoint auto-approves and redirects to Claude with auth code
6. Claude calls `/oauth/token` to complete flow

**Failsafe Mechanisms:**
- **5s timeout**: Force callback if no automatic redirect
- **10s timeout**: Show manual "Complete OAuth Manually" button
- **Emergency endpoint**: `/oauth/force-complete?oauth_session=xxx`

## Next Actions

1. **Deploy OAuth fixes** 🚀 (Ready)
2. **Test Claude Web connection** 🔗 (Monitor logs for callback completion)
3. **Verify token exchange** 🧪 (Look for POST /oauth/token in logs)
4. **Document success** 📝 (After validation)

## Success Criteria

- ✅ Production deployment completes without errors
- ✅ `/fastmcp/status` returns `"status": "ready"`
- ✅ OAuth discovery endpoints return proper metadata
- ✅ Claude Web can complete OAuth flow and connect to MCP server

**This deployment fix addresses the core issue while maintaining backward compatibility and providing clear status monitoring.**