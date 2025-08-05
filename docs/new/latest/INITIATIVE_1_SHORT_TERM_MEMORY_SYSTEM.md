# Initiative 1: Short-term/Long-term Memory System Architecture

## Overview

This initiative introduces a dual-layer memory architecture for Jean Memory, splitting memory storage into:
- **Short-term Memory**: Local, fast, lightweight storage for immediate access
- **Long-term Memory**: Cloud-based, persistent storage for comprehensive memory management

## Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Local Machine                      │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Short-term Memory Layer (Local)                │ │
│  │                                                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │ │
│  │  │    FAISS    │  │ Neo4j Local │  │ SQLite/DuckDB    │   │ │
│  │  │(Vector Store)│  │(Graph Store)│  │(Metadata Store)  │   │ │
│  │  └─────────────┘  └─────────────┘  └──────────────────┘   │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │       Jean Memory Library (Local Edition)          │    │ │
│  │  │  - Fast ingestion (<100ms)                         │    │ │
│  │  │  - Quick search (<50ms)                            │    │ │
│  │  │  - Lightweight footprint                           │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│                              │ Memory Shuttle Service             │
│                              │ (Bidirectional Sync)              │
│                              ▼                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              │ HTTPS/WebSocket
                              │
┌─────────────────────────────┼────────────────────────────────────┐
│                             ▼        Cloud Infrastructure         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Long-term Memory Layer (Cloud)                 │ │
│  │                                                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │ │
│  │  │Qdrant Cloud │  │ Neo4j Aura  │  │   PostgreSQL     │   │ │
│  │  │(Vector Store)│  │(Graph Store)│  │(via Supabase)    │   │ │
│  │  └─────────────┘  └─────────────┘  └──────────────────┘   │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │     Jean Memory Library (Production Edition)       │    │ │
│  │  │  - Scalable storage                                │    │ │
│  │  │  - Advanced analytics                              │    │ │
│  │  │  - Cross-device sync                               │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Short-term Memory Layer

#### 1.1 Local Jean Memory Library Clone

Create a lightweight version of the jean_memory library:

```python
# jean_memory_local/config.py
class LocalMemoryConfig:
    def __init__(self):
        self.vector_store = {
            "provider": "faiss",
            "config": {
                "index_path": "~/.jean_memory/faiss_index",
                "dimension": 1536
            }
        }
        self.graph_store = {
            "provider": "neo4j",
            "config": {
                "uri": "bolt://localhost:7687",
                "auth": ("neo4j", "password"),
                "database": "jean_memory_local"
            }
        }
        self.metadata_store = {
            "provider": "sqlite",
            "config": {
                "path": "~/.jean_memory/metadata.db"
            }
        }
```

#### 1.2 FAISS Integration

```python
# jean_memory_local/vector_store.py
import faiss
import numpy as np
import pickle
from pathlib import Path

class FAISSVectorStore:
    def __init__(self, config):
        self.index_path = Path(config["index_path"]).expanduser()
        self.dimension = config["dimension"]
        self.index = self._load_or_create_index()
        self.id_map = self._load_id_map()
        
    def _load_or_create_index(self):
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        else:
            # Create flat index for simplicity and speed
            index = faiss.IndexFlatL2(self.dimension)
            return index
            
    def add(self, embeddings, ids):
        """Add embeddings with IDs"""
        vectors = np.array(embeddings).astype('float32')
        self.index.add(vectors)
        
        # Update ID mapping
        for i, id in enumerate(ids):
            self.id_map[len(self.id_map)] = id
            
        self._save()
        
    def search(self, query_embedding, k=10):
        """Search for similar vectors"""
        query = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(query, k)
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx in self.id_map:
                results.append({
                    "id": self.id_map[idx],
                    "score": 1 / (1 + dist)  # Convert distance to similarity
                })
        return results
```

#### 1.3 Neo4j Local Setup

