# Jean Memory SDK Implementation - Human-in-Loop Execution Guide

## Overview
This prompt will guide you through implementing the Jean Memory SDK that enables developers to build multi-tenant AI chatbots with "Sign in with Jean" functionality. We'll follow a human-in-loop pattern: implement → commit → test → validate → repeat until complete.

## Current Git Status
**Branch:** main (up to date with origin/main)
**New files ready for implementation:**
- `docs/new/JEAN_MEMORY_SDK_ARCHITECTURE.md` - Complete architecture documentation
- `docs/new/MINIMAL_SDK_MVP_PLAN.md` - MVP implementation plan
- `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md` - Business case and vision
- `openmemory/api/app/routers/sdk_demo.py` - Core SDK implementation (CREATED)

## Implementation Steps (Human-in-Loop Pattern)

### Phase 1: Register SDK Router
**Goal:** Add the SDK router to FastAPI app and ensure it loads without errors

1. **Implementation Task:**
   - Add `sdk_demo` router to `/openmemory/api/app/main.py`
   - Follow existing router registration patterns (see how `keys`, `local_auth` routers are added)
   - Ensure proper import: `from app.routers import sdk_demo`
   - Add router: `app.include_router(sdk_demo.router)`

2. **Commit & Deploy:**
   ```bash
   git add openmemory/api/app/routers/sdk_demo.py
   git add openmemory/api/app/main.py  # (after modification)
   git commit -m "Add Jean Memory SDK router with authentication and chat enhancement endpoints"
   git push origin main
   ```

3. **Test & Validate:**
   - Start the FastAPI server locally
   - Check server logs for any import/startup errors
   - Visit `/docs` endpoint to verify SDK endpoints appear
   - Test `/sdk/health` endpoint returns 200 OK
   - **HUMAN CHECKPOINT:** Provide screenshots of:
     - Server startup logs (success/error)
     - `/docs` page showing SDK endpoints
     - `/sdk/health` response

4. **If Issues Found:** Provide error logs/screenshots → I'll debug and fix → repeat step

---

### Phase 2: Test Authentication Flow
**Goal:** Verify user authentication works through SDK

1. **Implementation Task:**
   - No code changes needed - test existing `/sdk/auth/login` endpoint
   - Use existing Supabase users or create test user via `/local-auth/create-user` (if in local dev)

2. **Test & Validate:**
   - POST to `/sdk/auth/login` with valid credentials:
     ```json
     {
       "email": "test@example.com",
       "password": "testpassword"
     }
     ```
   - Verify response contains `user_id`, `access_token`, etc.
   - Check server logs for authentication success
   - **HUMAN CHECKPOINT:** Provide screenshots of:
     - Successful login response
     - Server logs showing authentication
     - Any error responses if login fails

3. **If Issues Found:** Provide error details → I'll debug authentication flow → repeat

---

### Phase 3: Test API Key Validation
**Goal:** Verify developer API key validation works

1. **Prerequisites:**
   - Need a valid `jean_sk_*` API key from your system
   - Check existing API keys via `/api/v1/keys` endpoint

2. **Test & Validate:**
   - POST to `/sdk/validate-developer` with valid API key:
     ```json
     {
       "api_key": "jean_sk_your_actual_key_here",
       "client_name": "TestChatbot"
     }
     ```
   - Verify successful validation response
   - Test with invalid API key to ensure proper error handling
   - **HUMAN CHECKPOINT:** Provide screenshots of:
     - Successful API key validation
     - Invalid API key error response
     - Server logs

3. **If Issues Found:** Provide error details → I'll fix validation logic → commit → repeat

---

### Phase 4: Test Context Enhancement (Core Feature)
**Goal:** Verify chat enhancement with Jean Memory context works

1. **Prerequisites:**
   - Valid API key from Phase 3
   - Valid user_id from Phase 2
   - Existing memory data for the user (or create some via existing MCP tools)

2. **Test & Validate:**
   - POST to `/sdk/chat/enhance` with test conversation:
     ```json
     {
       "api_key": "jean_sk_your_key",
       "client_name": "TestChatbot",
       "user_id": "user_id_from_phase_2",
       "messages": [
         {"role": "user", "content": "What do you know about my recent projects?"}
       ],
       "system_prompt": "You are a helpful assistant with access to user context."
     }
     ```
   - Verify `enhanced_messages` includes system prompt with context
   - Check `context_retrieved` and `user_context` fields
   - **HUMAN CHECKPOINT:** Provide screenshots of:
     - Full chat enhancement response
     - Server logs showing jean_memory tool execution
     - Any MCP-related logs

3. **If Issues Found:** Provide error details → I'll debug MCP integration → commit → repeat

---

### Phase 5: Integration Testing & Documentation
**Goal:** End-to-end testing and create developer documentation

1. **Implementation Task:**
   - Create simple test script demonstrating full SDK flow
   - Update documentation with actual endpoint URLs and examples

2. **Test & Validate:**
   - Run complete flow: login → validate API key → enhance chat
   - Test error scenarios (invalid tokens, missing data, etc.)
   - Verify all logging works correctly
   - **HUMAN CHECKPOINT:** Provide:
     - Complete test script execution logs
     - Screenshots of all endpoints working
     - Performance metrics (response times)

3. **Final Commit:**
   ```bash
   git add docs/new/
   git commit -m "Complete Jean Memory SDK implementation with testing and documentation"
   git push origin main
   ```

---

## Key Files to Monitor During Implementation

**Core Implementation:**
- `/openmemory/api/app/routers/sdk_demo.py` - Main SDK logic
- `/openmemory/api/app/main.py` - Router registration
- `/openmemory/api/app/auth.py` - Authentication dependencies
- `/openmemory/api/app/tools/orchestration.py` - MCP jean_memory tool

**Documentation:**
- `/docs/new/JEAN_MEMORY_SDK_ARCHITECTURE.md` - Technical architecture
- `/docs/new/MINIMAL_SDK_MVP_PLAN.md` - Implementation plan
- `/docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md` - Business case

## Debugging Checkpoints

At each phase, if issues occur, provide:
1. **Error logs** - Full server logs showing the error
2. **Request/Response** - Exact API calls made and responses received  
3. **Screenshots** - UI/docs pages showing the issue
4. **Environment info** - Local vs production, any special config

## Success Criteria

✅ **Phase 1:** SDK endpoints appear in `/docs`, health check works
✅ **Phase 2:** User authentication returns valid tokens
✅ **Phase 3:** API key validation works for developers
✅ **Phase 4:** Chat enhancement retrieves and injects user context
✅ **Phase 5:** Complete end-to-end flow works reliably

## Final Goal
Enable developers to integrate "Sign in with Jean" functionality into their AI chatbots with just a few API calls, providing seamless access to user's Jean Memory context for personalized AI interactions.

---

**Next Step:** Start with Phase 1 - Register the SDK router in your FastAPI application and let me know when you're ready to begin!