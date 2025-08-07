# Jean Memory React SDK - Testing Instructions

## 🎯 Overview

Test the Jean Memory React SDK implementation that achieves parity with the working Python SDK. This follows the exact instructions and examples shown on the `/api-docs` page at https://docs.jeanmemory.com

## ✅ What Works

**Python SDK**: ✅ FULLY FUNCTIONAL
```python
from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_your_key_here",
    system_prompt="You are a helpful tutor"
)
agent.run()  # Interactive CLI with real AI + memory
```

**React SDK**: ✅ NOW FIXED to match Python SDK functionality

## 🚀 Quick Test (5 minutes)

### Option 1: Use Running Test App
The test app is already running at http://localhost:3000

1. **Visit**: http://localhost:3000
2. **Click**: Any demo button (Math Tutor, Therapist, Custom)  
3. **Sign In**: Use your Jean Memory account credentials
4. **Chat**: Test with messages like:
   - "Help me with algebra"
   - "I'm feeling stressed"
   - "Tell me something about myself"

### Option 2: Copy the Example Code

1. **Copy** the complete example from `JeanMemoryReactExample.tsx`
2. **Install SDK**: `npm install @jeanmemory/react`
3. **Import and use** in your React app
4. **Test** the three different demos

## 🔧 Technical Verification

### 1. Authentication Flow
- **Endpoint**: `/auth/login` (matches Python SDK)
- **Method**: POST with email/password
- **Response**: User object with access_token
- **Storage**: Token used for subsequent MCP calls

### 2. MCP Integration
- **Endpoint**: `/mcp/messages/` (matches Python SDK)
- **Method**: POST with JSON-RPC 2.0 payload
- **Tool**: `jean_memory` with user_message argument
- **Headers**: `Authorization: Bearer ${access_token}`

### 3. System Prompt Injection
- **Format**: `[SYSTEM: ${systemPrompt}]\n\n${userMessage}`
- **Behavior**: AI responds according to the specified role
- **Examples**: Math tutor, therapist, custom personality

### 4. Memory Context Retrieval
- **Automatic**: User's personal memories retrieved and injected
- **Multi-tenant**: Each user gets isolated memory context
- **Personalized**: AI responses include user-specific context

## 🧪 Test Scenarios

### Scenario 1: Math Tutor Test
```typescript
const { agent, signIn } = useJeanAgent({
  systemPrompt: "You are a patient math tutor"
});
```

**Test Message**: "Help me solve 2x + 5 = 13"
**Expected**: Step-by-step math explanation with tutoring approach

### Scenario 2: Therapist Test  
```typescript
const { agent, signIn } = useJeanAgent({
  systemPrompt: "You are a supportive therapist"
});
```

**Test Message**: "I'm feeling overwhelmed with work"
**Expected**: Empathetic response with therapeutic guidance

### Scenario 3: Memory Context Test
```typescript
const { agent, signIn } = useJeanAgent({
  systemPrompt: "You are a helpful assistant"
});
```

**Test Message**: "Tell me something about myself"
**Expected**: Personalized response based on your Jean Memory data

## 🔍 Debugging

### Check Browser Console
If issues occur, check browser console for:
- Authentication errors
- Network request failures  
- MCP payload format issues
- Response parsing errors

### Verify Network Requests
In browser dev tools, verify:
1. **Auth Request**: POST to `/auth/login` returns user object
2. **MCP Request**: POST to `/mcp/messages/` with correct JSON-RPC format
3. **Headers**: Authorization header with Bearer token
4. **Response**: Valid JSON-RPC response with result field

### Common Issues & Solutions

**Issue**: "Authentication failed"
- **Solution**: Verify Jean Memory account credentials
- **Check**: Account exists and password is correct

**Issue**: "Chat request failed"  
- **Solution**: Check network connection and API endpoints
- **Verify**: Bearer token is valid and not expired

**Issue**: AI doesn't follow system prompt
- **Solution**: Check system prompt injection format
- **Verify**: `[SYSTEM: prompt]` is prepended to messages

**Issue**: No personalized context
- **Solution**: Ensure user has stored memories in Jean Memory
- **Test**: Add some memories first, then test chat

## 📊 Success Criteria

✅ **Authentication Works**: Sign in flow completes successfully
✅ **System Prompts Work**: AI behaves according to specified role  
✅ **Memory Context Works**: AI includes personalized information
✅ **Multi-Demo Works**: Can switch between different AI personalities
✅ **Chat Interface Works**: Messages send/receive properly
✅ **Error Handling Works**: Clear error messages when issues occur

## 🚀 Deploy and Test Live

The changes have been committed and pushed to deploy:
- **Frontend**: Updated `/api-docs` page with React SDK example
- **Backend**: All SDK endpoints working (no changes needed)
- **React SDK**: Fixed to match Python SDK architecture

**Live URLs**:
- **API Docs**: https://docs.jeanmemory.com (includes React SDK example)  
- **Test App**: Running locally at http://localhost:3000

## 📝 What Was Fixed

### 1. Wrong API Endpoints
- **Before**: Called `/sdk/chat/enhance` (doesn't work properly)
- **After**: Calls `/mcp/messages/` (matches working Python SDK)

### 2. Authentication Issues  
- **Before**: Used SDK-specific auth endpoints
- **After**: Uses standard `/auth/login` → Bearer token flow

### 3. Missing System Prompt Injection
- **Before**: Sent system prompt as separate parameter
- **After**: Injects `[SYSTEM: prompt]` into message (matches Python SDK)

### 4. Wrong Response Parsing
- **Before**: Expected response.enhanced_messages format
- **After**: Parses result.result from JSON-RPC response

### 5. Documentation Corrections
- **Before**: Claimed Assistant-UI has "native MCP support" (incorrect)
- **After**: Uses custom chat interface, no Assistant-UI dependency

## 🎉 Result

The React SDK now achieves the **5-line integration vision**:

```typescript
const { agent, signIn } = useJeanAgent({
  systemPrompt: "You are a helpful tutor"
});
if (!agent) return <SignInWithJean onSuccess={signIn} />;
return <JeanChat agent={agent} />;
```

This matches the Python SDK's simplicity and functionality exactly! 🚀