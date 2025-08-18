# Jean Memory SDK Testing and Fix FRDs

## **CRITICAL PREREQUISITE: Codebase Version Alignment**

### **Version Discrepancies Found:**

| SDK | Local Version | Published Version | Status |
|-----|--------------|------------------|---------|
| **React SDK** | 0.2.1 | NPM: 1.1.1 | ⚠️ **MAJOR MISMATCH** |
| **Python SDK** | 0.1.0 | PyPI: 1.1.1 | ⚠️ **MAJOR MISMATCH** |
| **Node.js SDK** | 0.1.3 (local package name: jeanmemory-node) | NPM: 1.2.3 (@jeanmemory/node) | ⚠️ **MAJOR MISMATCH** |

### **Required Actions Before Testing:**

1. **Obtain Latest Source Code**
   - [ ] Get React SDK v1.1.1 source code (currently local is 0.2.1)
   - [ ] Get Python SDK v1.1.1 source code (currently local is 0.1.0)
   - [ ] Get Node.js SDK v1.2.3 source code (currently local is 0.1.3)

2. **Options to Resolve:**
   - **Option A:** Pull latest code from private repository/branch
   - **Option B:** Decompile/extract from published packages
   - **Option C:** Update local versions to match published and re-publish

3. **Verification Steps:**
   - Compare package contents with published versions
   - Ensure all features in published packages exist in source
   - Validate that published packages were built from available source

---

## **Part 1 — React SDK Testing & Fix Mini-FRD**

### **What**
Test and fix the Jean Memory React SDK to ensure proper functionality, type safety, and alignment between implementation and documentation for production-ready React applications.

### **Why**
The React SDK has version discrepancies (local 0.2.1 vs NPM 1.1.1), missing dependencies in package.json, and potential mismatches between documented and actual functionality. This impacts developer experience and adoption.

### **Scope**

**In Scope:**
- Verify JeanProvider wrapper functionality
- Test JeanChat component rendering and UX
- Validate useJean hook API and data flow
- Test authentication flow (Sign In with Jean)
- Verify tool access (add_memory, search_memory)
- Check TypeScript types and exports
- Test with latest NPM version (1.1.1)
- Fix package.json dependencies
- Ensure documentation matches implementation

**Out of Scope:**
- Backend API changes
- MCP protocol modifications
- OAuth provider configuration
- LLM model selection

### **Acceptance Criteria**
- [ ] JeanProvider wraps app without errors
- [ ] JeanChat component renders with proper styling
- [ ] useJean hook returns all documented methods
- [ ] Authentication flow completes successfully
- [ ] Messages send and receive properly
- [ ] Context retrieval works as documented
- [ ] TypeScript types are properly exported
- [ ] NPM package installs without peer dependency warnings
- [ ] All examples in docs work as written

---

## **Part 2 — Python SDK Testing & Fix Mini-FRD**

### **What**
Test and fix the Jean Memory Python SDK to ensure reliable integration for Python agents and backend services with proper error handling and authentication flow.

### **Why**
The Python SDK implementation shows potential issues with conversation history handling (sends only current message, not full history), OpenAI dependency not documented, and authentication flow requires explicit user credentials input.

### **Scope**

**In Scope:**
- Test JeanClient initialization and validation
- Verify get_context method functionality
- Test authentication methods (OAuth token flow)
- Validate speed modes and tool selection
- Check error handling and exceptions
- Verify PyPI package installation
- Test with various Python versions (3.8+)
- Fix conversation history handling
- Document OpenAI API key requirement

**Out of Scope:**
- OAuth provider implementation
- Backend context engineering
- LLM response generation logic
- Memory storage implementation

### **Acceptance Criteria**
- [ ] pip install jeanmemory works cleanly
- [ ] API key validation succeeds with valid key
- [ ] get_context returns proper response format
- [ ] Authentication with user token works
- [ ] Speed modes affect response correctly
- [ ] Tool selection works as documented
- [ ] Error messages are helpful and clear
- [ ] Works with Python 3.8, 3.9, 3.10, 3.11
- [ ] Documentation examples run without modification

---

## **Part 3 — Node.js SDK Testing & Fix Mini-FRD**

### **What**
Test and fix the Jean Memory Node.js SDK for seamless integration with Next.js API routes, serverless functions, and Node.js backends.

### **Why**
The Node.js SDK has undocumented dependencies (ai, @ai-sdk/openai), simplified JWT token parsing that may fail in production, and the NPM package may not match the repository version.

### **Scope**

**In Scope:**
- Test JeanClient initialization
- Verify getContext method with user tokens
- Test Next.js API route handler creation
- Validate streaming response functionality
- Check edge runtime compatibility
- Test error handling and retries
- Verify NPM package installation
- Fix missing dependencies in package.json
- Improve JWT token validation

**Out of Scope:**
- Frontend React components
- OAuth flow implementation
- WebSocket connections
- Database operations

### **Acceptance Criteria**
- [ ] npm install @jeanmemory/node works without errors
- [ ] JeanClient initializes with API key
- [ ] getContext returns enhanced messages
- [ ] createHandler works in Next.js API routes
- [ ] Streaming responses work properly
- [ ] Edge runtime compatible
- [ ] Token validation handles edge cases
- [ ] TypeScript types are accurate
- [ ] Documentation code examples work as-is

---

## **Testing Strategy**

### **Phase 0: Codebase Synchronization** ⚠️ **MUST DO FIRST**
1. Verify source code matches published packages
2. Download published packages and extract
3. Compare with local repository code
4. Update local versions or obtain latest source
5. Document any missing features or files

### **Phase 1: Setup & Installation Testing**
1. Create fresh test projects for each SDK
2. Install from NPM/PyPI
3. Verify no dependency conflicts
4. Check TypeScript/Python type definitions

### **Phase 2: Integration Testing**
1. Create minimal "hello world" examples
2. Test authentication flows
3. Verify context retrieval
4. Test message enhancement
5. Validate tool usage

### **Phase 3: Edge Case Testing**
1. Invalid API keys
2. Network failures
3. Malformed responses
4. Rate limiting
5. Token expiration

### **Phase 4: Documentation Validation**
1. Run every code example from docs
2. Verify all API methods exist
3. Check parameter names and types
4. Validate return value formats

### **Phase 5: Cross-SDK Consistency**
1. Ensure similar APIs across SDKs
2. Verify naming conventions
3. Check error message consistency
4. Validate configuration options

---

## **Success Metrics**
- 100% of documented examples work
- Zero TypeScript/Python type errors
- All acceptance criteria pass
- Clean installation on fresh systems
- Developer can integrate in <5 minutes

---

## **Risk Mitigation**
- **Version Mismatch**: Sync local and NPM versions before testing
- **Breaking Changes**: Test against existing implementations
- **Documentation Drift**: Update docs immediately after fixes
- **Dependency Conflicts**: Use peer dependencies where appropriate
- **Authentication Issues**: Provide clear error messages and fallbacks