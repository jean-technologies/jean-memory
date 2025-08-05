# Jean Memory MCP Integration Guide

## Overview

The Model Context Protocol (MCP) is a standardized protocol that enables AI assistants to interact with external tools and data sources. Jean Memory implements MCP to allow AI assistants like Claude, ChatGPT, and others to access and manage user memories.

## MCP Architecture

```
┌────────────────────────┐     ┌────────────────────────┐
│   AI Assistant Client  │     │  Jean Memory MCP Server│
│  (Claude, ChatGPT, etc)│<----│   /mcp/messages/       │
└────────────────────────┘     └────────┬───────────────┘
         JSON-RPC 2.0                    │
                                         │
                              ┌─────────▼───────────┐
                              │   MCP Orchestrator   │
                              │  (Smart Context AI)  │
                              └─────────┬───────────┘
                                         │
                    ┌────────────────┴─────────────────┐
                    │                                  │
            ┌───────▼───────┐              ┌────────▼───────┐
            │  Memory Tools │              │ Context Tools  │
            └───────────────┘              └────────────────┘
```

## MCP Implementation Details

### 1. Protocol Support

**Supported Versions:**
- `2024-11-05`: Standard MCP protocol
- `2025-03-26`: Extended protocol with annotations

**Transport Methods:**
1. **SSE (Server-Sent Events)**: Legacy, compatible with all clients
2. **HTTP Transport**: 50% faster, direct backend routing

### 2. Endpoints

#### Standard MCP Endpoint
```
POST /mcp/messages/
Headers:
  X-User-Id: <user_id>
  X-Client-Name: <client_name>
```

#### V2 HTTP Transport Endpoint
```
POST /mcp/v2/{client_name}/{user_id}
```

#### Client-Specific SSE Endpoints
```
GET /mcp/chatgpt/sse/{user_id}
GET /mcp/claude/sse/{user_id}
GET /mcp/chorus/sse/{user_id}
```

### 3. Available Tools

#### Memory Management Tools

**add_memories**
```json
{
  "name": "add_memories",
  "description": "Add new memories to the user's memory",
  "inputSchema": {
    "type": "object",
    "properties": {
      "memories": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of memories to add"
      }
    },
    "required": ["memories"]
  }
}
```

**search_memory**
```json
{
  "name": "search_memory",
  "description": "Search the user's memory for memories that match the query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional tags to filter by"
      },
      "deep_search": {
        "type": "boolean",
        "description": "Enable deep document search"
      }
    },
    "required": ["query"]
  }
}
```

**ask_memory**
```json
{
  "name": "ask_memory",
  "description": "Ask a question about the user's memories and get an AI-generated response",
  "inputSchema": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string",
        "description": "Question to ask about memories"
      }
    },
    "required": ["question"]
  }
}
```

**list_memories**
```json
{
  "name": "list_memories",
  "description": "List all memories for the user",
  "inputSchema": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "number",
        "description": "Maximum number of memories to return"
      }
    }
  }
}
```

#### Advanced Tools

**deep_memory_query**
- Performs comprehensive search across memories and documents
- Uses AI synthesis for intelligent responses
- Includes graph relationships and context

**add_observation**
- Adds factual observations to memory
- Optimized for objective information

### 4. Smart Context Orchestration

**AI-Powered Context Engineering:**

The MCP server uses Gemini 2.5 Flash to intelligently determine:
1. What memories to retrieve
2. How much context to provide
3. Whether to use deep analysis
4. Background memory saving strategy

**Context Strategies:**

```python
class SmartContextOrchestrator:
    async def orchestrate(self, message, user_id, client_name, is_new_conversation):
        # Determine strategy based on:
        # - Message content and intent
        # - Client capabilities
        # - Conversation state
        # - User preferences
        
        if self._should_use_deep_analysis(message, is_new_conversation):
            return await self._deep_memory_orchestration(...)
        else:
            return await self._standard_orchestration(...)
```

### 5. Client Profiles

**ChatGPT Profile**
```python
class ChatGPTProfile(BaseClientProfile):
    # Optimized for GPT context window
    # Structured memory format
    # Background memory saving
    # Session-based user mapping
```

