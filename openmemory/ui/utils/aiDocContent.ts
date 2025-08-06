/**
 * AI-Optimized Documentation Content Generators
 * These functions generate complete, AI-readable documentation that can be directly
 * pasted into Claude, ChatGPT, or other AI assistants for immediate implementation.
 */

export const generateQuickstartAIContent = () => `# Jean Memory - AI Implementation Guide

## IMMEDIATE IMPLEMENTATION - 5 LINES OF CODE

You are about to implement Jean Memory, a personal memory layer for AI applications. This guide contains everything needed for immediate implementation.

## WHAT IS JEAN MEMORY?
Jean Memory provides persistent, personalized context for AI applications. Users' memories follow them across the internet.

## AUTHENTICATION REQUIREMENT
- Developer provides API key: jean_sk_...
- Users sign in with their Jean Memory account
- Complete isolation between users

## COMPLETE IMPLEMENTATION EXAMPLES

### REACT IMPLEMENTATION (COPY THIS EXACTLY)
\`\`\`tsx
// 1. Install: npm install @jeanmemory/react

// 2. Complete implementation in App.tsx:
import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function App() {
  const { agent, signIn } = useJeanAgent({
    apiKey: "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA", // Replace with your key
    systemPrompt: "You are a helpful assistant with access to user's personal context"
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />;
}

export default App;
\`\`\`

### PYTHON IMPLEMENTATION (COPY THIS EXACTLY)
\`\`\`python
# 1. Install: pip install jeanmemory

# 2. Complete implementation in app.py:
from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",  # Replace with your key
    system_prompt="You are a helpful assistant with access to user's personal context"
)

# Run the interactive chat
agent.run()
\`\`\`

### NODE.JS IMPLEMENTATION (COPY THIS EXACTLY)
\`\`\`javascript
// 1. Install: npm install @jeanmemory/node

// 2. Complete implementation in app.js:
import { JeanAgent } from '@jeanmemory/node';

const agent = new JeanAgent({
  apiKey: "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA", // Replace with your key
  systemPrompt: "You are a helpful assistant with access to user's personal context"
});

await agent.run();
\`\`\`

## API KEY INSTRUCTIONS
1. Go to https://jeanmemory.com/signup
2. Create account
3. Navigate to API Keys section
4. Create new API key
5. Replace placeholder in code above

## WHAT HAPPENS AUTOMATICALLY
- User authentication handled by SDK
- Memory retrieval happens automatically
- Context injection into AI responses
- Complete user isolation
- Secure memory storage

## SYSTEM PROMPT EXAMPLES

### Education Tutor
\`\`\`
You are a patient math tutor who remembers the student's learning style, weak areas, and progress over time. Adapt explanations based on their understanding level.
\`\`\`

### Customer Support
\`\`\`
You are a customer support agent with access to the customer's purchase history, past issues, and preferences. Provide personalized solutions.
\`\`\`

### Health Coach
\`\`\`
You are a fitness coach who knows the user's goals, dietary preferences, workout history, and progress. Provide personalized recommendations.
\`\`\`

## ENVIRONMENT VARIABLES
\`\`\`bash
# .env file
JEAN_API_KEY=jean_sk_your_actual_api_key_here
\`\`\`

## TESTING THE IMPLEMENTATION
1. Run the application
2. User clicks "Sign in with Jean"
3. User authenticates with their account
4. Chat interface appears
5. User messages include their personal context automatically

## PRODUCTION DEPLOYMENT
- API key in environment variables only
- Never commit API keys to version control
- Use HTTPS in production
- Rate limits: 100 req/min (free), 1000 req/min (pro)

## IMMEDIATE NEXT STEPS FOR AI AGENT
1. Create new project directory
2. Install the appropriate SDK
3. Copy the implementation code exactly
4. Add API key to environment variables
5. Run the application
6. Test with sample user authentication

## COMMON PATTERNS

### Storing New Memories
\`\`\`javascript
agent.addMemory("User prefers dark mode");
\`\`\`

### Searching Memories
\`\`\`javascript
const memories = await agent.searchMemory("preferences");
\`\`\`

### Getting Conversation History
\`\`\`javascript
const history = agent.getConversationHistory();
\`\`\`

## SUCCESS CRITERIA
✅ Application runs without errors
✅ Sign in button appears
✅ User can authenticate
✅ Chat interface loads
✅ Responses include personalized context

## ERROR HANDLING
- Invalid API key: Check key format (jean_sk_...)
- Authentication fails: Verify user has Jean Memory account
- No context retrieved: Normal for new users with no memories

## SUPPORT
- Documentation: https://jeanmemory.com/api-docs
- GitHub: https://github.com/jean-technologies/jean-memory
- Discord: https://discord.gg/jeanmemory

END OF IMPLEMENTATION GUIDE - COPY EVERYTHING ABOVE`;

