# Jean Memory SDK Suite: Comprehensive Technical Overview

**Version**: 2.0.1  
**Last Updated**: August 2025  
**Status**: Production Ready  
**Architecture**: Multi-Platform Enterprise SDK Suite  

## Executive Summary

The Jean Memory SDK Suite is a comprehensive set of developer tools that make AI memory accessible across all major development platforms. Currently comprising React, Node.js, and Python SDKs, all aligned at version 2.0.1, the suite provides enterprise-grade functionality with OAuth 2.1 PKCE security, cross-platform token sharing, and a unified API architecture.

**Key Value Propositions:**
- **5-Line Integration**: From API key to production-ready AI memory in minutes
- **Universal Platform Support**: React frontends, Node.js backends, Python agents
- **Enterprise Security**: OAuth 2.1 PKCE with secure token exchange
- **Unified Architecture**: Consistent API patterns across all SDKs
- **Production Ready**: Rate limiting, error handling, automatic retry logic
- **Test Mode Support**: Automatic test users for development without OAuth setup

## Architecture Overview

### Multi-SDK Design Philosophy

The Jean Memory SDK architecture follows a **unified API pattern** across all platforms while maintaining platform-specific optimizations:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SDK     │    │   Node.js SDK   │    │   Python SDK    │
│   @1.2.0+       │    │   @1.2.0+       │    │   @1.2.0+       │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • OAuth UI      │    │ • Server Routes │    │ • Agent Backend │
│ • Components    │    │ • API Endpoints │    │ • Data Pipeline │
│ • Hooks         │    │ • Edge Runtime  │    │ • AI Integration│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
              ┌─────────────────────────────────────┐
              │        Unified Core API             │
              │    jean-memory-api-virginia         │
              │         /sdk/chat/enhance           │
              │         OAuth 2.1 PKCE             │
              └─────────────────────────────────────┘
```

### Core API Architecture

All SDKs communicate through a **unified backend API** at `jean-memory-api-virginia.onrender.com`:

**Primary Endpoints:**
- `/sdk/chat/enhance` - Main context retrieval and memory orchestration
- `/auth/oauth/authorize` - OAuth 2.1 PKCE authorization
- `/auth/oauth/token` - Token exchange and refresh
- `/health` - System health and status

**Authentication Flow:**
1. Frontend (React) initiates OAuth 2.1 PKCE flow
2. User completes authentication
3. Frontend receives `user_token`
4. Backend (Node.js/Python) receives token from frontend
5. Backend makes authenticated API calls using token

## React SDK (@jeanmemory/react) - v2.0.1

### Primary Components

**JeanProvider** - Context provider for SDK configuration
```jsx
<JeanProvider apiKey="jean_sk_...">
  <App />
</JeanProvider>
```

**JeanChatComplete** - Drop-in complete chat interface
```jsx
<JeanChatComplete />
```

**SignInWithJean** - OAuth authentication component
```jsx
<SignInWithJean onSuccess={handleAuth} />
```

### Hooks API

**useJeanAuth()** - Authentication state management
```jsx
const { user, token, login, logout, loading } = useJeanAuth();
```

**useJeanMemory()** - Direct memory operations
```jsx
const { storeMemory, getContext, loading } = useJeanMemory();
```

### Use Cases
- Drop-in UI components for rapid prototyping
- Custom chat interfaces with memory integration
- OAuth authentication for user identity
- Real-time context-aware conversations

## Node.js SDK (@jeanmemory/node) - v2.0.1

### Core Client

**JeanClient** - Main SDK client
```typescript
import { JeanClient } from '@jeanmemory/node';

const jean = new JeanClient({ 
  apiKey: process.env.JEAN_API_KEY 
});
```

### Primary Methods

**getContext()** - Intelligent context retrieval
```typescript
const context = await jean.getContext({
  user_token: userToken,
  message: "What's my schedule?",
  speed: "balanced", // fast | balanced | comprehensive
  tool: "jean_memory", // jean_memory | search_memory
  format: "enhanced" // simple | enhanced
});
```

**Tools Namespace** - Direct API access
```typescript
// Memory operations
await jean.tools.add_memory({ user_token, content });
const results = await jean.tools.search_memory({ user_token, query });

