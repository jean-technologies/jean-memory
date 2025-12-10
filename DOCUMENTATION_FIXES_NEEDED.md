# Documentation Fixes Needed

## Overview
This document tracks remaining documentation issues identified during SDK testing. These are non-critical issues that can be addressed when convenient.

## Performance Expectations Gap

### Issue
Speed-modes documentation shows optimistic processing times:
- Documentation: "Balanced mode: 3-5 seconds"
- Reality: 15+ seconds including network overhead

### Fix Needed
Update `openmemory/ui/docs-mintlify/speed-modes.mdx` lines 98, 197, etc:

```markdown
**Performance**: 3-5 seconds core processing + 2-10s network overhead (5-15s total)
```

## Missing Documentation Sections

### 1. Troubleshooting Guide
Create `openmemory/ui/docs-mintlify/troubleshooting.mdx` with:

```markdown
## Common Errors

### `Cannot read properties of undefined (reading 'replace')`  
**Cause**: Using Node.js object API without user_token (pre-2.0.7)
**Solution**: Update to 2.0.7+ or use string overload: `client.getContext("query")`

### `401 Unauthorized`
**Cause**: Invalid API key or expired test credentials
**Solution**: Verify API key starts with 'jean_sk_'

### Performance slower than expected
**Cause**: Network latency + server processing
**Reality**: Actual times are 2-5x documented processing time
```

### 2. Error Handling Guide
Add to SDK documentation:

```javascript
// Always use try-catch for production
try {
  const response = await jean.getContext({ message: query, speed: 'balanced' });
} catch (error) {
  console.error('Context retrieval failed:', error.message);
  // Fallback strategy
}
```

## JWT Token Persistence

### Question to Investigate
- How long do JWT tokens last?
- Do they persist across browser sessions? 
- Cookie-based or localStorage?
- Auto-refresh mechanism?

**Location to check**: `openmemory/ui/docs-mintlify/authentication.mdx`

## Authentication Documentation Clarification

### Current Issue
MCP API docs say: `Authorization: Bearer <your_pkce_jwt>`
SDK code sends: `Authorization: Bearer ${userToken}`

This is actually **correct** - userToken IS the PKCE JWT. No fix needed, just document clearly that userToken = JWT.

## Low Priority Improvements

1. Add SDK version badges to README
2. Cross-reference examples between React/Node.js/Python docs
3. Add performance benchmarking guide
4. Expand use case examples

## CRITICAL BUG: MCP Authentication Completely Broken

### Issue (CRITICAL PRIORITY)
**Date Identified**: 2024-08-23

The MCP endpoints in the backend **completely ignore user JWT tokens**, making user authentication non-functional. This is a fundamental architecture flaw.

**Problem**: 
- **SDKs send**: Both `Authorization: Bearer {jwt_token}` AND `X-API-Key: {api_key}`
- **Backend processes**: Only `X-API-Key` via `get_user_from_api_key_header()`  
- **JWT token is completely ignored** - all users with same API key become identical

**Impact**:
- All SDK users sharing same API key are treated as same user
- No per-user memory isolation  
- User authentication is completely bypassed
- Multi-user apps cannot work correctly

**Root Cause**:
`openmemory/api/app/routing/mcp.py:217` calls `get_user_from_api_key_header()` instead of `get_current_user_secure()`

**Fix Required**:
Change MCP endpoints to use `get_current_user_secure()` which validates BOTH:
1. `X-API-Key` header (company/app identification)  
2. `Authorization: Bearer {jwt}` header (user identity)

**Files Affected**:
- `openmemory/api/app/routing/mcp.py` (line 217)
- All SDK MCP calls currently broken for multi-user scenarios

**Severity**: **CRITICAL** - Authentication is "one of the most important parts of these working SDKs"

**Status**: 🔴 **UNRESOLVED** - Active blocker for production multi-user deployments

## Status
- ✅ **Critical Node.js SDK crash fixed** (2024-08-23)
- ✅ **Misleading documentation removed** (2024-08-23)  
- 🔴 **CRITICAL: MCP user authentication broken** - HIGHEST PRIORITY
- ⏳ **Performance documentation** - Low priority
- ⏳ **Troubleshooting guide** - Medium priority
- ⏳ **JWT persistence docs** - Low priority

## Notes
These are all quality-of-life improvements. The SDKs are functional and a reasonably good developer with AI assistance can work around any remaining gaps.

**EXCEPTION**: The MCP authentication issue is a critical blocker that prevents proper multi-user functionality.