export const generateSDKAIContent = () => `# Jean Memory SDK - Complete AI Implementation Reference

## PURPOSE
This document contains complete SDK implementation details for Jean Memory across React, Python, and Node.js. An AI agent can use this to implement any SDK feature.

## REACT SDK COMPLETE REFERENCE

### Installation
\`\`\`bash
npm install @jeanmemory/react
\`\`\`

### Core Hook - useJeanAgent
\`\`\`typescript
import { useJeanAgent } from '@jeanmemory/react';

const {
  agent,           // Assistant-UI compatible agent
  user,            // Current authenticated user
  messages,        // Conversation history
  isLoading,       // Loading state
  error,           // Error state
  signIn,          // Authentication function
  signOut,         // Sign out function
  sendMessage      // Send message function
} = useJeanAgent({
  apiKey: "jean_sk_...",
  systemPrompt: "Your system prompt here",
  clientName: "My App"
});
\`\`\`

### Components

#### SignInWithJean Component
\`\`\`tsx
<SignInWithJean 
  onSuccess={(user) => console.log('Signed in:', user)}
  apiKey="jean_sk_..."
  className="custom-button-class"
/>
\`\`\`

#### JeanChat Component
\`\`\`tsx
<JeanChat 
  agent={agent}
  className="h-96 border rounded"
/>
\`\`\`

### Complete React Example
\`\`\`tsx
import React from 'react';
import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function PersonalizedApp() {
  const { agent, signIn, user, error, sendMessage } = useJeanAgent({
    apiKey: process.env.REACT_APP_JEAN_API_KEY,
    systemPrompt: "You are a helpful assistant"
  });

  // Handle authentication
  if (!agent) {
    return (
      <div>
        <h1>Welcome</h1>
        {error && <p>Error: {error}</p>}
        <SignInWithJean onSuccess={signIn} />
      </div>
    );
  }

  // Authenticated view
  return (
    <div>
      <h1>Hello, {user?.email}</h1>
      <JeanChat agent={agent} />
      
      {/* Or custom implementation */}
      <button onClick={() => sendMessage("Hello!")}>
        Send Custom Message
      </button>
    </div>
  );
}
\`\`\`

## PYTHON SDK COMPLETE REFERENCE

### Installation
\`\`\`bash
pip install jeanmemory
\`\`\`

### Core Class - JeanAgent
\`\`\`python
from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_...",
    system_prompt="Your system prompt",
    modality="chat",
    client_name="Python App"
)
\`\`\`

### Methods

#### Authentication
\`\`\`python
# Interactive (prompts for credentials)
agent.authenticate()

# With credentials
agent.authenticate("user@example.com", "password")
\`\`\`

#### Sending Messages
\`\`\`python
response = agent.send_message("What did we discuss yesterday?")
print(response)
\`\`\`

#### Interactive Chat
\`\`\`python
agent.run(auto_auth=True)  # Starts interactive terminal chat
\`\`\`

#### Conversation History
\`\`\`python
history = agent.get_conversation_history()
for message in history:
    print(f"{message['role']}: {message['content']}")
\`\`\`

#### Clear Conversation
\`\`\`python
agent.clear_conversation()
\`\`\`

### Complete Python Example
\`\`\`python
from jeanmemory import JeanAgent
import os

class PersonalAssistant:
    def __init__(self):
        self.agent = JeanAgent(
            api_key=os.getenv("JEAN_API_KEY"),
            system_prompt=\"\"\"You are a personal assistant who:
            - Remembers all past conversations
            - Knows user preferences
            - Provides personalized recommendations
            \"\"\"
        )
    
    def start_session(self):
        print("Authenticating...")
        if self.agent.authenticate():
            print("Connected to Jean Memory!")
            return True
        return False
    
    def chat(self, message):
        return self.agent.send_message(message)
    
    def interactive_mode(self):
        self.agent.run()

# Usage
assistant = PersonalAssistant()
if assistant.start_session():
    # Option 1: Programmatic
    response = assistant.chat("What are my goals for this week?")
    print(response)
    
    # Option 2: Interactive
    assistant.interactive_mode()
\`\`\`

## NODE.JS SDK COMPLETE REFERENCE

### Installation
\`\`\`bash
npm install @jeanmemory/node
\`\`\`

### Core Class - JeanAgent
\`\`\`javascript
import { JeanAgent } from '@jeanmemory/node';

const agent = new JeanAgent({
  apiKey: "jean_sk_...",
  systemPrompt: "Your system prompt",
  clientName: "Node App",
  model: "gpt-4"
});
\`\`\`

### Methods

#### Authentication
\`\`\`javascript
// Interactive
await agent.authenticate();

// With credentials
const success = await agent.authenticate('user@example.com', 'password');
\`\`\`

#### Sending Messages
\`\`\`javascript
const response = await agent.sendMessage("Tell me about my project");
console.log(response);
\`\`\`

#### Interactive Chat
\`\`\`javascript
await agent.run(true);  // Auto-authenticate
\`\`\`

#### Conversation History
\`\`\`javascript
const history = agent.getConversationHistory();
history.forEach(msg => console.log(\`\${msg.role}: \${msg.content}\`));
\`\`\`

### Complete Node.js Example
\`\`\`javascript
import { JeanAgent } from '@jeanmemory/node';
import express from 'express';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(express.json());

// Initialize agent
const agent = new JeanAgent({
  apiKey: process.env.JEAN_API_KEY,
  systemPrompt: "You are a helpful API assistant"
});

// Endpoint for chat
app.post('/chat', async (req, res) => {
  const { userId, message } = req.body;
  
  try {
    // Each user has isolated memory
    const response = await agent.sendMessage(message, {
      userId: userId
    });
    
    res.json({ response });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(3000, () => {
  console.log('Jean Memory API running on port 3000');
});
\`\`\`

## ADVANCED PATTERNS

### Multi-User Support (Isolated Memories)
\`\`\`javascript
// Each user has completely isolated memory space
const response = await agent.sendMessage(message, {
  userId: 'user-123'  // Unique user identifier
});
\`\`\`

### Custom System Prompts by Context
\`\`\`javascript
const tutorAgent = new JeanAgent({
  apiKey: API_KEY,
  systemPrompt: \`You are a \${subject} tutor for \${gradeLevel} students\`
});
\`\`\`

### Error Handling
\`\`\`javascript
try {
  const response = await agent.sendMessage(message);
  return response;
} catch (error) {
  if (error.code === 'AUTH_FAILED') {
    // Re-authenticate
    await agent.authenticate();
  } else if (error.code === 'RATE_LIMIT') {
    // Wait and retry
    await new Promise(r => setTimeout(r, 60000));
  }
}
\`\`\`

## CONFIGURATION OPTIONS

### React Configuration
\`\`\`typescript
interface JeanAgentConfig {
  apiKey?: string;           // Your API key
  systemPrompt?: string;     // AI behavior definition
  clientName?: string;       // Client identifier
  baseUrl?: string;          // API endpoint (default: production)
}
\`\`\`

### Python Configuration
\`\`\`python
JeanAgent(
    api_key: str,              # Required
    system_prompt: str = "...", # Optional
    modality: str = "chat",    # chat or completion
    client_name: str = "..."   # Optional identifier
)
\`\`\`

### Node.js Configuration
\`\`\`javascript
{
  apiKey: string,           // Required
  systemPrompt?: string,    // Optional
  clientName?: string,      // Optional
  model?: string            // AI model selection
}
\`\`\`

## IMPLEMENTATION CHECKLIST FOR AI AGENTS

When implementing Jean Memory:

1. ✅ Choose appropriate SDK (React for web, Python for scripts, Node for servers)
2. ✅ Install SDK package
3. ✅ Set up environment variables for API key
4. ✅ Initialize agent with system prompt
5. ✅ Implement authentication flow
6. ✅ Handle errors gracefully
7. ✅ Test with sample messages
8. ✅ Verify memory persistence
9. ✅ Check user isolation (multi-user apps)
10. ✅ Deploy with secure API key management

## COMPLETE TEST SUITE
\`\`\`javascript
// Test authentication
const authSuccess = await agent.authenticate();
assert(authSuccess === true);

// Test message sending
const response = await agent.sendMessage("Hello");
assert(response.length > 0);

// Test memory persistence
await agent.addMemory("Test memory");
const search = await agent.searchMemory("test");
assert(search.results.length > 0);

// Test conversation history
const history = agent.getConversationHistory();
assert(Array.isArray(history));

// Test user isolation
const user1Response = await agent.sendMessage("Hi", { userId: "user1" });
const user2Response = await agent.sendMessage("Hi", { userId: "user2" });
assert(user1Response !== user2Response);
\`\`\`

END OF SDK REFERENCE - IMPLEMENT ANY FEATURE USING THE ABOVE`;

