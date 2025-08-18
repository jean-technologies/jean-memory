# Jean Memory SDK Testing - Notion/JIRA Tasks

## ⚠️ **BLOCKER: Codebase Version Mismatch**

### **Critical Issue Found:**
All three SDKs have major version mismatches between local repository and published packages:
- **React SDK:** Local 0.2.1 vs NPM 1.1.1
- **Python SDK:** Local 0.1.0 vs PyPI 1.1.1  
- **Node.js SDK:** Local 0.1.3 vs NPM 1.2.3

**Action Required:** Obtain latest source code before proceeding with testing tasks.

---

## Task 1: React SDK Testing & Fixes

### **Task Name:**
`[SDK] Test and Fix React SDK v1.1.1 - Package Dependencies & Documentation Alignment`

### **Task Description:**
**Objective:** Validate and fix the Jean Memory React SDK to ensure production readiness and documentation accuracy.

**⚠️ PREREQUISITE:** Must first obtain React SDK v1.1.1 source code (current local is 0.2.1)

**Background:**
The React SDK has version discrepancies between local (0.2.1) and NPM (1.1.1), missing dependencies in package.json, and potential mismatches between documented and actual functionality.

**Deliverables:**
- Source code synchronization report
- Test report documenting all issues found
- Fixed package.json with correct dependencies
- Updated TypeScript type definitions
- Verified JeanProvider, JeanChat, and useJean hook functionality
- Working authentication flow with "Sign In with Jean"
- All documentation examples tested and working

**Acceptance Criteria:**
- [ ] NPM package installs without warnings
- [ ] All components render without errors
- [ ] Authentication flow completes successfully
- [ ] TypeScript types properly exported
- [ ] Documentation examples work as written

**Priority:** High
**Estimated Time:** 8 hours
**Labels:** `sdk`, `react`, `testing`, `documentation`

---

## Task 2: Python SDK Testing & Fixes

### **Task Name:**
`[SDK] Test and Fix Python SDK - Authentication Flow & OpenAI Dependencies`

### **Task Description:**
**Objective:** Test and fix the Jean Memory Python SDK for reliable backend integration and proper dependency management.

**⚠️ PREREQUISITE:** Must first obtain Python SDK v1.1.1 source code (current local is 0.1.0)

**Background:**
The Python SDK has undocumented OpenAI dependencies, conversation history handling differences from other SDKs, and authentication flow requires explicit credentials which may not align with OAuth token flow.

**Deliverables:**
- Complete test suite for Python SDK
- Fixed conversation history handling
- Documented OpenAI API key requirement
- Improved authentication flow with token support
- Error handling improvements
- PyPI package verification

**Acceptance Criteria:**
- [ ] pip install jeanmemory works cleanly
- [ ] API key validation succeeds
- [ ] get_context returns proper format
- [ ] Works with Python 3.8+
- [ ] Clear error messages for missing dependencies

**Priority:** High
**Estimated Time:** 6 hours
**Labels:** `sdk`, `python`, `testing`, `backend`

---

## Task 3: Node.js SDK Testing & Fixes

### **Task Name:**
`[SDK] Test and Fix Node.js SDK - Next.js Integration & JWT Token Handling`

### **Task Description:**
**Objective:** Validate and fix the Node.js SDK for seamless Next.js and serverless function integration.

**⚠️ PREREQUISITE:** Must first obtain Node.js SDK v1.2.3 source code (current local is 0.1.3 with different package name)

**Background:**
The Node.js SDK has undocumented dependencies (ai, @ai-sdk/openai), oversimplified JWT token parsing that may fail in production, and needs verification for edge runtime compatibility. Local package name is "jeanmemory-node" while NPM package is "@jeanmemory/node".

**Deliverables:**
- Complete Next.js integration test
- Fixed package.json with all dependencies
- Improved JWT token validation
- Edge runtime compatibility verification
- Streaming response testing
- API route handler examples

**Acceptance Criteria:**
- [ ] npm install @jeanmemory/node works without errors
- [ ] createHandler works in Next.js API routes
- [ ] Proper JWT token validation
- [ ] Streaming responses functional
- [ ] Edge runtime compatible

**Priority:** High
**Estimated Time:** 6 hours
**Labels:** `sdk`, `nodejs`, `testing`, `nextjs`, `serverless`

---

## Epic/Parent Task (Optional)

### **Epic Name:**
`[EPIC] SDK Production Readiness - Test and Fix All SDKs`

### **Epic Description:**
**Objective:** Ensure all Jean Memory SDKs (React, Python, Node.js) are production-ready with accurate documentation and reliable functionality.

**Scope:**
Comprehensive testing and fixing of all three SDKs to ensure consistent APIs, proper dependency management, and documentation alignment.

**Success Metrics:**
- 100% of documented examples working
- Zero installation warnings/errors
- Consistent API patterns across SDKs
- Developer integration time < 5 minutes

**Child Tasks:**
1. React SDK Testing & Fixes
2. Python SDK Testing & Fixes  
3. Node.js SDK Testing & Fixes

**Priority:** Critical
**Timeline:** 1 Sprint (2 weeks)
**Labels:** `epic`, `sdk`, `testing`, `q1-2025`