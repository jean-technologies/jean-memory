# JIRA Task: OAuth Sign-in Support - GitHub & Google Integration

**Task Name:** SDK OAuth Authentication - GitHub & Google Provider Support  
**Task Type:** Enhancement  
**Priority:** P1  
**Epic:** User Authentication Experience  
**Story Points:** 8  

---

## Task Description

Enable OAuth sign-in options (GitHub and Google) for Jean Memory SDK applications alongside existing email/password authentication. This will reduce sign-in friction, increase conversion rates, and provide a more familiar authentication experience for users by leveraging OAuth providers already configured on the main jeanmemory.com platform.

**Current State:** SDK only supports email/password authentication  
**Target State:** SDK supports email/password + GitHub OAuth + Google OAuth

---

## Mini-FRD (What & Why)

### What
Add GitHub and Google OAuth sign-in capabilities to all Jean Memory SDKs (React, Node.js, Python) so users can authenticate using their existing accounts instead of creating new passwords.

### Why  
- Current email/password flow creates friction and reduces conversion rates
- Developer community expects OAuth sign-in options, especially GitHub
- OAuth provides better security (no passwords to store/manage)
- Leverages existing Supabase OAuth infrastructure already working on main site

### Scope

**In Scope:**
- GitHub OAuth integration for all SDKs (React, Node.js, Python)
- Google OAuth integration for all SDKs (React, Node.js, Python)  
- OAuth callback handling and token exchange
- UI components for OAuth sign-in buttons (React SDK)
- PKCE security flow implementation
- SDK endpoint wrappers for existing OAuth infrastructure

**Out of Scope:**
- Apple OAuth or other providers
- Account linking between OAuth and email accounts (future enhancement)
- OAuth scope customization beyond basic profile access
- Social sharing features or provider-specific integrations

### Acceptance Criteria
- [ ] GitHub sign-in works in React SDK with popup/redirect flow
- [ ] Google sign-in works in React SDK with popup/redirect flow  
- [ ] Node.js SDK can authenticate via browser OAuth flow
- [ ] Python SDK can authenticate via browser OAuth flow
- [ ] OAuth tokens are properly exchanged for Jean Memory session tokens
- [ ] CSRF protection via state parameter validation
- [ ] Works on both desktop and mobile browsers
- [ ] Graceful error handling for OAuth failures
- [ ] Existing email/password authentication continues working unchanged

---

## Mini-EDD (How)

### Chosen Approach
Extend the existing SDK OAuth infrastructure (`/sdk/oauth/*` endpoints) to support GitHub and Google providers by wrapping the main site's Supabase OAuth implementation. This leverages proven OAuth flows while providing SDK-specific token exchange and session management.

### Key Components / Code Areas
- `sdk/react/SignInWithJean.tsx` - Add OAuth button options
- `openmemory/api/app/routers/sdk_oauth.py` - OAuth endpoint wrappers  
- `sdk/node/src/auth.ts` - Node.js OAuth browser flow
- `sdk/python/jean_memory/auth.py` - Python OAuth browser flow
- `openmemory/api/app/oauth_simple_new.py` - Token exchange backend
- `openmemory/ui/components/auth/AuthForm.tsx` - Reference OAuth UI patterns

### Implementation Steps
1. **Backend OAuth Endpoint Enhancement** (1 day)
   - Extend `/sdk/oauth/authorize` to support `provider` parameter
   - Add provider routing to GitHub/Google OAuth URLs
   - Update token exchange to handle OAuth callback tokens

2. **React SDK OAuth Integration** (2 days)  
   - Add GitHub/Google OAuth buttons to SignInWithJean component
   - Implement popup-based OAuth flow with postMessage communication
   - Add OAuth callback page component for redirect handling
   - Update JeanAgent to show OAuth options in auth modal

3. **Node.js SDK OAuth Flow** (1 day)
   - Extend JeanMemoryAuth class with OAuth provider methods
   - Implement browser-based OAuth with local callback server
   - Add OAuth URL generation and token exchange methods

4. **Python SDK OAuth Flow** (1 day)
   - Add OAuth provider support to JeanMemoryAuth class  
   - Implement webbrowser-based OAuth with local HTTP server
   - Add provider-specific OAuth configuration

5. **Testing & Documentation** (1 day)
   - Test OAuth flows across all SDKs with real GitHub/Google accounts
   - Update SDK documentation with OAuth examples
   - Add error handling and edge case coverage

### Risks & Mitigation
- **OAuth popup blocking** → Provide fallback redirect flow option
- **Mobile browser limitations** → Test extensively on iOS/Android, consider app-based flows for mobile
- **Token security** → Ensure proper PKCE implementation, never expose provider tokens
- **Provider API changes** → Use stable OAuth 2.0 endpoints, monitor provider documentation
- **CSRF attacks** → Implement proper state parameter validation and session management

### Testing Plan
- **Local Development**: Test OAuth flows with GitHub/Google test apps on localhost
- **Staging Environment**: Verify OAuth with production GitHub/Google apps on staging domain
- **Cross-Platform Testing**: Test on Chrome, Safari, Firefox across desktop and mobile
- **Error Scenarios**: Test network failures, user denial, invalid tokens
- **Security Testing**: Verify CSRF protection, token validation, session security

---

## Implementation Notes

### Current OAuth Infrastructure Analysis
✅ **Existing Infrastructure:**
- Supabase OAuth configured for GitHub/Google on main site
- Working OAuth flows in `openmemory/ui/components/auth/AuthForm.tsx`
- JWT token system with scope support
- Basic SDK OAuth endpoints at `/sdk/oauth/*`

✅ **Gaps to Address:**
- SDK OAuth endpoints don't support provider routing
- No OAuth UI components in React SDK  
- Node.js/Python SDKs lack OAuth support
- Missing OAuth callback handling in SDKs

### Security Considerations
- Use OAuth 2.1 PKCE flow for all implementations
- Validate state parameter to prevent CSRF attacks
- Never expose provider access tokens to SDK applications
- Use time-limited Jean Memory session tokens post-OAuth
- Implement proper redirect URI validation

### Breaking Changes Assessment
- **None expected** - This is purely additive functionality
- Existing email/password authentication remains unchanged
- New OAuth methods are optional additions to SDK APIs

---

## Definition of Ready Checklist
- [x] FRD and EDD sections completed
- [x] Acceptance criteria clearly defined and testable  
- [x] No blocking dependencies identified
- [x] Security and privacy implications reviewed
- [x] Breaking changes assessment completed (none expected)
- [x] Implementation approach validated against existing codebase

## Subtasks
1. **JMS-001**: Backend OAuth provider routing and token exchange
2. **JMS-002**: React SDK OAuth button integration and popup flow
3. **JMS-003**: Node.js SDK OAuth browser flow implementation  
4. **JMS-004**: Python SDK OAuth browser flow implementation
5. **JMS-005**: Cross-platform testing and documentation updates

---

**Ready for Development** ✅