export const generateMCPAIContent = () => `# Jean Memory MCP Protocol - Complete AI Implementation Guide

## PURPOSE
Complete MCP (Model Context Protocol) implementation guide for integrating Jean Memory with AI assistants like Claude, ChatGPT, and Cursor.

## WHAT IS MCP?
MCP is a standardized protocol that allows AI assistants to discover and use external tools. Jean Memory implements MCP to provide memory tools to AI assistants.

## QUICK SETUP FOR EACH PLATFORM

### CLAUDE DESKTOP SETUP
\`\`\`json
// File: ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "jean-memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-jean-memory"],
      "env": {
        "JEAN_API_KEY": "jean_sk_your_api_key_here"
      }
    }
  }
}
\`\`\`

### CHATGPT CUSTOM GPT ACTION
\`\`\`json
{
  "openapi": "3.0.0",
  "info": {
    "title": "Jean Memory MCP",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://jean-memory-api-virginia.onrender.com"
    }
  ],
  "paths": {
    "/mcp/messages/": {
      "post": {
        "operationId": "callJeanMemory",
        "summary": "Execute Jean Memory tools",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/MCPRequest"
              }
            }
          }
        }
      }
    }
  }
}
\`\`\`

### CURSOR SETUP
\`\`\`json
// File: ~/.cursor/config.json
{
  "mcpServers": {
    "jean-memory": {
      "command": "node",
      "args": ["/path/to/jean-memory-mcp-server.js"],
      "env": {
        "JEAN_API_KEY": "jean_sk_your_api_key_here"
      }
    }
  }
}
\`\`\`

## MCP PROTOCOL IMPLEMENTATION

### Endpoint
\`\`\`
POST https://jean-memory-api-virginia.onrender.com/mcp/messages/
\`\`\`

### Authentication Headers
\`\`\`http
Authorization: Bearer <oauth_token>
X-Client-Name: claude-desktop
X-User-Id: <user_id>
\`\`\`

### Initialize Request
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true }
    },
    "clientInfo": {
      "name": "claude-desktop",
      "version": "1.0.0"
    }
  },
  "id": 1
}
\`\`\`

### Tool Discovery Request
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}
\`\`\`

## AVAILABLE MCP TOOLS

### 1. jean_memory - Primary Context Tool
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "jean_memory",
    "arguments": {
      "user_message": "What did I work on last week?",
      "is_new_conversation": true,
      "needs_context": true
    }
  },
  "id": 1
}
\`\`\`

### 2. add_memories - Store Information
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "add_memories",
    "arguments": {
      "text": "User prefers TypeScript for all new projects",
      "tags": ["preferences", "programming"]  // API users only
    }
  },
  "id": 2
}
\`\`\`

### 3. search_memory - Search Memories
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_memory",
    "arguments": {
      "query": "project deadlines",
      "limit": 10
    }
  },
  "id": 3
}
\`\`\`

### 4. search_memory_v2 - Advanced Search (API Key Only)
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_memory_v2",
    "arguments": {
      "query": "meeting notes",
      "tags_filter": ["work", "project-alpha"],
      "limit": 20
    }
  },
  "id": 4
}
\`\`\`

### 5. store_document - Store Large Documents
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "store_document",
    "arguments": {
      "title": "Architecture Documentation",
      "content": "# System Architecture\\n\\nComplete document content...",
      "document_type": "markdown"
    }
  },
  "id": 5
}
\`\`\`

### 6. list_memories - List All Memories
\`\`\`json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list_memories",
    "arguments": {
      "limit": 50,
      "offset": 0
    }
  },
  "id": 6
}
\`\`\`

## OAUTH 2.1 AUTHENTICATION FLOW

### OAuth Discovery
\`\`\`
GET /.well-known/oauth-authorization-server
\`\`\`

### OAuth Endpoints
- Authorize: \`/oauth/authorize\`
- Token: \`/oauth/token\`
- Register: \`/oauth/register\`

### PKCE Flow Implementation
\`\`\`javascript
// 1. Generate code verifier and challenge
const codeVerifier = generateRandomString(128);
const codeChallenge = sha256(codeVerifier);

// 2. Redirect to authorize
const authUrl = \`/oauth/authorize?
  client_id=\${clientId}&
  redirect_uri=\${redirectUri}&
  code_challenge=\${codeChallenge}&
  code_challenge_method=S256&
  response_type=code&
  scope=memory:read memory:write\`;

// 3. Exchange code for token
const tokenResponse = await fetch('/oauth/token', {
  method: 'POST',
  body: JSON.stringify({
    grant_type: 'authorization_code',
    code: authCode,
    redirect_uri: redirectUri,
    code_verifier: codeVerifier
  })
});
\`\`\`

## COMPLETE IMPLEMENTATION EXAMPLE

### Custom MCP Server Implementation
\`\`\`javascript
import express from 'express';
import { JeanMemoryMCP } from '@jeanmemory/mcp';

const app = express();
app.use(express.json());

const mcp = new JeanMemoryMCP({
  apiKey: process.env.JEAN_API_KEY
});

// MCP endpoint
app.post('/mcp/messages/', async (req, res) => {
  const { method, params, id } = req.body;
  
  try {
    let result;
    
    switch(method) {
      case 'initialize':
        result = {
          protocolVersion: "2024-11-05",
          serverInfo: {
            name: "jean-memory",
            version: "1.0.0"
          },
          capabilities: {
            tools: true
          }
        };
        break;
        
      case 'tools/list':
        result = {
          tools: [
            {
              name: "jean_memory",
              description: "Retrieve personalized context",
              inputSchema: {
                type: "object",
                properties: {
                  user_message: { type: "string" },
                  is_new_conversation: { type: "boolean" },
                  needs_context: { type: "boolean" }
                },
                required: ["user_message", "is_new_conversation"]
              }
            },
            // ... other tools
          ]
        };
        break;
        
      case 'tools/call':
        result = await mcp.callTool(params.name, params.arguments);
        break;
    }
    
    res.json({
      jsonrpc: "2.0",
      result,
      id
    });
  } catch (error) {
    res.json({
      jsonrpc: "2.0",
      error: {
        code: -32603,
        message: error.message
      },
      id
    });
  }
});

app.listen(3000);
\`\`\`

## TESTING MCP INTEGRATION

### Test with cURL
\`\`\`bash
# Initialize
curl -X POST https://jean-memory-api-virginia.onrender.com/mcp/messages/ \\
  -H "X-Api-Key: jean_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05"
    },
    "id": 1
  }'

# List tools
curl -X POST https://jean-memory-api-virginia.onrender.com/mcp/messages/ \\
  -H "X-Api-Key: jean_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
  }'

# Call jean_memory tool
curl -X POST https://jean-memory-api-virginia.onrender.com/mcp/messages/ \\
  -H "X-Api-Key: jean_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "jean_memory",
      "arguments": {
        "user_message": "What are my current projects?",
        "is_new_conversation": true,
        "needs_context": true
      }
    },
    "id": 3
  }'
\`\`\`

## TROUBLESHOOTING MCP

### Tools Not Appearing
1. Verify API key is correct
2. Restart AI assistant completely
3. Check MCP server logs
4. Ensure proper JSON formatting

### Authentication Failures
1. Clear OAuth cache
2. Re-authenticate user
3. Check redirect URI configuration
4. Verify Jean Memory account is active

### Performance Issues
- MCP adds 100-200ms overhead
- First request slower due to initialization
- Consider SDK for production apps
- Use caching for frequently accessed memories

## CLIENT-SPECIFIC CONSIDERATIONS

### Claude Desktop
- Simplified toolset for stability
- No metadata/tags support
- Automatic OAuth handling

### ChatGPT
- Requires Custom GPT Action setup
- Supports full API features with API key
- Manual OAuth configuration

### Cursor
- Full MCP protocol support
- Integrated with code editor
- Supports all tools

## IMPLEMENTATION CHECKLIST

1. ✅ Choose MCP client (Claude/ChatGPT/Cursor)
2. ✅ Get Jean Memory API key
3. ✅ Configure MCP server in client
4. ✅ Restart client application
5. ✅ Verify tools appear in UI
6. ✅ Test jean_memory tool
7. ✅ Test add_memories tool
8. ✅ Verify memory persistence
9. ✅ Check OAuth flow (if applicable)
10. ✅ Monitor performance

END OF MCP IMPLEMENTATION GUIDE`;