```python
# jean_memory_local/graph_store.py
from neo4j import GraphDatabase
import docker

class LocalNeo4jManager:
    def __init__(self):
        self.container_name = "jean-memory-neo4j-local"
        self.docker_client = docker.from_env()
        
    def ensure_running(self):
        """Ensure Neo4j is running locally"""
        try:
            container = self.docker_client.containers.get(self.container_name)
            if container.status != "running":
                container.start()
        except docker.errors.NotFound:
            # Start new container
            self.docker_client.containers.run(
                "neo4j:5-community",
                name=self.container_name,
                detach=True,
                ports={'7687/tcp': 7687, '7474/tcp': 7474},
                environment={
                    "NEO4J_AUTH": "neo4j/jeanmemory123",
                    "NEO4J_PLUGINS": '["apoc"]',
                    "NEO4J_dbms_memory_heap_max__size": "512M",
                    "NEO4J_dbms_memory_pagecache_size": "256M"
                },
                volumes={
                    "jean-memory-neo4j-data": {"bind": "/data", "mode": "rw"},
                    "jean-memory-neo4j-logs": {"bind": "/logs", "mode": "rw"}
                }
            )
```

### Phase 2: Memory Shuttle Service

#### 2.1 Shuttle Architecture

```python
# jean_memory_shuttle/shuttle.py
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MemoryShuttle:
    def __init__(self, local_memory, cloud_memory, config):
        self.local = local_memory
        self.cloud = cloud_memory
        self.config = config
        self.sync_queue = asyncio.Queue()
        self.last_sync = {}
        
    async def load_initial_context(self, user_id: str, k: int = 100):
        """
        Load top-k memories from long-term to short-term on session start
        """
        # Get user's most relevant memories from cloud
        cloud_memories = await self.cloud.get_recent_memories(user_id, limit=k)
        
        # Bulk insert into local storage
        for memory in cloud_memories:
            await self.local.add_memory(
                content=memory['content'],
                embedding=memory['embedding'],
                metadata={
                    **memory['metadata'],
                    'synced_from_cloud': True,
                    'cloud_id': memory['id']
                }
            )
            
        return len(cloud_memories)
        
    async def sync_to_cloud(self, batch_size: int = 50):
        """
        Background task to sync local memories to cloud
        """
        while True:
            try:
                # Get unsynced memories from local
                unsynced = await self.local.get_unsynced_memories(limit=batch_size)
                
                if unsynced:
                    # Batch upload to cloud
                    cloud_ids = await self.cloud.batch_add_memories(unsynced)
                    
                    # Mark as synced in local
                    for local_id, cloud_id in zip(
                        [m['id'] for m in unsynced], 
                        cloud_ids
                    ):
                        await self.local.mark_synced(local_id, cloud_id)
                        
                # Wait before next sync
                await asyncio.sleep(self.config.sync_interval_seconds)
                
            except Exception as e:
                logger.error(f"Sync error: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute
```

#### 2.2 Sync Configuration

```yaml
# config/shuttle.yaml
shuttle:
  # Initial load settings
  initial_load:
    memory_count: 100
    include_categories:
      - personal
      - work
      - preferences
    time_window_days: 30
    
  # Sync settings
  sync:
    interval_seconds: 300  # 5 minutes
    batch_size: 50
    retry_attempts: 3
    
  # Conflict resolution
  conflict_resolution:
    strategy: "cloud_wins"  # or "local_wins" or "newest_wins"
    
  # Performance
  performance:
    max_local_memories: 10000
    cleanup_threshold: 0.8  # Clean up when 80% full
```

### Phase 3: Integration with Existing System

#### 3.1 Modified MCP Tools

```python
# app/tools/memory_v2.py
from app.utils.memory_layers import get_memory_layer

@mcp.tool(description="Add memories with automatic layer selection")
async def add_memories_v2(memories: List[str], layer: str = "auto"):
    """
    Add memories to appropriate layer
    - 'short': Force short-term only
    - 'long': Force long-term only  
    - 'auto': Add to short-term with background sync
    """
    memory_layer = get_memory_layer(layer)
    
    if layer == "auto":
        # Add to short-term for immediate access
        local_results = await memory_layer.local.add_memories(memories)
        
        # Queue for background sync
        for memory in memories:
            await memory_layer.shuttle.sync_queue.put(memory)
            
        return {
            "status": "success",
            "layer": "short-term",
            "count": len(memories),
            "sync_status": "queued"
        }
```