// Advanced operations
const deep = await jean.tools.deep_memory_query({ user_token, query });
const doc = await jean.tools.store_document({ 
  user_token, title, content, document_type 
});
```

### Test User Support
The Node.js SDK automatically creates test users when no `user_token` is provided:

```typescript
// Production with OAuth token
const context = await jean.getContext({
  user_token: userToken, // From frontend OAuth
  message: "Hello"
});

// Development with automatic test user  
const context = await jean.getContext({
  // user_token automatically set to test user for this API key
  message: "Hello"
});
```

### Use Cases
- Next.js API routes with edge runtime support
- Express.js backend services
- Serverless functions (Vercel, Netlify, AWS Lambda)
- Real-time streaming responses with AI SDKs

### Integration Patterns

**Next.js API Route Example:**
```typescript
// pages/api/chat.ts
import { JeanClient } from '@jeanmemory/node';
import { OpenAIStream, StreamingTextResponse } from 'ai';

const jean = new JeanClient({ apiKey: process.env.JEAN_API_KEY });

export default async function POST(req: Request) {
  const { messages, userToken } = await req.json();
  
  // Get context from Jean Memory
  const context = await jean.getContext({
    user_token: userToken,
    message: messages[messages.length - 1].content
  });
  
  // Stream response with context
  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo',
    stream: true,
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: `Context: ${context.text}\n\nUser: ${currentMessage}` }
    ]
  });

  return new StreamingTextResponse(OpenAIStream(response));
}
```

## Python SDK (jeanmemory) - v2.0.1

### Core Client

**JeanMemoryClient** - Main SDK client (with JeanClient alias)
```python
from jeanmemory import JeanMemoryClient

jean = JeanMemoryClient(api_key=os.environ.get("JEAN_API_KEY"))
```

### Primary Methods

**get_context()** - Intelligent context retrieval
```python
context = jean.get_context(
    user_token=user_token,
    message="What were the key takeaways from our last meeting?",
    speed="balanced",  # fast | balanced | comprehensive
    tool="jean_memory",  # jean_memory | search_memory  
    format="enhanced"  # simple | enhanced
)
```

**Tools Namespace** - Direct API access
```python
# Memory operations
jean.tools.add_memory(user_token=token, content="Meeting scheduled for Friday")
results = jean.tools.search_memory(user_token=token, query="meetings")

# Advanced operations  
deep_results = jean.tools.deep_memory_query(user_token=token, query="project status")
doc_result = jean.tools.store_document(
    user_token=token, 
    title="Meeting Notes",
    content="...", 
    document_type="markdown"
)
```

### Authentication Options

**Production with OAuth Token:**
```python
# Token received from frontend via OAuth flow
user_token = get_user_token_from_request()
context = jean.get_context(user_token=user_token, message="Hello")
```

**Development with Test User:**
```python
# Automatic test user when user_token is None
context = jean.get_context(user_token=None, message="Hello")
```

**Headless OAuth (Backend-Only):**
```python
# Generate OAuth URL
auth_url = jean.get_auth_url(callback_url="http://localhost:8000/callback")
print(f"Visit: {auth_url}")

# Exchange code for token
user_token = jean.exchange_code_for_token(auth_code)
```

### Use Cases
- AI agent backends with persistent memory
- Data processing pipelines with context
- Chatbot services and APIs  
- Scientific computing with memory layers
- FastAPI/Django/Flask integrations

### Integration Patterns

**FastAPI Integration:**
```python
from fastapi import FastAPI
from jeanmemory import JeanMemoryClient
import openai

app = FastAPI()
jean = JeanMemoryClient(api_key=os.environ.get("JEAN_API_KEY"))

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Get context from Jean Memory
    context = jean.get_context(
        user_token=request.user_token,
        message=request.message
    )
    
    # Generate response with context
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context.text}\n\nUser: {request.message}"}
        ]
    )
    
    return {"response": response.choices[0].message.content}
