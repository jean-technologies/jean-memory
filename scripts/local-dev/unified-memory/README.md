# Unified Memory System - Local Development

This directory contains the unified memory system integration for local development. It combines **Mem0** (vector search + entity graphs) with **Graphiti** (temporal graphs) to provide advanced memory capabilities.

## Overview

The unified memory system provides:

- **Vector Search**: Semantic similarity search via Mem0 + Qdrant
- **Entity Graphs**: Relationship modeling via Mem0 + Neo4j
- **Temporal Graphs**: Time-aware relationships via Graphiti + Neo4j
- **Unified API**: Single interface for advanced memory operations

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Your API      │    │  MCP Clients    │
│   (FastAPI)     │    │  (Claude, etc.) │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
         ┌───────────▼────────────┐
         │  Unified Memory API    │
         │  /api/v1/mcp/unified_* │
         └───────────┬────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐    ┌──────▼──────┐    ┌────▼────┐
│ Mem0   │    │  Graphiti   │    │ Neo4j   │
│Vector  │    │ Temporal    │    │ Graph   │
│Search  │    │ Graph       │    │ Store   │
└───┬────┘    └─────────────┘    └─────────┘
    │
┌───▼────┐
│ Qdrant │
│Vector  │
│Store   │
└────────┘
```

## Quick Start

### 1. Start Services

```bash
# Navigate to the unified memory directory
cd scripts/local-dev/unified-memory

# Start Neo4j and Qdrant services
./start-unified-memory.sh
```

The script will:
- Create a `.env.unified-memory` file if it doesn't exist
- Prompt you to add your OpenAI API key
- Start Docker services
- Wait for services to be ready

### 2. Install Dependencies

```bash
# Install additional Python dependencies
pip install -r scripts/local-dev/unified-memory/requirements-unified-memory.txt
```

### 3. Enable Unified Memory

Add to your main `.env` file:
```bash
USE_UNIFIED_MEMORY=true
```

### 4. Restart Your API

```bash
# Restart your FastAPI server to pick up the new configuration
cd openmemory/api
uvicorn main:app --reload
```

## Configuration

### Environment Variables

The system uses these environment variables (set in `.env.unified-memory`):

```bash
# Required
OPENAI_API_KEY=your_actual_api_key_here

# Neo4j (default values work for local development)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fasho93fasho

# Qdrant (default values work for local development)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Feature flags
USE_UNIFIED_MEMORY=true
IS_LOCAL_UNIFIED_MEMORY=true
```

### Service Ports

- **Neo4j Browser**: http://localhost:7474
- **Qdrant Web UI**: http://localhost:6334
- **Neo4j Bolt**: bolt://localhost:7687
- **Qdrant gRPC**: localhost:6333

## API Endpoints

### Standard Endpoints (Always Available)

- `POST /api/v1/mcp/search_memory` - Standard Mem0 search
- `POST /api/v1/mcp/add_memories` - Standard Mem0 add
- `POST /api/v1/mcp/list_memories` - List all memories

### Unified Endpoints (Local Development Only)

- `POST /api/v1/mcp/unified_search` - Advanced search (Mem0 + Graphiti)
- `POST /api/v1/mcp/unified_add_memory` - Enhanced memory creation

## Usage Examples

### Adding a Memory with Timestamp

```bash
curl -X POST http://localhost:8000/api/v1/mcp/unified_add_memory \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Alice started working on the quantum computing project",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

### Unified Search

```bash
curl -X POST http://localhost:8000/api/v1/mcp/unified_search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "query": "What was Alice working on in January?",
    "limit": 10
  }'
```

Response includes both vector and graph results:
```json
{
  "status": "success",
  "results": {
    "mem0_results": [...],
    "graphiti_results": [...],
    "unified": true,
    "query": "What was Alice working on in January?"
  },
  "unified": true
}
```

## Testing

### Manual Testing

1. **Start Services**: `./start-unified-memory.sh`
2. **Check Service Health**:
   - Neo4j: Visit http://localhost:7474 (login: neo4j/fasho93fasho)
   - Qdrant: Visit http://localhost:6334
3. **Test API**: Use the curl examples above
4. **Stop Services**: `./stop-unified-memory.sh`

### Integration with MCP Clients

The unified endpoints work with any MCP client (Claude, Cursor, etc.) that can make HTTP requests to your API.

## Troubleshooting

### Services Won't Start

```bash
# Check Docker status
docker ps

# View service logs
cd scripts/local-dev/unified-memory
docker-compose -f docker-compose.unified-memory.yml logs neo4j_unified
docker-compose -f docker-compose.unified-memory.yml logs qdrant_unified
```

### API Errors

```bash
# Check if unified memory is enabled
curl -X POST http://localhost:8000/api/v1/mcp/unified_search \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# Should return error if not enabled:
# {"error": "Unified memory system not available..."}
```

### Reset Data

```bash
# Stop services and remove all data
cd scripts/local-dev/unified-memory
docker-compose -f docker-compose.unified-memory.yml down -v

# Start fresh
./start-unified-memory.sh
```

## Development Notes

### Code Structure

- `app/utils/unified_memory.py` - Main unified memory implementation
- `app/utils/memory.py` - Enhanced to support unified memory
- `app/routers/mcp_tools.py` - New unified endpoints
- `scripts/local-dev/unified-memory/` - Local development infrastructure

### Production Considerations

- Unified memory is **disabled by default** in production
- Only activates when `USE_UNIFIED_MEMORY=true` AND `is_local_development=true`
- Production continues using standard Mem0 + Qdrant Cloud
- No impact on existing functionality

### Extending the System

To add new unified memory features:

1. Extend `UnifiedMemorySystem` class in `app/utils/unified_memory.py`
2. Add new endpoints in `app/routers/mcp_tools.py`
3. Update this README with usage examples

## Advanced Features

### Temporal Queries

Graphiti enables time-aware queries:
- "What was happening around the same time as X?"
- "Show me the timeline of events related to Y"
- "What changed between date A and date B?"

### Entity Relationships

The system automatically extracts and models:
- People and their relationships
- Projects and their participants  
- Events and their contexts
- Concepts and their connections

### Graph Exploration

Use Neo4j Browser (http://localhost:7474) to explore the knowledge graph:

```cypher
// View all nodes
MATCH (n) RETURN n LIMIT 25

// Find relationships between entities
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10

// Search for specific entities
MATCH (n) WHERE n.name CONTAINS "Alice" RETURN n
```

## Support

For issues with the unified memory system:

1. Check the logs: `docker-compose logs`
2. Verify configuration: Check `.env.unified-memory`
3. Test individual services: Neo4j Browser, Qdrant UI
4. Review API logs: Check FastAPI console output

The system is designed to fail gracefully - if unified memory is unavailable, it falls back to standard Mem0 functionality. 