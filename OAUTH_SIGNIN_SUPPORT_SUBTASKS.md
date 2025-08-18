# OAuth Sign-in Support - Detailed Subtasks

**Parent Epic:** OAuth Sign-in Support - GitHub & Google Integration  
**Total Story Points:** 8  
**Sprint Duration:** 2 weeks  

---

## JMS-001: Backend OAuth Provider Routing and Token Exchange

**Task Type:** Backend Development  
**Story Points:** 2  
**Priority:** P1 (Blocking)  
**Duration:** 1 day  

### Task Description
Extend the existing SDK OAuth infrastructure to support provider routing (GitHub/Google) and implement proper token exchange between OAuth providers and Jean Memory session tokens.

### Mini-FRD (What & Why)

**What:** Modify `/sdk/oauth/*` endpoints to handle `provider` parameter and route authentication requests to appropriate OAuth providers (GitHub/Google).

**Why:** The current SDK OAuth endpoints exist but don't differentiate between providers. We need provider-specific routing to leverage the existing Supabase OAuth infrastructure.

**Scope:**
- **In Scope:** Provider parameter handling, OAuth URL generation, token exchange for GitHub/Google
- **Out Scope:** Apple OAuth, custom OAuth providers, account linking

**Acceptance Criteria:**
- [ ] `/sdk/oauth/authorize?provider=github` redirects to GitHub OAuth
- [ ] `/sdk/oauth/authorize?provider=google` redirects to Google OAuth  
- [ ] OAuth callback properly exchanges provider tokens for Jean Memory tokens
- [ ] State parameter validation prevents CSRF attacks
- [ ] Error handling for invalid providers or failed exchanges

### Mini-EDD (How)

**Chosen Approach:** Extend existing `sdk_oauth_router` to add provider routing logic, reusing Supabase OAuth infrastructure from main site.

**Key Components:**
- `openmemory/api/app/routers/sdk_oauth.py` - Add provider routing
- `openmemory/api/app/oauth_simple_new.py` - Provider-specific URL generation
- `openmemory/api/app/auth.py` - Token validation and exchange

**Implementation Steps:**
1. Add `provider` query parameter to `/sdk/oauth/authorize` endpoint
2. Implement provider-specific OAuth URL generation using Supabase
3. Update `/sdk/oauth/callback` to handle provider tokens
4. Add token exchange logic for OAuth → Jean Memory session tokens
5. Implement proper error handling and validation

**Risks & Mitigation:**
- **Provider configuration issues** → Test with development OAuth apps first
- **Token security** → Ensure provider tokens never exposed to client applications

---

## JMS-002: React SDK OAuth Button Integration and Popup Flow

**Task Type:** Frontend Development  
**Story Points:** 2  
**Priority:** P1  
**Duration:** 2 days  

### Task Description
Add GitHub and Google OAuth buttons to the React SDK's SignInWithJean component and implement a popup-based OAuth flow with proper callback handling.

### Mini-FRD (What & Why)

**What:** Enhance the existing SignInWithJean React component to include OAuth provider buttons and implement popup-based authentication flow.

**Why:** React applications need seamless OAuth integration without full page redirects. Popup flow maintains application state and provides better UX.

**Scope:**
- **In Scope:** OAuth buttons UI, popup OAuth flow, callback handling, error states
- **Out Scope:** Account linking UI, provider-specific features, social sharing

**Acceptance Criteria:**
- [ ] SignInWithJean component shows GitHub and Google buttons
- [ ] Clicking OAuth button opens popup window with provider OAuth
- [ ] Popup communicates auth result back to parent window via postMessage
- [ ] Successful OAuth closes popup and triggers onSuccess callback
- [ ] Failed OAuth shows clear error message and closes popup
- [ ] Works on desktop Chrome, Safari, Firefox
- [ ] Mobile browser compatibility (fallback to redirect if popup blocked)

### Mini-EDD (How)

**Chosen Approach:** Extend existing SignInWithJean component with OAuth buttons, implement popup-based flow using window.open() and postMessage API for secure cross-window communication.

**Key Components:**
- `sdk/react/SignInWithJean.tsx` - Add OAuth buttons and popup logic
- `sdk/react/OAuthCallback.tsx` - New callback page component
- `sdk/react/components/OAuthButton.tsx` - Reusable OAuth button component

