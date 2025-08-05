# Jean Memory Backend API Documentation

## Overview

The Jean Memory backend is a FastAPI-based Python application that provides RESTful APIs and MCP (Model Context Protocol) endpoints for memory management. It orchestrates multiple databases and AI services to deliver intelligent memory storage and retrieval.

## Project Structure

```
openmemory/api/
├── app/
│   ├── __init__.py
│   ├── auth.py                 # Authentication logic
│   ├── database.py              # Database connections
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── settings.py              # Configuration
│   ├── mcp_server.py            # MCP server setup
│   ├── mcp_orchestration.py     # Smart context orchestration
│   ├── routers/                 # API endpoints
│   │   ├── memories.py          # Memory CRUD operations
│   │   ├── apps.py              # App management
│   │   ├── integrations.py      # External integrations
│   │   ├── webhooks.py          # Webhook handlers
│   │   └── agent_mcp.py         # MCP agent endpoints
│   ├── tools/                   # MCP tools
│   │   ├── memory.py            # Memory operations
│   │   ├── documents.py         # Document processing
│   │   └── orchestration.py     # Context orchestration
│   ├── services/                # Business logic
│   │   ├── background_processor.py
│   │   ├── chunking_service.py
│   │   └── background_sync.py
│   ├── utils/                   # Utility functions
│   │   ├── neo4j_connection.py  # Neo4j client
│   │   ├── pgvector_connection.py # pgvector client
│   │   ├── gemini.py            # Gemini AI service
│   │   └── categorization.py    # AI categorization
│   └── clients/                 # MCP client profiles
│       ├── base.py              # Base client class
│       ├── chatgpt.py           # ChatGPT profile
│       ├── claude.py            # Claude profile
│       └── default.py           # Default profile
├── jean_memory/                 # Core memory library
│   ├── core.py                  # Main interface
│   ├── search.py                # Search engine
│   ├── ingestion.py             # Memory ingestion
│   ├── orchestrator.py          # AI orchestration
│   └── config.py                # Configuration
├── main.py                      # FastAPI app entry
├── alembic/                     # Database migrations
└── requirements.txt             # Dependencies
```

## Core Components

### 1. FastAPI Application (`main.py`)

```python
# Key features:
- CORS middleware for cross-origin requests
- Health check endpoints
- Background task management
- Database initialization
- MCP server integration
```

### 2. Authentication System (`app/auth.py`)

**Dual Authentication Support:**
1. **Supabase JWT Authentication**
   - Primary authentication method
   - Validates JWT tokens from Supabase
   - Supports social login providers

2. **API Key Authentication**
   - Alternative for programmatic access
   - Keys prefixed with `jean_sk_`
   - SHA-256 hashed storage

### 3. Database Models (`app/models.py`)

**Key Models:**
- **User**: User accounts with subscription tiers
- **App**: Connected applications (ChatGPT, Claude, etc.)
- **Memory**: Core memory entries with states
- **Category**: Auto-assigned memory categories
- **Document**: Stored documents (Substack, etc.)
- **DocumentChunk**: Chunked document content
- **UserNarrative**: AI-generated user summaries
- **SMSConversation**: SMS interaction history

**Memory States:**
- `active`: Normal, searchable memory
- `paused`: Temporarily hidden
- `archived`: Long-term storage
- `deleted`: Soft deleted

### 4. API Routers

#### Memory Router (`/api/v1/memories`)
- `GET /`: List all memories with filtering
- `GET /paginated`: Paginated memory listing
- `POST /`: Create new memory
- `GET /{id}`: Get specific memory
- `PUT /{id}`: Update memory
- `DELETE /{id}`: Delete memory
- `POST /batch-delete`: Delete multiple memories
- `POST /pause`: Pause memories
- `POST /filter`: Advanced filtering

#### Apps Router (`/api/v1/apps`)
- `GET /`: List user's connected apps
- `POST /{app_id}/sync`: Trigger app sync
- `GET /task/{task_id}`: Check sync status

#### Integration Router
- `POST /integrations/substack/sync`: Sync Substack
- `POST /integrations/twitter/sync`: Sync Twitter/X

### 5. MCP Server Implementation

**MCP Tools Available:**
1. **add_memories**: Add new memories
2. **search_memory**: Search memories by query
3. **list_memories**: List all memories
4. **ask_memory**: AI-powered Q&A
5. **deep_memory_query**: Deep document search
6. **add_observation**: Add factual observations

**Client-Specific Profiles:**
- ChatGPT: Optimized for GPT context
- Claude: Supports latest MCP protocol
- VS Code: Developer-focused features
- Default: Generic MCP client

### 6. Smart Context Orchestration