```

## Cross-SDK Features

### Unified API Pattern

All SDKs implement the same core methods with platform-appropriate signatures:

| Method | React | Node.js | Python |
|--------|-------|---------|--------|
| Context Retrieval | `useJeanMemory().getContext()` | `jean.getContext()` | `jean.get_context()` |
| Memory Storage | `useJeanMemory().storeMemory()` | `jean.tools.add_memory()` | `jean.tools.add_memory()` |
| Memory Search | `useJeanMemory().searchMemory()` | `jean.tools.search_memory()` | `jean.tools.search_memory()` |
| Authentication | `useJeanAuth()` | N/A (token-based) | `jean.get_auth_url()` |

### Configuration Options

All SDKs support the same configuration parameters:

**Speed Control:**
- `fast` - Optimized for speed, less comprehensive context
- `balanced` - Default, balanced speed vs comprehensiveness  
- `comprehensive` - Maximum context depth, slower response

**Tool Selection:**
- `jean_memory` - Default, intelligent context orchestration
- `search_memory` - Direct memory search without orchestration

**Response Format:**
- `enhanced` - Default, full metadata and structured response
- `simple` - Plain text response only

### Error Handling

Consistent error handling patterns across all SDKs:

**Network Errors:**
- Automatic retry with exponential backoff
- Graceful degradation for partial failures
- Clear error messages with actionable guidance

**Authentication Errors:**
- Token expiration handling
- Clear OAuth flow guidance
- Automatic token refresh where possible

**Rate Limiting:**
- Built-in respect for API rate limits
- Queue management for burst requests
- Clear feedback on limit status

## Enterprise Features

### OAuth 2.1 PKCE Security

**Complete Implementation:**
- PKCE (Proof Key for Code Exchange) for enhanced security
- Secure token storage and transmission
- Automatic token refresh
- Cross-domain security measures

**Flow Architecture:**
```
Frontend (React) → OAuth Authorization → Jean Memory Auth Server
       ↓                                           ↓
   User Token ←─────── Token Exchange ←─────── Auth Code
       ↓
Backend (Node.js/Python) ← Token via Request Body
```

### Cross-Platform Token Sharing

**Secure Token Transmission:**
- Frontend obtains token via OAuth
- Backend receives token via secure API calls
- Token validation on every request
- Automatic token refresh handling

### Production-Ready Features

**Rate Limiting & Quotas:**
- Per-API-key rate limiting
- Subscription tier enforcement
- Graceful handling of limit exceeded

**Error Recovery:**
- Automatic retry with backoff
- Circuit breaker patterns
- Fallback strategies for degraded service

**Monitoring & Analytics:**
- Request tracing and logging
- Performance metrics collection
- Usage analytics for optimization

## Version 2.0.1 Release Notes

### Critical Bug Fixes

**Python SDK Exports Restoration:**
- Restored 20+ missing exports in `__init__.py`
- Added `JeanClient` alias for documentation compatibility
- Fixed import paths for all model classes

**Node.js SDK Null Reference Fixes:**
- Fixed `getTestUserToken()` null handling
- Fixed `makeMCPRequest()` null reference bug
- Added comprehensive null checking throughout

**API Endpoint Updates:**
- Updated `store_memory()` to use working `/sdk/chat/enhance`
- Updated `retrieve_memories()` to use working endpoints
- Fixed 401/404 errors from deprecated `/api/v1/` endpoints

### Version Alignment

All SDKs now aligned at version 2.0.1:
- React SDK: 2.0.1
- Node.js SDK: 2.0.1  
- Python SDK: 2.0.1

### Documentation Corrections

- Fixed class name references (JeanClient vs JeanMemoryClient)
- Updated all version references to 2.0.1
- Corrected API endpoint documentation
- Added comprehensive examples for all methods

## Testing & Development

### Test User System

All SDKs support automatic test user creation for development:

**How It Works:**
- When `user_token` is not provided, SDK creates isolated test user
- Test user is tied to specific API key
- All memory operations are isolated per test user
- No OAuth setup required for development

**Usage Patterns:**
```javascript
// Node.js - automatic test user
const context = await jean.getContext({ message: "Hello" });

// Python - automatic test user  
context = jean.get_context(message="Hello")