**Implementation Steps:**
1. Create OAuthButton component with GitHub/Google styling
2. Add OAuth buttons to SignInWithJean component layout
3. Implement popup window creation and management
4. Create OAuth callback page that communicates with parent window
5. Add postMessage event handling for auth results
6. Implement fallback redirect flow for popup-blocked scenarios

**Risks & Mitigation:**
- **Popup blocking** → Detect popup blocking, offer redirect fallback
- **Mobile compatibility** → Test extensively on iOS/Android browsers
- **Cross-origin messaging** → Validate message origins for security

---

## JMS-003: Node.js SDK OAuth Browser Flow Implementation

**Task Type:** Backend SDK Development  
**Story Points:** 1.5  
**Priority:** P1  
**Duration:** 1 day  

### Task Description
Extend the Node.js SDK's JeanMemoryAuth class to support OAuth authentication through browser-based flows with local callback server handling.

### Mini-FRD (What & Why)

**What:** Add OAuth methods to the existing JeanMemoryAuth class that can open a browser for OAuth and capture the callback via a local HTTP server.

**Why:** Node.js applications (CLI tools, desktop apps) need OAuth support but can't use browser-only popup flows. Local server approach allows secure OAuth without exposing credentials.

**Scope:**
- **In Scope:** Browser-based OAuth flow, local callback server, GitHub/Google providers
- **Out Scope:** Headless OAuth, service account authentication, mobile app integration

**Acceptance Criteria:**
- [ ] `auth.authenticateWithOAuth('github')` opens browser to GitHub OAuth
- [ ] `auth.authenticateWithOAuth('google')` opens browser to Google OAuth
- [ ] Local callback server captures OAuth redirect securely
- [ ] Method returns Jean Memory session token after successful OAuth
- [ ] Graceful error handling for user denial or network issues
- [ ] Works on macOS, Windows, Linux development environments
- [ ] Proper cleanup of local server after authentication

### Mini-EDD (How)

**Chosen Approach:** Extend existing JeanMemoryAuth class with OAuth methods that start a local HTTP server, open browser to OAuth URL, and exchange callback code for tokens.

**Key Components:**
- `sdk/node/src/auth.ts` - Add OAuth methods to JeanMemoryAuth class
- Local HTTP server implementation for OAuth callbacks
- Browser opening utility using `open` package

**Implementation Steps:**
1. Add OAuth provider methods to JeanMemoryAuth class
2. Implement local callback server with random port selection
3. Add browser opening functionality with fallback messaging
4. Implement OAuth callback parameter extraction and validation
5. Add token exchange integration with backend OAuth endpoints
6. Implement proper server cleanup and error handling

**Risks & Mitigation:**
- **Port conflicts** → Use random port selection with retry logic
- **Browser opening failures** → Provide manual URL copy option
- **Firewall issues** → Use localhost binding only, document port requirements

---

## JMS-004: Python SDK OAuth Browser Flow Implementation

**Task Type:** Python SDK Development  
**Story Points:** 1.5  
**Priority:** P1  
**Duration:** 1 day  

### Task Description
Add OAuth authentication capabilities to the Python SDK's JeanMemoryAuth class using browser-based OAuth with local HTTP server for callback handling.

### Mini-FRD (What & Why)

**What:** Extend the existing Python JeanMemoryAuth class to support GitHub and Google OAuth through browser automation and local callback server.

**Why:** Python applications (data science tools, automation scripts) need OAuth support for better security and user experience compared to API key management.

**Scope:**
- **In Scope:** Browser OAuth flow, local HTTP server, webbrowser integration, GitHub/Google
- **Out Scope:** Jupyter notebook widgets, headless authentication, service accounts

**Acceptance Criteria:**
- [ ] `auth.authenticate(method='github')` opens browser to GitHub OAuth
- [ ] `auth.authenticate(method='google')` opens browser to Google OAuth
- [ ] Local server captures OAuth callback and displays success page
- [ ] Method returns user info dict with Jean Memory access token
- [ ] Works in Python 3.8+ environments (Windows, macOS, Linux)
- [ ] Proper error handling for user cancellation or network failures
- [ ] Clean server shutdown after authentication completion

### Mini-EDD (How)

**Chosen Approach:** Extend existing JeanMemoryAuth class with OAuth methods using Python's built-in `webbrowser` and `http.server` modules for browser automation and callback handling.

**Key Components:**
- `sdk/python/jean_memory/auth.py` - Extend JeanMemoryAuth with OAuth methods
- Built-in HTTP server for OAuth callbacks
- `webbrowser` module integration for cross-platform browser opening