export const generateRestAPIContent = () => `# Jean Memory REST API - Complete Implementation Reference

## BASE URL
\`\`\`
https://jean-memory-api-virginia.onrender.com
\`\`\`

## AUTHENTICATION

### Method 1: API Key (Recommended)
\`\`\`http
X-Api-Key: jean_sk_your_api_key_here
\`\`\`

### Method 2: Bearer Token (Supabase JWT)
\`\`\`http
Authorization: Bearer <jwt_token>
\`\`\`

## COMPLETE API ENDPOINTS

### Memory Operations

#### List Memories
\`\`\`bash
GET /api/v1/memories?search_query=typescript&categories=work&limit=50&offset=0

curl -X GET "https://jean-memory-api-virginia.onrender.com/api/v1/memories?limit=10" \\
  -H "X-Api-Key: jean_sk_..."
\`\`\`

Response:
\`\`\`json
{
  "memories": [
    {
      "id": "mem_123",
      "content": "User prefers TypeScript",
      "categories": ["preferences", "programming"],
      "created_at": "2024-01-15T10:00:00Z",
      "metadata": {
        "tags": ["work", "tech-stack"]
      }
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
\`\`\`

#### Create Memory
\`\`\`bash
POST /api/v1/memories

curl -X POST "https://jean-memory-api-virginia.onrender.com/api/v1/memories" \\
  -H "X-Api-Key: jean_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Important project deadline on March 15th",
    "metadata": {
      "tags": ["work", "deadlines", "project-alpha"]
    }
  }'
\`\`\`

#### Update Memory
\`\`\`bash
PATCH /api/v1/memories/{memory_id}

curl -X PATCH "https://jean-memory-api-virginia.onrender.com/api/v1/memories/mem_123" \\
  -H "X-Api-Key: jean_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Updated deadline to March 20th",
    "metadata": {
      "tags": ["work", "deadlines", "project-alpha", "updated"]
    }
  }'
\`\`\`

#### Delete Memory
\`\`\`bash
DELETE /api/v1/memories/{memory_id}

curl -X DELETE "https://jean-memory-api-virginia.onrender.com/api/v1/memories/mem_123" \\
  -H "X-Api-Key: jean_sk_..."
\`\`\`

### MCP Tools via REST

#### Execute MCP Tool
\`\`\`bash
POST /mcp/messages/

curl -X POST "https://jean-memory-api-virginia.onrender.com/mcp/messages/" \\
  -H "X-Api-Key: jean_sk_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_memory_v2",
      "arguments": {
        "query": "meeting notes",
        "tags_filter": ["work", "meetings"]
      }
    },
    "id": 1
  }'
\`\`\`

### App Management

#### List Apps
\`\`\`bash
GET /api/v1/apps

curl -X GET "https://jean-memory-api-virginia.onrender.com/api/v1/apps" \\
  -H "Authorization: Bearer <jwt_token>"
\`\`\`

#### Sync App
\`\`\`bash
POST /api/v1/apps/{app_id}/sync

curl -X POST "https://jean-memory-api-virginia.onrender.com/api/v1/apps/app_123/sync" \\
  -H "Authorization: Bearer <jwt_token>"
\`\`\`

### API Key Management

#### Create API Key
\`\`\`bash
POST /api/v1/keys

curl -X POST "https://jean-memory-api-virginia.onrender.com/api/v1/keys" \\
  -H "Authorization: Bearer <jwt_token>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Production API Key",
    "permissions": ["read", "write"]
  }'
\`\`\`

#### List API Keys
\`\`\`bash
GET /api/v1/keys

curl -X GET "https://jean-memory-api-virginia.onrender.com/api/v1/keys" \\
  -H "Authorization: Bearer <jwt_token>"
\`\`\`

#### Revoke API Key
\`\`\`bash
DELETE /api/v1/keys/{key_id}

curl -X DELETE "https://jean-memory-api-virginia.onrender.com/api/v1/keys/key_123" \\
  -H "Authorization: Bearer <jwt_token>"
\`\`\`

## PYTHON IMPLEMENTATION

\`\`\`python
import requests
import json
import os

class JeanMemoryAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://jean-memory-api-virginia.onrender.com"
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def list_memories(self, search_query=None, tags=None, limit=50):
        params = {"limit": limit}
        if search_query:
            params["search_query"] = search_query
        if tags:
            params["tags"] = ",".join(tags)
        
        response = requests.get(
            f"{self.base_url}/api/v1/memories",
            headers=self.headers,
            params=params
        )
        return response.json()
    
    def create_memory(self, content, tags=None):
        data = {"content": content}
        if tags:
            data["metadata"] = {"tags": tags}
        
        response = requests.post(
            f"{self.base_url}/api/v1/memories",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def search_with_tags(self, query, tags_filter):
        data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_memory_v2",
                "arguments": {
                    "query": query,
                    "tags_filter": tags_filter
                }
            },
            "id": 1
        }
        
        response = requests.post(
            f"{self.base_url}/mcp/messages/",
            headers=self.headers,
            json=data
        )
        return response.json()

# Usage
api = JeanMemoryAPI("jean_sk_...")

# Create memory
api.create_memory(
    "Project meeting at 3pm tomorrow",
    tags=["work", "meetings", "tomorrow"]
)

# Search memories
results = api.list_memories(search_query="meeting")

# Advanced search with tags
filtered = api.search_with_tags(
    "project updates",
    tags_filter=["work", "project-alpha"]
)
\`\`\`

## JAVASCRIPT/NODE IMPLEMENTATION

\`\`\`javascript
class JeanMemoryAPI {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://jean-memory-api-virginia.onrender.com';
  }
  
  async listMemories(searchQuery = null, tags = null, limit = 50) {
    const params = new URLSearchParams({ limit });
    if (searchQuery) params.append('search_query', searchQuery);
    if (tags) params.append('tags', tags.join(','));
    
    const response = await fetch(\`\${this.baseUrl}/api/v1/memories?\${params}\`, {
      headers: {
        'X-Api-Key': this.apiKey
      }
    });
    
    return response.json();
  }
  
  async createMemory(content, tags = null) {
    const body = { content };
    if (tags) body.metadata = { tags };
    
    const response = await fetch(\`\${this.baseUrl}/api/v1/memories\`, {
      method: 'POST',
      headers: {
        'X-Api-Key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    });
    
    return response.json();
  }
  
  async searchWithTags(query, tagsFilter) {
    const response = await fetch(\`\${this.baseUrl}/mcp/messages/\`, {
      method: 'POST',
      headers: {
        'X-Api-Key': this.apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/call',
        params: {
          name: 'search_memory_v2',
          arguments: {
            query,
            tags_filter: tagsFilter
          }
        },
        id: 1
      })
    });
    
    return response.json();
  }
}

// Usage
const api = new JeanMemoryAPI('jean_sk_...');

// Create memory
await api.createMemory(
  'User prefers dark mode',
  ['preferences', 'ui']
);

// Search memories
const results = await api.listMemories('preferences');

// Advanced search
const filtered = await api.searchWithTags(
  'ui settings',
  ['preferences', 'ui']
);
\`\`\`

## ERROR HANDLING

### Error Response Format
\`\`\`json
{
  "error": "Error type",
  "message": "Detailed error message",
  "code": "ERROR_CODE"
}
\`\`\`

### Common Error Codes
- 400: Bad Request - Invalid parameters
- 401: Unauthorized - Invalid API key
- 403: Forbidden - Insufficient permissions
- 404: Not Found - Resource doesn't exist
- 429: Rate Limited - Too many requests
- 500: Server Error - Internal error

### Rate Limiting
- Free tier: 100 requests/minute
- Pro tier: 1,000 requests/minute
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

## PAGINATION

\`\`\`javascript
// Paginate through all memories
async function getAllMemories(api) {
  const allMemories = [];
  let offset = 0;
  const limit = 50;
  let hasMore = true;
  
  while (hasMore) {
    const response = await api.listMemories(null, null, limit, offset);
    allMemories.push(...response.memories);
    
    hasMore = response.has_more;
    offset += limit;
  }
  
  return allMemories;
}
\`\`\`

## METADATA AND TAGS

### Tag Naming Conventions
\`\`\`javascript
// Good tag examples
tags: ["work", "project-alpha", "meeting-notes", "q1-2024"]

// Namespace tags for organization
tags: ["source:slack", "project:alpha", "priority:high", "status:active"]
\`\`\`

### Filtering Logic
- AND condition: All specified tags must be present
- Use namespaces for complex filtering
- Limit to 5 tags per memory for performance

## WEBHOOK INTEGRATION

\`\`\`javascript
// Express webhook receiver
app.post('/webhook/jean-memory', (req, res) => {
  const { event, data } = req.body;
  
  switch(event) {
    case 'memory.created':
      console.log('New memory:', data);
      break;
    case 'memory.updated':
      console.log('Updated memory:', data);
      break;
    case 'memory.deleted':
      console.log('Deleted memory:', data);
      break;
  }
  
  res.status(200).json({ received: true });
});
\`\`\`

## TESTING CHECKLIST

1. ✅ Test authentication with API key
2. ✅ Create a test memory
3. ✅ Search for the memory
4. ✅ Update the memory
5. ✅ Delete the memory
6. ✅ Test pagination with many memories
7. ✅ Test tag filtering
8. ✅ Test rate limiting behavior
9. ✅ Test error handling
10. ✅ Verify multi-user isolation

END OF REST API IMPLEMENTATION GUIDE`;

