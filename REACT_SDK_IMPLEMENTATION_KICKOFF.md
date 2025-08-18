# React SDK Implementation Kickoff Prompt

**Context**: You are implementing the Jean Memory React SDK to deliver the full "Sign in with Jean" business case vision. All preparatory analysis is complete, and the code has been reverted to a clean state.

## 🎯 Objective

Transform the basic React SDK into a production-ready implementation that delivers **instant personalized AI responses** matching the business case described in `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md` (lines 54-64).

## 📋 Current Status (Verified Clean State)

✅ **Code reverted successfully**  
✅ **Working reference implementation exists**: `test-react-app/components/useJeanAgentMCP.tsx`  
✅ **Proven working apps available**: `test-react-app/pages/math-tutor.tsx` (and fitness-coach, fashion-coach)  
✅ **Implementation plan ready**: `REACT_SDK_IMPLEMENTATION_GAPS.md`  

## 🏗️ Implementation Task

Replace the current primitive SDK with the proven working MCP-based implementation by following the detailed plan in `REACT_SDK_IMPLEMENTATION_GAPS.md`.

### Phase 1: Core SDK Replacement (Priority: HIGH)

**Primary Task**: Replace `sdk/react/useJeanAgent.tsx` with working MCP implementation

**Source**: Copy and adapt from `test-react-app/components/useJeanAgentMCP.tsx`

**Key Features to Implement**:
1. **MCP Integration**: Use `/mcp/{client}/messages/{user_id}` endpoints
2. **AI Synthesis**: Server-side response generation via `/sdk/synthesize`
3. **Natural Conversations**: Context-aware AI responses (not generic acknowledgments)
4. **Memory Integration**: Proper jean_memory tool usage

**Expected Outcome**: Math tutor behaves like a math tutor, writing coach like a writing coach, etc.

### Phase 2: Assistant-UI Integration (Priority: MEDIUM)

**Task**: Add modern chat UI using `@assistant-ui/react`

**Documentation**: https://www.assistant-ui.com/docs/getting-started

**Benefits**: Professional chat interface, saves development time, better UX

### Phase 3: Documentation & Testing (Priority: HIGH)

**Task**: Update `openmemory/ui/docs-mintlify/sdk/react.mdx` with working examples

**Requirement**: All documentation examples must work out-of-the-box

## 📁 Key Files in This Project

### Files to Modify
- `sdk/react/useJeanAgent.tsx` - **Main implementation target**
- `sdk/react/index.ts` - Update exports if needed
- `openmemory/ui/docs-mintlify/sdk/react.mdx` - Fix documentation examples

### Reference Files (DO NOT MODIFY - Use as Source)
- `test-react-app/components/useJeanAgentMCP.tsx` - **Working implementation to copy from**
- `test-react-app/pages/math-tutor.tsx` - **Working math tutor reference**
- `test-react-app/pages/fitness-coach.tsx` - **Working fitness coach reference**
- `test-react-app/pages/fashion-coach.tsx` - **Working fashion coach reference**

### Planning Documents
- `REACT_SDK_IMPLEMENTATION_GAPS.md` - **Complete implementation plan**
- `docs/new/SIGN_IN_WITH_JEAN_BUSINESS_CASE.md` - **Target vision**

## 🎨 Target API (From Business Case)

The final implementation should support this simple integration:

```jsx
import { JeanAgent } from 'jeanmemory-react';

function WriteWellAI() {
  return <JeanAgent 
    apiKey="jean_sk_bob_api_key_here"
    systemPrompt="You are an expert writing coach who helps improve clarity and engagement"
  />;
}
```

## ✅ Success Criteria

### Must Work Out of the Box:
1. **Math tutor provides actual math tutoring** (not "I can see your context...")
2. **Writing coach provides writing advice** with personal context
3. **Documentation examples work exactly as written**
4. **Authentication flow is seamless**
5. **AI responses are intelligent and contextual**

### Business Case Alignment:
- ✅ **5-line integration** for developers
- ✅ **Instant personalization** for users  
- ✅ **No infrastructure needed** for developers
- ✅ **Context-aware responses** that deliver "wow" moments

## 🚨 Critical Requirements

### What Must Work:
- **Real AI responses**: Not generic acknowledgments
- **Role-specific behavior**: Math tutor != writing coach
- **Personal context**: AI knows user from Jean Memory
- **Natural conversation**: Flows like human chat

### What to Avoid:
- ❌ Generic template responses
- ❌ Hardcoded user-specific logic  
- ❌ Breaking existing functionality
- ❌ Complex backend changes

## 🛠️ Technical Implementation Notes

### Core Pattern (From Working Implementation):
```typescript
// 1. Call MCP jean_memory tool
const memoryResponse = await callJeanMemoryTool(message);

// 2. Synthesize natural response using context
const assistantResponse = await synthesizeNaturalResponse(
  message, 
  context, 
  systemPrompt, 
  hasRichContext
);
```

### API Endpoints (Already Working):
- Authentication: `POST /sdk/auth/login`
- MCP Integration: `POST /mcp/{client}/messages/{user_id}`
- AI Synthesis: `POST /sdk/synthesize`

## 📊 Timeline Estimate

- **Phase 1** (Core SDK): 2-3 hours
- **Phase 2** (Assistant-UI): 1-2 hours  
- **Phase 3** (Docs/Testing): 1 hour
- **Total**: 4-6 hours focused development

## 🔍 How to Start

1. **Read the implementation plan**: `REACT_SDK_IMPLEMENTATION_GAPS.md`
2. **Examine the working reference**: `test-react-app/components/useJeanAgentMCP.tsx`
3. **Test the working apps**: Visit the math-tutor, fitness-coach pages to see expected behavior
4. **Begin Phase 1**: Replace `sdk/react/useJeanAgent.tsx` with MCP implementation

## 💡 Key Success Factors

1. **Copy proven working code** - Don't reinvent what already works
2. **Test frequently** - Use existing working apps as validation
3. **Focus on business case delivery** - Users should get "wow" personalization
4. **Keep changes minimal** - Leverage existing infrastructure

## 🎬 Ready to Begin

Everything is prepared for a successful implementation. The working code exists, the plan is detailed, and the target is clear. Focus on delivering the business case vision: **instant personalized AI that actually works out of the box**.

**Start with Phase 1** and systematically work through the implementation plan. The working reference implementation in `test-react-app/components/useJeanAgentMCP.tsx` already delivers everything needed for the business case.

Good luck! 🚀