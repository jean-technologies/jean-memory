# React + Assistant-UI SDK Testing Prompt

You are tasked with testing and fixing the Jean Memory React SDK + Assistant-UI integration to make it work exactly like the Python SDK does now. Follow the same human-in-the-loop approach we used to successfully fix the Python SDK.

## 📚 Essential Reading

Before starting, read these key documents to understand the context and vision:

1. **Business Vision**: `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md` - Core value proposition
2. **Technical Architecture**: `docs/new/JEAN_MEMORY_SDK_ARCHITECTURE.md` - Current implementation status  
3. **Implementation Progress**: `docs/new/MINIMAL_SDK_MVP_PLAN.md` - What's working vs what needs fixes
4. **Demo Requirements**: `docs/new/VC_DEMO_BUSINESS_CASE.md` - End-to-end user experience goals

## 🎨 Assistant-UI Integration

### About Assistant-UI
**Website**: https://www.assistant-ui.com/  
**Documentation**: https://www.assistant-ui.com/docs/getting-started  
**Examples**: https://www.assistant-ui.com/examples

Assistant-UI is our chosen chat interface library because:
- ✅ **Native MCP Support**: Built-in Model Context Protocol integration
- ✅ **Production Ready**: Professional chat components out of the box
- ✅ **TypeScript First**: Excellent developer experience
- ✅ **Streaming Support**: Real-time message rendering
- ✅ **Composable**: Use only what you need

### Key Assistant-UI Components We Need
```tsx
import { AssistantRuntimeProvider, Thread } from '@assistant-ui/react';
```

## Background Context

### ✅ Python SDK Status (FULLY WORKING)
The Python SDK is now fully functional:
```python
from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
    system_prompt="You are a helpful math tutor"
)
agent.run()  # ✅ FULLY FUNCTIONAL
```

**What Works in Python SDK:**
1. ✅ Authentication: Real "Sign in with Jean" functionality  
2. ✅ Context Retrieval: 4681+ characters of personalized user context
3. ✅ System Prompt: Bot acts as specified role (math tutor, therapist, etc.)
4. ✅ Memory Persistence: New conversations automatically saved to user's memory vault
5. ✅ Multi-tenant: Each user gets isolated memory context
6. ✅ Real AI Integration: OpenAI GPT-4o-mini for intelligent responses

### 🚧 React SDK Status (NEEDS FIXES)
The React SDK exists but has dependency/import issues preventing it from working like the Python version.

## Your Task

**Test and fix the React + Assistant-UI part of the /api-docs page** to work exactly like the Python CLI part does now.

### Target React Code (from /api-docs page)
```tsx
import { SignInWithJean, JeanChat, useJeanAgent } from '@jeanmemory/react';

function MathTutorApp() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a patient math tutor"
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />; // Powered by Assistant-UI
}
```

### Business Case Alignment
From `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md`, this React SDK should deliver:
- **"Sign in with Google for AI memory"** experience
- **5-line integration** for developers  
- **Multi-tenant ready** - each user gets their own memory context
- **Zero infrastructure** - no database, vector store, or LLM setup needed

### Technical Architecture Requirements
From `docs/new/JEAN_MEMORY_SDK_ARCHITECTURE.md`, the React SDK must:
- Use Assistant-UI's `Thread` component for chat interface
- Integrate with our MCP runtime adapter
- Handle authentication via our SDK API endpoints
- Support system prompt injection for personalized AI behaviors

### Expected User Experience
1. User sees "Sign in with Jean" component
2. User enters their Jean Memory email/password
3. Authentication succeeds → `agent` becomes available
4. `<JeanChat agent={agent} />` renders
5. User can chat with assistant that:
   - Acts as the specified system prompt ("patient math tutor")
   - Has access to user's personal Jean Memory context
   - Saves new information to user's memory vault
   - Provides intelligent responses using AI

## Testing Approach