**Implementation Steps:**
1. Add OAuth provider support to JeanMemoryAuth constructor
2. Implement local HTTP server using HTTPServer and BaseHTTPRequestHandler
3. Add OAuth URL generation and browser opening with webbrowser module
4. Implement callback parameter parsing and state validation
5. Add token exchange with backend OAuth endpoints
6. Implement proper server threading and cleanup

**Risks & Mitigation:**
- **Python version compatibility** → Test with Python 3.8, 3.9, 3.10, 3.11, 3.12
- **Threading issues** → Use proper threading for server management
- **Browser detection** → Handle environments without browser gracefully

---

## JMS-005: Cross-platform Testing and Documentation Updates

**Task Type:** Testing & Documentation  
**Story Points:** 1  
**Priority:** P1  
**Duration:** 1 day  

### Task Description
Comprehensive testing of OAuth flows across all SDKs and platforms, plus documentation updates with OAuth examples and troubleshooting guides.

### Mini-FRD (What & Why)

**What:** End-to-end testing of OAuth functionality across React, Node.js, and Python SDKs on multiple platforms, with comprehensive documentation updates.

**Why:** OAuth flows have many platform-specific edge cases and browser compatibility issues. Thorough testing prevents production issues and good documentation reduces support burden.

**Scope:**
- **In Scope:** Cross-platform testing, browser compatibility, documentation, troubleshooting guides
- **Out Scope:** Performance testing, load testing, automated CI integration

**Acceptance Criteria:**
- [ ] OAuth works in React apps on Chrome, Safari, Firefox (desktop)
- [ ] OAuth works in React apps on iOS Safari, Android Chrome (mobile)
- [ ] Node.js OAuth tested on Windows, macOS, Linux
- [ ] Python OAuth tested on Windows, macOS, Linux  
- [ ] All SDK documentation updated with OAuth examples
- [ ] Troubleshooting guide created for common OAuth issues
- [ ] Migration guide for existing email/password users
- [ ] Error scenarios documented with solutions

### Mini-EDD (How)

**Chosen Approach:** Systematic testing matrix covering all SDK/platform/browser combinations, with documentation updates focused on practical examples and common issues.

**Key Components:**
- Test applications for each SDK with OAuth integration
- Browser compatibility testing matrix
- Documentation updates across all SDK READMEs
- Troubleshooting knowledge base

**Implementation Steps:**
1. Create test applications for React, Node.js, Python with OAuth
2. Execute testing matrix across browsers and platforms
3. Document all discovered issues and solutions
4. Update SDK documentation with OAuth examples
5. Create troubleshooting guide with common error scenarios
6. Write migration guide for existing applications
7. Review and approve all documentation changes

**Risks & Mitigation:**
- **Platform-specific issues** → Allocate time for debugging platform edge cases
- **Documentation drift** → Create templates for consistent OAuth documentation
- **Testing coverage gaps** → Use systematic testing matrix to ensure completeness

---

## Implementation Timeline

```
Week 1:
├── JMS-001: Backend OAuth routing (Day 1)
├── JMS-002: React OAuth integration (Days 2-3) 
└── JMS-003: Node.js OAuth implementation (Day 4)

Week 2:
├── JMS-004: Python OAuth implementation (Day 1)
├── JMS-005: Testing & documentation (Days 2-3)
└── Integration testing and bug fixes (Days 4-5)
```

## Dependencies Between Subtasks

1. **JMS-001 (Backend)** → Must complete first (blocks all other tasks)
2. **JMS-002, JMS-003, JMS-004** → Can run in parallel after JMS-001
3. **JMS-005** → Requires completion of all implementation tasks

## Risk Mitigation Strategy

### High-Risk Areas
- **Browser compatibility** (JMS-002) - Allocate extra testing time
- **Cross-platform authentication** (JMS-003, JMS-004) - Test early and often
- **OAuth provider configuration** (JMS-001) - Use development OAuth apps initially

### Contingency Plans
- If popup issues persist → Implement redirect-only fallback
- If platform-specific issues arise → Document platform-specific setup requirements
- If provider integration fails → Focus on single provider (GitHub) for MVP

---

**Total Effort:** 8 Story Points over 2 weeks  
**Critical Path:** JMS-001 → (JMS-002 || JMS-003 || JMS-004) → JMS-005  
**Success Metrics:** All OAuth flows working across platforms, documentation complete, zero critical bugs