// React - manual test mode
const { getContext } = useJeanMemory();
const context = await getContext({ message: "Hello" }); // Uses test mode if no auth
```

### SDK Development Tools

**Built-in CLI Tools:**
- Python SDK includes CLI for testing: `jean-cli`
- Node.js SDK includes debug utilities
- React SDK includes development components

**Testing Utilities:**
- Mock clients for unit testing
- Integration test helpers
- Performance benchmarking tools

## Integration Patterns

### Full-Stack Integration

**Typical Architecture:**
```
React Frontend (OAuth) → Node.js Backend (Context) → Python Agent (Intelligence)
                ↓                     ↓                        ↓
            User Token ───────► API Gateway ─────────► Memory Engine
```

**Data Flow:**
1. User authenticates via React SDK OAuth
2. Frontend receives `user_token`
3. Frontend sends requests to Node.js backend with token
4. Backend uses token to get context from Jean Memory
5. Backend integrates context with LLM responses
6. Optional: Python agents process complex queries

### Common Integration Patterns

**Next.js + OpenAI:**
```typescript
// API route with streaming
import { JeanClient } from '@jeanmemory/node';
import { OpenAIStream } from 'ai';

export async function POST(request: Request) {
  const jean = new JeanClient({ apiKey: process.env.JEAN_API_KEY });
  const context = await jean.getContext({ /* ... */ });
  
  const stream = await openai.chat.completions.create({
    stream: true,
    messages: [{ role: "user", content: `Context: ${context.text}...` }]
  });
  
  return new Response(OpenAIStream(stream));
}
```

**FastAPI + Anthropic Claude:**
```python
from fastapi import FastAPI
from jeanmemory import JeanMemoryClient
import anthropic

app = FastAPI()
jean = JeanMemoryClient(api_key=os.environ.get("JEAN_API_KEY"))

@app.post("/chat")
async def chat(request: ChatRequest):
    context = jean.get_context(user_token=request.token, message=request.message)
    
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        messages=[{"role": "user", "content": f"Context: {context.text}\n{request.message}"}]
    )
    
    return {"response": response.content[0].text}
```

## Performance & Scalability

### Response Times

**Typical Performance:**
- Context retrieval: 200-500ms
- Memory storage: 100-300ms  
- Search operations: 150-400ms

**Speed Optimization:**
- `speed="fast"` reduces latency by 40-60%
- CDN-cached responses for common queries
- Connection pooling and keep-alive

### Scalability Features

**Horizontal Scaling:**
- Stateless SDK design
- Load balancer compatible
- Auto-scaling backend infrastructure

**Caching Strategy:**
- Intelligent context caching
- User-specific cache invalidation
- Redis-based distributed caching

## Security Architecture

### Data Protection

**Encryption:**
- TLS 1.3 for all API communications
- At-rest encryption for stored memories
- Zero-knowledge architecture options

**Access Control:**
- API key-based authentication
- User-isolated memory spaces
- Role-based access control (Enterprise)

**Privacy Features:**
- Automatic PII detection and masking
- User data deletion capabilities
- GDPR/CCPA compliance tools

## Future Roadmap

### Planned SDK Additions

**Mobile SDKs:**
- React Native SDK (Q4 2025)
- Flutter SDK (Q1 2026)
- Swift SDK (Q2 2026)

**Additional Language Support:**
- Go SDK (Q4 2025)
- Java SDK (Q1 2026)
- PHP SDK (Q2 2026)

### Feature Enhancements

**Advanced Context Engineering:**
- Multi-modal context (images, documents)
- Real-time context streaming
- Collaborative memory spaces

**Enterprise Features:**
- Single Sign-On (SSO) integration
- Advanced analytics dashboard
- Custom model fine-tuning

## Support & Resources

### Documentation

- **Primary Docs**: https://docs.jeanmemory.com
- **SDK References**: Platform-specific API documentation
- **Integration Guides**: Step-by-step implementation guides
- **Best Practices**: Performance and security guidelines

### Community & Support

- **GitHub Issues**: Bug reports and feature requests
- **Discord Community**: Real-time developer support
- **Enterprise Support**: Dedicated technical account management
- **Professional Services**: Custom integration assistance

---

**Conclusion**

The Jean Memory SDK Suite represents a comprehensive, enterprise-ready solution for adding AI memory capabilities to any application. With consistent APIs across all platforms, robust security, and production-ready features, the SDK suite enables developers to integrate sophisticated memory capabilities in minutes rather than months.

The v2.0.1 release represents a mature, stable foundation for building the next generation of context-aware AI applications.