### Phase 1: Initial Assessment
1. **Read the architecture documents** to understand the planned integration
2. **Examine current React SDK files** in `/sdk/react/`
3. **Compare with Assistant-UI documentation** (https://www.assistant-ui.com/docs/getting-started)
4. **Check Assistant-UI examples** (https://www.assistant-ui.com/examples) for integration patterns
5. **Identify the specific import/dependency issues**
6. **Document what's broken vs what needs to be built**

### Phase 2: Fix Dependencies & Imports
1. **Update package.json** with correct Assistant-UI dependencies:
   ```bash
   npm install @assistant-ui/react
   ```
2. **Fix import statements** to use actual Assistant-UI packages:
   ```tsx
   import { AssistantRuntimeProvider, Thread } from '@assistant-ui/react';
   ```
3. **Review Assistant-UI examples** for proper integration patterns
4. **Resolve any TypeScript/React compilation errors**
5. **Test basic component rendering**

### Phase 3: Test Authentication Flow
1. **Test the `useJeanAgent` hook** 
2. **Verify `SignInWithJean` component works**
3. **Test actual authentication with Jean Memory credentials**
4. **Confirm user context is retrieved after authentication**

### Phase 4: Test Chat Integration
1. **Test `JeanChat` component renders**
2. **Verify messages can be sent and received**
3. **Confirm system prompt is being applied**
4. **Test that user's Jean Memory context is being used**
5. **Verify new information is saved to memory vault**

### Phase 5: End-to-End Validation
1. **Test the complete 5-line integration**
2. **Compare functionality to working Python SDK**
3. **Ensure multi-tenant isolation works**
4. **Verify memory persistence across sessions**

## Human-in-the-Loop Process

### After Each Fix:
1. **Commit and push changes** to deploy
2. **Test on actual /api-docs page** (same as Python testing)
3. **Report what works and what doesn't**
4. **Provide screenshots/logs of any errors**
5. **Continue iterating until fully working**

## Key Files to Examine

### Documentation First (READ THESE FIRST)
- `docs/new/JEAN_MEMORY_SDK_ARCHITECTURE.md` - Technical architecture and Assistant-UI integration plan
- `docs/new/MINIMAL_SDK_MVP_PLAN.md` - Implementation status and what's working
- `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md` - Business requirements and user experience
- `docs/new/VC_DEMO_BUSINESS_CASE.md` - End-to-end demo requirements

### Assistant-UI Resources  
- **Documentation**: https://www.assistant-ui.com/docs/getting-started
- **Examples**: https://www.assistant-ui.com/examples  
- **Key patterns**: Runtime providers, Thread components, MCP integration

### React SDK Files
- `/sdk/react/useJeanAgent.ts` - Main hook implementation (likely needs Assistant-UI integration)
- `/sdk/react/package.json` - Dependencies and configuration (likely needs @assistant-ui/react)
- `/sdk/react/README.md` - Usage documentation

### Frontend Integration
- `/openmemory/ui/app/api-docs/page.tsx` - Where the React example is shown (lines 430-496)
- Look for any React SDK demo components

### Backend API (Already Working ✅)
- The backend SDK API endpoints are fully functional
- Authentication: `POST /sdk/auth/login`
- Chat Enhancement: `POST /sdk/chat/enhance`
- Use same API key: `jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA`

## Success Criteria

The React SDK will be considered working when:

1. ✅ **5-Line Integration**: The exact code from /api-docs page works
2. ✅ **Authentication**: "Sign in with Jean" flow works end-to-end
3. ✅ **Context Retrieval**: User gets personalized responses based on their memories  
4. ✅ **System Prompt**: Bot acts as specified role consistently
5. ✅ **Memory Persistence**: New conversations saved to user's vault
6. ✅ **Assistant-UI Integration**: Professional chat interface renders properly
7. ✅ **Multi-tenant**: Each user sees only their own memories

## Business Case Alignment

From the business case documents, this React SDK should deliver the same value proposition as the working Python SDK:

**"Sign in with Google for AI memory"** (from `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md`) - Users can bring their personal context to any React application, while developers get instant personalization without building memory infrastructure.

### Demo Requirements (from VC_DEMO_BUSINESS_CASE.md)
The React SDK will be used in our VC demo showing:
- Health Coach + Career Mentor apps that share user context
- Cross-domain memory sharing (e.g., fitness data informing career advice)
- 5-line integration that "just works"

## Getting Started

1. **READ THE DOCS FIRST**: Start with `docs/new/JEAN_MEMORY_SDK_ARCHITECTURE.md` to understand the intended Assistant-UI integration
2. **Check Assistant-UI examples**: https://www.assistant-ui.com/examples for integration patterns
3. **Examine current React SDK**: Identify what's broken vs what needs to be built
4. **Follow the iterative cycle**: Fix-test-deploy cycle we used successfully for the Python SDK

**Remember**: The backend is working perfectly. The goal is to make the React frontend work as well as the Python CLI does.

## Expected Assistant-UI Integration Pattern

Based on the architecture documents and Assistant-UI examples, the final integration should look like:

```tsx
// Expected final structure from Assistant-UI docs
import { AssistantRuntimeProvider, Thread } from '@assistant-ui/react';
import { createJeanMemoryRuntime } from '@jeanmemory/react';

function JeanChat({ agent }) {
  const runtime = createJeanMemoryRuntime(agent);
  
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="h-full max-h-dvh flex flex-col">
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}
```

**Key Assistant-UI Resources:**  
- **Getting Started**: https://www.assistant-ui.com/docs/getting-started
- **Examples Gallery**: https://www.assistant-ui.com/examples
- **Core Components**: `AssistantRuntimeProvider`, `Thread`, `Composer`

## Important Notes

- Use the same API key: `jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA`
- Test with real Jean Memory credentials (same as Python SDK testing)
- Focus on the /api-docs page integration first
- Keep the human-in-the-loop approach - commit, test, iterate
- The Python SDK is the gold standard - React should match its functionality
- **Study Assistant-UI examples first** before implementing

Good luck! The Python SDK proves the concept works - now make the React version just as powerful using Assistant-UI's professional chat components.