**AI-Powered Context Engineering:**
```python
class SmartContextOrchestrator:
    # Uses Gemini 2.5 Flash for intelligent planning
    # Determines optimal memory retrieval strategy
    # Handles background memory saving
    # Provides deep analysis for new conversations
```

**Context Strategies:**
1. **Fast Deep Analysis**: 10-15s for conversation start
2. **Full Deep Analysis**: 30-60s for rich content
3. **Standard Orchestration**: Quick memory retrieval
4. **Fallback Plan**: When AI planning fails

### 7. Background Processing

**Background Tasks:**
- Document chunk processing
- Embedding generation
- Memory categorization
- Narrative generation
- Integration syncing

### 8. Jean Memory Library

**Core Classes:**

```python
class JeanMemoryV2:
    """Main interface for memory operations"""
    - search(query, user_id) -> SearchResult
    - ingest_memories(memories, user_id) -> IngestionResult
    - get_config() -> JeanMemoryConfig
```

**Search Engine:**
- Hybrid search across multiple sources
- Vector similarity (Qdrant)
- Graph relationships (Neo4j)
- AI synthesis (Gemini)

**Ingestion Engine:**
- Deduplication
- Embedding generation
- Graph entity extraction
- Batch processing

## API Endpoints

### Authentication Headers
```
Authorization: Bearer <supabase_jwt_token>
# OR
Authorization: Bearer jean_sk_<api_key>
```

### Memory Operations

#### Create Memory
```http
POST /api/v1/memories
Content-Type: application/json

{
  "content": "I love hiking in the mountains",
  "app_id": "<app_uuid>"
}
```

#### Search Memories
```http
GET /api/v1/memories?search_query=hiking&categories=outdoor,travel
```

#### Update Memory
```http
PUT /api/v1/memories/{memory_id}
Content-Type: application/json

{
  "content": "Updated memory content"
}
```

### MCP Endpoints

#### Initialize MCP
```http
POST /mcp/messages/
X-User-Id: <user_id>
X-Client-Name: <client_name>

{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {"protocolVersion": "2024-11-05"},
  "id": 1
}
```

#### Call MCP Tool
```http
POST /mcp/messages/
X-User-Id: <user_id>
X-Client-Name: <client_name>

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_memory",
    "arguments": {"query": "my hobbies"}
  },
  "id": 2
}
```

## Configuration

### Environment Variables

**Core Settings:**
- `DATABASE_URL`: PostgreSQL connection
- `ENVIRONMENT`: production/development
- `LOG_LEVEL`: INFO/DEBUG/ERROR

**AI Services:**
- `OPENAI_API_KEY`: OpenAI access
- `OPENAI_MODEL`: Model selection (gpt-4o-mini)
- `GEMINI_API_KEY`: Google Gemini access
- `ANTHROPIC_API_KEY`: Claude access

**Vector/Graph Databases:**
- `QDRANT_HOST`, `QDRANT_API_KEY`: Vector search
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`: Graph DB

**External Services:**
- `STRIPE_SECRET_KEY`: Payments
- `TWILIO_*`: SMS integration
- `RESEND_API_KEY`: Email delivery
- `POSTHOG_API_KEY`: Analytics

## Database Schema

### Memory Storage Strategy
1. **PostgreSQL**: Metadata, user data, app configs
2. **Qdrant**: Vector embeddings for semantic search
3. **Neo4j**: Entity relationships and knowledge graphs

### Key Relationships
- User -> Apps (1:N)
- User -> Memories (1:N)
- App -> Memories (1:N)
- Memory -> Categories (M:N)
- Memory -> Documents (M:N)
- Document -> DocumentChunks (1:N)

## Security Considerations

1. **Authentication**: All endpoints require auth except health checks
2. **Data Isolation**: User data strictly isolated
3. **Input Validation**: Pydantic schemas for all inputs
4. **Rate Limiting**: Configurable per subscription tier
5. **Secret Management**: Environment variables, never in code
6. **CORS**: Strict origin allowlist

## Performance Optimization

1. **Database Indexes**: Strategic indexes on frequent queries
2. **Connection Pooling**: Efficient database connections
3. **Async Operations**: Non-blocking I/O throughout
4. **Background Tasks**: Heavy processing offloaded
5. **Caching**: Redis-like caching for frequent data
6. **Batch Operations**: Bulk memory operations supported

## Monitoring & Debugging

1. **Health Checks**: `/health` and `/health/detailed`
2. **Structured Logging**: JSON logs with context
3. **Error Tracking**: Comprehensive error handling
4. **Performance Metrics**: Via PostHog analytics
5. **Database Status**: Connection monitoring for all DBs