export const generateExamplesAIContent = () => `# Jean Memory - Complete Production Examples

## INSTANT IMPLEMENTATION EXAMPLES
Copy any of these complete, production-ready implementations directly into your project.

## 1. PERSONALIZED EDUCATION PLATFORM

### Math Tutor with Progress Tracking (React)
\`\`\`tsx
import React, { useState, useEffect } from 'react';
import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function MathTutorApp() {
  const [currentTopic, setCurrentTopic] = useState('');
  const [difficulty, setDifficulty] = useState('beginner');
  
  const { agent, signIn, user, sendMessage } = useJeanAgent({
    apiKey: process.env.REACT_APP_JEAN_API_KEY,
    systemPrompt: \`You are an expert math tutor who:
    - Remembers each student's strengths and weaknesses
    - Tracks which concepts they've mastered
    - Adjusts difficulty based on their progress
    - Provides step-by-step explanations
    - Offers practice problems at the right level
    - Celebrates improvements and milestones\`
  });

  const topics = ['Algebra', 'Geometry', 'Calculus', 'Statistics'];
  
  const startLesson = async (topic) => {
    setCurrentTopic(topic);
    const response = await sendMessage(
      \`Let's practice \${topic}. What concepts have I struggled with before?\`
    );
    return response;
  };
  
  const checkProgress = async () => {
    return await sendMessage(
      "Show me my learning progress and what I should focus on next"
    );
  };

  if (!agent) {
    return (
      <div className="education-app">
        <h1>Personal Math Tutor</h1>
        <p>Track your progress across all math topics</p>
        <SignInWithJean onSuccess={signIn} />
      </div>
    );
  }

  return (
    <div className="math-tutor">
      <header>
        <h1>Math Tutor for {user?.email}</h1>
        <button onClick={checkProgress}>View My Progress</button>
      </header>
      
      <div className="topic-selector">
        {topics.map(topic => (
          <button key={topic} onClick={() => startLesson(topic)}>
            Study {topic}
          </button>
        ))}
      </div>
      
      <JeanChat 
        agent={agent}
        placeholder="Ask me anything about math..."
      />
    </div>
  );
}

export default MathTutorApp;
\`\`\`

### Language Learning Assistant (Python)
\`\`\`python
from jeanmemory import JeanAgent
import speech_recognition as sr
import pyttsx3
from datetime import datetime

class LanguageLearningAssistant:
    def __init__(self, target_language="Spanish"):
        self.target_language = target_language
        self.agent = JeanAgent(
            api_key="jean_sk_...",
            system_prompt=f"""You are a {target_language} language tutor who:
            - Tracks vocabulary the student has learned
            - Remembers their native language
            - Adjusts lessons based on proficiency level
            - Provides contextual examples from past conversations
            - Corrects mistakes gently with explanations
            - Tracks pronunciation improvements
            - Suggests daily practice based on weak areas"""
        )
        self.speech = pyttsx3.init()
        self.recognizer = sr.Recognizer()
    
    def daily_lesson(self):
        """Generate personalized daily lesson"""
        lesson = self.agent.send_message(
            f"Create today's {self.target_language} lesson based on "
            "what I need to practice most. Include:
            1. Review of recent vocabulary
            2. New words related to my interests
            3. Grammar point I struggle with
            4. Conversation practice scenario"
        )
        return lesson
    
    def practice_conversation(self, topic):
        """Interactive conversation practice"""
        prompt = f"""Let's have a conversation about {topic} in {self.target_language}.
        - Use vocabulary I've learned
        - Introduce 2-3 new words naturally
        - Correct my mistakes after I respond
        - Track this conversation for future reference"""
        
        return self.agent.send_message(prompt)
    
    def vocabulary_quiz(self):
        """Personalized vocabulary quiz"""
        quiz = self.agent.send_message(
            "Quiz me on 10 words I've learned recently. "
            "Focus on ones I've struggled with."
        )
        return quiz
    
    def progress_report(self):
        """Weekly progress analysis"""
        return self.agent.send_message(
            "Analyze my language learning progress this week. Include:
            - Vocabulary growth
            - Grammar improvements  
            - Areas needing work
            - Recommended focus for next week"
        )

# Usage
assistant = LanguageLearningAssistant("French")
assistant.agent.authenticate()

# Daily routine
print(assistant.daily_lesson())
print(assistant.practice_conversation("ordering at a restaurant"))
print(assistant.vocabulary_quiz())
print(assistant.progress_report())
\`\`\`

## 2. BUSINESS & PRODUCTIVITY

### Intelligent CRM System (Node.js + Express)
\`\`\`javascript
import express from 'express';
import { JeanAgent } from '@jeanmemory/node';
import { WebClient } from '@slack/web-api';

class IntelligentCRM {
  constructor() {
    this.app = express();
    this.app.use(express.json());
    
    this.agent = new JeanAgent({
      apiKey: process.env.JEAN_API_KEY,
      systemPrompt: \`You are a CRM assistant who:
      - Tracks all customer interactions and history
      - Remembers customer preferences and pain points
      - Identifies upsell opportunities
      - Suggests next best actions for each lead
      - Analyzes patterns across successful deals
      - Provides personalized email templates\`
    });
    
    this.slack = new WebClient(process.env.SLACK_TOKEN);
    this.setupEndpoints();
  }
  
  setupEndpoints() {
    // Log customer interaction
    this.app.post('/api/interactions', async (req, res) => {
      const { customerId, type, notes, outcome } = req.body;
      
      // Store in Jean Memory with context
      await this.agent.addMemory(
        \`Customer \${customerId}: \${type} on \${new Date()}.
        Notes: \${notes}. Outcome: \${outcome}\`,
        { userId: customerId, tags: ['interaction', type, outcome] }
      );
      
      // Get AI suggestions for follow-up
      const suggestions = await this.agent.sendMessage(
        \`Based on this \${type} with outcome "\${outcome}", 
        what should our next steps be with this customer?\`,
        { userId: customerId }
      );
      
      res.json({ 
        logged: true, 
        suggestions,
        customerId 
      });
    });
    
    // Get customer insights
    this.app.get('/api/customers/:id/insights', async (req, res) => {
      const insights = await this.agent.sendMessage(
        \`Provide comprehensive insights for this customer:
        - Interaction history summary
        - Current status and sentiment
        - Pain points and objectives
        - Recommended approach
        - Upsell opportunities
        - Risk factors\`,
        { userId: req.params.id }
      );
      
      res.json({ insights });
    });
    
    // Generate personalized email
    this.app.post('/api/emails/generate', async (req, res) => {
      const { customerId, purpose } = req.body;
      
      const email = await this.agent.sendMessage(
        \`Write a personalized email for \${purpose}.
        Use their name, reference past conversations,
        and match their communication style.\`,
        { userId: customerId }
      );
      
      res.json({ email });
    });
    
    // Find similar successful deals
    this.app.post('/api/deals/similar', async (req, res) => {
      const { criteria } = req.body;
      
      const similar = await this.agent.searchMemory(
        \`successful deals with \${criteria}\`,
        { tags_filter: ['deal-won'] }
      );
      
      res.json({ similar });
    });
    
    // Weekly team insights
    this.app.get('/api/insights/weekly', async (req, res) => {
      const insights = await this.agent.sendMessage(
        \`Generate weekly sales insights:
        - Top opportunities
        - At-risk deals
        - Team performance patterns
        - Recommended focus areas\`
      );
      
      // Post to Slack
      await this.slack.chat.postMessage({
        channel: '#sales',
        text: \`Weekly AI Insights:\\n\${insights}\`
      });
      
      res.json({ insights, posted_to_slack: true });
    });
  }
  
  start() {
    this.app.listen(3000, () => {
      console.log('Intelligent CRM running on port 3000');
    });
  }
}

// Deploy
const crm = new IntelligentCRM();
crm.start();
\`\`\`

### AI Project Manager (React + TypeScript)
\`\`\`typescript
import React, { useState, useEffect } from 'react';
import { useJeanAgent } from '@jeanmemory/react';

interface Project {
  id: string;
  name: string;
  status: 'planning' | 'active' | 'completed';
  team: string[];
}

function AIProjectManager() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  
  const { agent, signIn, sendMessage } = useJeanAgent({
    apiKey: process.env.REACT_APP_JEAN_API_KEY,
    systemPrompt: \`You are an AI project manager who:
    - Tracks all project tasks, deadlines, and dependencies
    - Remembers team member strengths and workload
    - Identifies risks and blockers early
    - Suggests resource optimization
    - Provides daily standup summaries
    - Generates status reports
    - Recommends process improvements based on patterns\`
  });
  
  const createDailyStandup = async () => {
    const standup = await sendMessage(\`
      Generate today's standup summary:
      - What was completed yesterday
      - Today's priorities
      - Current blockers
      - Team member updates
      - Risk assessment
    \`);
    return standup;
  };
  
  const analyzeProjectHealth = async (projectId: string) => {
    const analysis = await sendMessage(
      \`Analyze project \${projectId} health:
      - Current progress vs timeline
      - Resource utilization
      - Risk factors
      - Team morale indicators
      - Recommended interventions\`,
      { userId: projectId }
    );
    return analysis;
  };
  
  const generateStatusReport = async () => {
    const report = await sendMessage(\`
      Generate executive status report:
      - Projects overview
      - Key achievements
      - Critical issues
      - Resource needs
      - Next week priorities
    \`);
    return report;
  };
  
  const suggestTaskAssignment = async (task: string) => {
    const suggestion = await sendMessage(\`
      Who should handle this task: "\${task}"?
      Consider:
      - Team member expertise
      - Current workload
      - Past similar tasks
      - Availability
    \`);
    return suggestion;
  };
  
  if (!agent) {
    return <SignInWithJean onSuccess={signIn} />;
  }
  
  return (
    <div className="project-manager">
      <header>
        <h1>AI Project Manager</h1>
        <div className="actions">
          <button onClick={createDailyStandup}>Daily Standup</button>
          <button onClick={generateStatusReport}>Status Report</button>
        </div>
      </header>
      
      <div className="projects-grid">
        {projects.map(project => (
          <div key={project.id} className="project-card">
            <h3>{project.name}</h3>
            <p>Status: {project.status}</p>
            <p>Team: {project.team.join(', ')}</p>
            <button onClick={() => analyzeProjectHealth(project.id)}>
              Analyze Health
            </button>
          </div>
        ))}
      </div>
      
      <div className="task-assistant">
        <h2>Task Assignment AI</h2>
        <input 
          type="text" 
          placeholder="Describe the task..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              suggestTaskAssignment(e.currentTarget.value);
            }
          }}
        />
      </div>
    </div>
  );
}
\`\`\`

## 3. HEALTHCARE & WELLNESS

### Mental Health Companion (React Native)
\`\`\`typescript
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, ScrollView } from 'react-native';
import { useJeanAgent } from '@jeanmemory/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function MentalHealthCompanion() {
  const [mood, setMood] = useState<number>(5);
  const [journalEntry, setJournalEntry] = useState('');
  
  const { agent, signIn, user, sendMessage } = useJeanAgent({
    apiKey: process.env.JEAN_API_KEY,
    systemPrompt: \`You are a supportive mental health companion who:
    - Tracks mood patterns and triggers
    - Remembers coping strategies that work
    - Provides personalized support during difficult times
    - Celebrates progress and positive moments
    - Suggests evidence-based techniques
    - Identifies when professional help may be needed
    Note: You are not a replacement for professional therapy.\`
  });
  
  const logMood = async (moodScore: number, notes: string) => {
    await sendMessage(\`
      Mood check-in: \${moodScore}/10
      Notes: \${notes}
      
      Please acknowledge this and provide:
      1. Validation of my feelings
      2. Relevant coping strategies based on my history
      3. Encouragement based on my progress
    \`);
  };
  
  const getMoodAnalysis = async () => {
    return await sendMessage(\`
      Analyze my mood patterns over the past week:
      - Trends and patterns
      - Common triggers
      - Effective coping strategies used
      - Areas of improvement
      - Suggestions for next week
    \`);
  };
  
  const crisisSupport = async () => {
    return await sendMessage(\`
      I'm having a difficult moment. Please:
      1. Provide immediate grounding techniques
      2. Remind me of strategies that have helped before
      3. Offer encouragement based on past resilience
      4. Suggest whether I should reach out for additional support
    \`);
  };
  
  const celebrateWin = async (achievement: string) => {
    return await sendMessage(\`
      I want to celebrate: \${achievement}
      
      Please help me:
      1. Acknowledge this progress
      2. Connect it to my journey
      3. Suggest how to build on this success
    \`);
  };
  
  if (!agent) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Your Mental Health Companion</Text>
        <Text>Private, supportive, always here for you</Text>
        <Button title="Get Started" onPress={signIn} />
      </View>
    );
  }
  
  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Hi {user?.name} 💚</Text>
      
      <View style={styles.moodTracker}>
        <Text>How are you feeling? (1-10)</Text>
        <Slider
          value={mood}
          onValueChange={setMood}
          minimumValue={1}
          maximumValue={10}
        />
        <TextInput
          placeholder="Any notes about your mood?"
          value={journalEntry}
          onChangeText={setJournalEntry}
          multiline
        />
        <Button 
          title="Log Mood" 
          onPress={() => logMood(mood, journalEntry)}
        />
      </View>
      
      <View style={styles.actions}>
        <Button title="Week Analysis" onPress={getMoodAnalysis} />
        <Button title="I Need Support" onPress={crisisSupport} color="red" />
        <Button title="Celebrate a Win" onPress={() => {
          // Show celebration input
        }} color="green" />
      </View>
      
      <View style={styles.chat}>
        <JeanChat agent={agent} />
      </View>
    </ScrollView>
  );
}
\`\`\`

## 4. DEVELOPER TOOLS

### AI Code Reviewer (Python)
\`\`\`python
from jeanmemory import JeanAgent
import subprocess
import ast
import os
from github import Github
from typing import List, Dict

class AICodeReviewer:
    def __init__(self, github_token: str):
        self.agent = JeanAgent(
            api_key=os.getenv("JEAN_API_KEY"),
            system_prompt="""You are an expert code reviewer who:
            - Remembers team coding standards and patterns
            - Tracks common mistakes by each developer
            - Identifies security vulnerabilities
            - Suggests performance optimizations
            - Maintains consistency across the codebase
            - Provides constructive feedback with examples
            - Learns from past review decisions"""
        )
        self.github = Github(github_token)
        
    def review_pull_request(self, repo_name: str, pr_number: int):
        """Complete AI review of a pull request"""
        repo = self.github.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        
        # Get changed files
        files = pr.get_files()
        
        review_comments = []
        for file in files:
            if file.filename.endswith('.py'):
                # Analyze Python files
                analysis = self.analyze_python_file(
                    file.filename, 
                    file.patch,
                    pr.user.login
                )
                review_comments.append(analysis)
        
        # Generate overall review
        overall_review = self.agent.send_message(f"""
        Review PR #{pr_number} by {pr.user.login}:
        Title: {pr.title}
        Description: {pr.body}
        Files changed: {[f.filename for f in files]}
        
        Provide:
        1. Overall assessment
        2. Security concerns
        3. Performance considerations
        4. Consistency with our patterns
        5. Suggestions for improvement
        
        Consider this developer's past patterns and mistakes.
        """)
        
        # Post review
        pr.create_review(
            body=overall_review,
            event='COMMENT'
        )
        
        # Store review for learning
        self.agent.add_memory(
            f"PR #{pr_number} review: {overall_review}",
            tags=['code-review', f'dev-{pr.user.login}', repo_name]
        )
        
        return overall_review
    
    def analyze_python_file(self, filename: str, patch: str, developer: str):
        """Deep analysis of Python code"""
        return self.agent.send_message(f"""
        Review this Python code change in {filename} by {developer}:
        
        {patch}
        
        Check for:
        1. PEP 8 compliance
        2. Type hints usage
        3. Error handling
        4. Test coverage implications
        5. Documentation completeness
        6. Common mistakes this developer makes
        7. Security issues (SQL injection, XSS, etc.)
        8. Performance bottlenecks
        """)
    
    def get_developer_patterns(self, developer: str):
        """Get historical patterns for a developer"""
        return self.agent.search_memory(
            f"code patterns and issues for {developer}",
            tags_filter=[f'dev-{developer}']
        )
    
    def generate_coding_guidelines(self):
        """Generate team coding guidelines from reviews"""
        return self.agent.send_message("""
        Based on all code reviews, generate comprehensive coding guidelines:
        1. Common patterns to follow
        2. Anti-patterns to avoid
        3. Security best practices
        4. Performance guidelines
        5. Documentation standards
        6. Testing requirements
        """)

# Usage
reviewer = AICodeReviewer(os.getenv("GITHUB_TOKEN"))
reviewer.agent.authenticate()

# Review a PR
review = reviewer.review_pull_request("myorg/myrepo", 123)
print(review)

# Get developer insights
patterns = reviewer.get_developer_patterns("john_doe")
print(patterns)

# Generate guidelines
guidelines = reviewer.generate_coding_guidelines()
with open("CODING_GUIDELINES.md", "w") as f:
    f.write(guidelines)
\`\`\`

## DEPLOYMENT CHECKLIST

1. ✅ Choose implementation example
2. ✅ Copy complete code
3. ✅ Install dependencies
4. ✅ Add API key to environment
5. ✅ Customize system prompt
6. ✅ Test locally
7. ✅ Add error handling
8. ✅ Deploy to production
9. ✅ Monitor usage
10. ✅ Iterate based on user feedback

END OF PRODUCTION EXAMPLES`;