#### 3.2 Frontend Integration

Refer to [JEAN_MEMORY_FRONTEND.md](./JEAN_MEMORY_FRONTEND.md) for UI components.

```typescript
// hooks/useMemoryLayers.ts
export const useMemoryLayers = () => {
  const [layer, setLayer] = useState<'short' | 'long' | 'auto'>('auto')
  const [syncStatus, setSyncStatus] = useState<SyncStatus>()
  
  const addMemory = async (content: string) => {
    const response = await apiClient.post('/api/v2/memories', {
      content,
      layer
    })
    
    if (layer === 'auto') {
      // Start monitoring sync status
      monitorSyncStatus(response.data.sync_id)
    }
    
    return response.data
  }
  
  return { addMemory, layer, setLayer, syncStatus }
}
```

## Performance Targets

### Short-term Memory Layer
- **Ingestion**: <100ms per memory
- **Search**: <50ms for top-10 results
- **Memory footprint**: <500MB for 10k memories
- **Startup time**: <5 seconds

### Long-term Memory Layer
- **Ingestion**: <2s per memory (with full processing)
- **Search**: <500ms for complex queries
- **Storage**: Unlimited
- **Availability**: 99.9%

### Memory Shuttle
- **Initial load**: <10s for 100 memories
- **Sync latency**: <5 minutes
- **Conflict resolution**: <100ms
- **Queue capacity**: 10,000 items

## Implementation Timeline

### Prerequisites: Local Development Setup
**Depends on**: [INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md)
- [ ] Complete local development environment setup
- [ ] Verify Neo4j local container functionality
- [ ] Confirm FAISS testing capabilities
- [ ] Test local memory ingestion pipeline

### Week 1-2: Short-term Memory Core
- [ ] Fork jean_memory library using local development template
- [ ] Implement FAISS vector store with local testing integration
- [ ] Set up local Neo4j with Docker (leveraging existing local setup)
- [ ] Create SQLite metadata store with test data seeding
- [ ] Unit tests for local operations using local test framework

### Week 3-4: Memory Shuttle
- [ ] Design sync protocol with local testing mocks
- [ ] Implement bidirectional sync using local development database
- [ ] Add conflict resolution with comprehensive local test scenarios
- [ ] Create monitoring dashboard integrated with local metrics
- [ ] Integration tests using local development test suite

### Week 5-6: System Integration
- [ ] Update MCP tools using local development MCP testing
- [ ] Modify API endpoints with local API testing infrastructure
- [ ] Update frontend components using local UI development server
- [ ] End-to-end testing using local development full-stack setup
- [ ] Performance optimization validated against local development targets

## Security Considerations

1. **Local Storage Security**
   - Encrypt FAISS index at rest
   - Secure Neo4j with strong passwords
   - Use OS keychain for credentials

2. **Sync Security**
   - TLS for all cloud communication
   - Authentication tokens with short TTL
   - Rate limiting on sync operations

3. **Data Privacy**
   - Option to exclude sensitive memories from sync
   - Local-only mode for privacy-conscious users
   - Clear data retention policies

## Monitoring and Debugging

```python
# Metrics to track
metrics = {
    "short_term": {
        "memory_count": gauge,
        "ingestion_time": histogram,
        "search_time": histogram,
        "disk_usage": gauge
    },
    "shuttle": {
        "sync_queue_size": gauge,
        "sync_success_rate": counter,
        "sync_latency": histogram,
        "conflicts_resolved": counter
    }
}
```

## References

- [Local Development Setup](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md) - **Required prerequisite**
- [Backend API Documentation](./JEAN_MEMORY_BACKEND_API.md) - For API modifications
- [Database Schema](./JEAN_MEMORY_DATABASE_SCHEMA.md) - For storage layer details
- [MCP Integration](./JEAN_MEMORY_MCP_INTEGRATION.md) - For tool updates