**Claude Profile**
```python
class ClaudeProfile(BaseClientProfile):
    # Latest MCP protocol support
    # Annotation support
    # Rich memory context
    # Efficient tool responses
```

**Default Profile**
```python
class DefaultProfile(BaseClientProfile):
    # Generic MCP implementation
    # Standard tool set
    # Basic context formatting
```

## Integration Examples

### 1. Claude Desktop Integration

**Install Extension:**
```bash
# Download extension
curl -O https://jean-memory-api-virginia.onrender.com/download/claude-extension-http

# Install in Claude Desktop
# Settings > Extensions > Install from file
```

**Configuration (claude_desktop_config.json):**
```json
{
  "mcpServers": {
    "jean-memory": {
      "command": "node",
      "args": ["/path/to/extension/build/index.js"],
      "env": {
        "JEAN_MEMORY_USER_ID": "your-user-id"
      }
    }
  }
}
```

### 2. ChatGPT Integration

**Custom GPT Configuration:**
```yaml
Name: Jean Memory Assistant
Description: Access and manage your personal memories
Instructions: |
  You are connected to the user's Jean Memory system.
  Use the available tools to help them remember and organize information.
  
Actions:
  - Server: https://jean-memory-api-virginia.onrender.com/openapi.json
  - Authentication: API Key (user provides jean_sk_xxx key)
```

### 3. VS Code / Cursor Integration

**MCP Server Config:**
```json
{
  "name": "jean-memory",
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-memory",
    "--url", "https://jean-memory-api-virginia.onrender.com/mcp/v2/vscode/{USER_ID}"
  ]
}
```

### 4. Generic MCP Client

**Using mcp-client CLI:**
```bash
# Install MCP client
npm install -g @modelcontextprotocol/cli

# Connect to Jean Memory
mcp connect https://jean-memory-api-virginia.onrender.com/mcp/messages/ \
  --header "X-User-Id: your-user-id" \
  --header "X-Client-Name: my-client"
```

## Authentication

### User Authentication Methods

1. **Header-based (Recommended)**
   ```
   X-User-Id: <supabase_user_id>
   X-Client-Name: <client_identifier>
   ```

2. **URL-based (V2 endpoints)**
   ```
   /mcp/v2/{client_name}/{user_id}
   ```

3. **API Key (For API endpoints)**
   ```
   Authorization: Bearer jean_sk_<api_key>
   ```

## Best Practices

### 1. Memory Management
- Add memories in batches when possible
- Use descriptive memory content
- Include temporal context
- Avoid duplicate memories

### 2. Search Optimization
- Use specific search queries
- Enable deep_search for detailed results
- Leverage tags for categorization
- Use ask_memory for complex questions

### 3. Performance
- Use HTTP transport when available
- Implement client-side caching
- Batch operations
- Handle rate limits gracefully

### 4. Error Handling
```javascript
try {
  const result = await mcp.callTool('search_memory', {
    query: 'my hobbies'
  })
} catch (error) {
  if (error.code === -32603) {
    // Internal error - retry
  } else if (error.code === -32602) {
    // Invalid params - fix and retry
  }
}
```

## Debugging

### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
export MCP_DEBUG=true
```

### Common Issues

1. **Authentication Failures**
   - Verify user ID format
   - Check client name registration
   - Ensure headers are properly set

2. **Tool Errors**
   - Validate input parameters
   - Check tool availability for client
   - Review error messages in response

3. **Performance Issues**
   - Switch to HTTP transport
   - Reduce memory batch sizes
   - Enable response streaming

### Health Check
```bash
# Check MCP server health
curl https://jean-memory-api-virginia.onrender.com/health/detailed
```

## Advanced Features

### 1. Context Enrichment
The orchestrator automatically enriches responses with:
- Related memories
- Temporal context
- Entity relationships
- User narratives

### 2. Background Processing
- Memories saved asynchronously
- Automatic categorization
- Embedding generation
- Graph relationship extraction

### 3. Adaptive Responses
- Client-specific formatting
- Context window optimization
- Progressive detail loading
- Fallback strategies