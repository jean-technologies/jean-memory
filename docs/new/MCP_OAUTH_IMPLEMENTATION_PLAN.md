# MCP OAuth 2.1 Implementation Plan

## Summary
Based on official MCP specification (2025-03-26) and Anthropic documentation, this plan outlines the correct OAuth 2.1 implementation for Jean Memory's MCP server integration with Claude Web.

## Current Problem
- Claude Web redirects users away from Claude page (wrong behavior)
- Authorization endpoint shows "Sign in" page instead of auto-approving authenticated users
- No authorization code exchange happening (missing `/oauth/token` requests in logs)
- Cross-domain authentication detection failing

## Official MCP OAuth Requirements

### 1. Core Standards Compliance
- **MUST implement OAuth 2.1** with PKCE for all clients
- **MUST implement OAuth 2.0 Authorization Server Metadata (RFC8414)**
- **SHOULD implement Dynamic Client Registration (RFC7591)**
- All endpoints **MUST be served over HTTPS**

### 2. Required Endpoints
```
/.well-known/oauth-authorization-server  (metadata discovery)
/oauth/authorize                         (authorization endpoint)
/oauth/token                            (token exchange endpoint)  
/oauth/register                         (dynamic client registration)
```

### 3. Authorization Base URL Rule
- Authorization base URL = MCP server domain root
- If MCP server: `https://jean-memory-api-virginia.onrender.com/mcp`
- Then auth base: `https://jean-memory-api-virginia.onrender.com`
- Metadata at: `https://jean-memory-api-virginia.onrender.com/.well-known/oauth-authorization-server`

### 4. Expected Flow for Claude Web
```
1. User clicks "Connect" in Claude
2. Claude discovers OAuth metadata at /.well-known/oauth-authorization-server
3. Claude registers as client via /oauth/register (auto-happens)
4. Claude redirects user to /oauth/authorize with PKCE challenge
5. Authorization endpoint checks if user authenticated to Jean Memory
6. IF authenticated → auto-approve, generate auth code, redirect back to Claude
7. IF not authenticated → redirect to Jean Memory login, then return to step 6
8. Claude receives auth code, exchanges at /oauth/token with PKCE verifier
9. Claude gets Bearer token, uses for all MCP requests
```

## Key Implementation Requirements

### 1. Authorization Endpoint (`/oauth/authorize`)
**MUST:**
- Validate redirect URI (must be `https://claude.ai/api/mcp/auth_callback`)
- Generate and store authorization code with PKCE challenge
- Support auto-approval for authenticated users
- Handle user authentication via existing Jean Memory session
- Redirect back to Claude with authorization code

**SHOULD NOT:**
- Show manual approval UI for trusted clients (Claude)
- Require user to leave Claude interface
- Break existing Jean Memory authentication

### 2. Token Endpoint (`/oauth/token`)
**MUST:**
- Validate PKCE code_verifier against stored code_challenge
- Exchange authorization code for Bearer access token
- Issue JWT tokens with user identity (user_id, email, client)
- Support token expiration and rotation

### 3. Authentication Detection
**Current Issue:** Cross-domain authentication detection
**Solution:** Check for Jean Memory session via:
- Supabase session cookies (domain-compatible)
- If no session → redirect to `https://jeanmemory.com/auth?return_url=...`
- If session exists → auto-approve immediately

## Implementation Plan

### Phase 1: Fix Authorization Endpoint (HIGH PRIORITY)
1. **Auto-approval for authenticated users**
   - Check Supabase session cookies
   - If user authenticated → immediate redirect to Claude with auth code
   - No intermediate approval UI for Claude client

2. **Proper session detection**
   - Use domain-compatible cookie checking
   - Handle cross-domain authentication properly
   - Fallback to login redirect if not authenticated

### Phase 2: Fix Token Exchange
1. **Implement proper PKCE validation**
   - Store code_challenge with authorization code
   - Validate code_verifier on token exchange
   - Generate proper JWT Bearer tokens

2. **Add comprehensive logging**
   - Track each step of OAuth flow
   - Debug authorization code exchange issues

### Phase 3: End-to-End Testing
1. **Test complete flow**
   - User already logged into Jean Memory
   - User not logged into Jean Memory
   - Token validation in MCP endpoints

## Security Requirements (Per MCP Spec)

1. **PKCE required for all clients**
2. **Redirect URI validation** (only allow Claude's callback URL)
3. **HTTPS enforcement** (already implemented)
4. **Token expiration and rotation**
5. **Secure token storage**

## Expected User Experience

### Ideal Flow (User Already Authenticated):
1. User clicks "Connect Jean Memory" in Claude
2. Brief redirect/loading (< 2 seconds)
3. User returns to Claude with connection established
4. No manual approval steps, no leaving Claude interface

### Flow (User Not Authenticated):
1. User clicks "Connect Jean Memory" in Claude
2. Redirected to Jean Memory login page
3. User logs in to Jean Memory
4. Automatic redirect back to Claude with connection established
5. Returns to Claude interface

## Critical Success Criteria

✅ **User never manually approves Claude client**
✅ **User stays in Claude interface (or minimal redirect time)**
✅ **Authorization code exchange completes successfully**
✅ **Bearer tokens work for MCP requests**
✅ **Existing MCP v2 endpoints remain functional**

## Files to Modify

1. `/app/oauth_simple.py` - Fix authorization endpoint auto-approval
2. `/app/oauth_simple.py` - Fix token exchange with PKCE validation
3. `/main.py` - Ensure OAuth discovery endpoint works correctly

## Testing Checklist

- [ ] OAuth metadata discovery returns correct endpoints
- [ ] Dynamic client registration works for Claude
- [ ] Authorization endpoint auto-approves authenticated users
- [ ] Authorization endpoint redirects unauthenticated users to login
- [ ] Token exchange validates PKCE and returns Bearer tokens
- [ ] Bearer tokens work with `/mcp` endpoint
- [ ] Existing `/mcp/v2/{client}/{user_id}` endpoints still work
- [ ] End-to-end flow completes without user intervention (when authenticated)

## References

- [MCP Authorization Specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)
- [Anthropic MCP Connector Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector)
- [OAuth 2.1 IETF Draft](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-10)
- [RFC 8414 - OAuth 2.0 Authorization Server Metadata](https://tools.ietf.org/html/rfc8414)
- [RFC 7591 - OAuth 2.0 Dynamic Client Registration](https://tools.ietf.org/html/rfc7591)