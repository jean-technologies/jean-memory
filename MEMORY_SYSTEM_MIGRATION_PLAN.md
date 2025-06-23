# Memory System Migration Plan: From Qdrant Cloud to Multi-Layer RAG

**Date**: December 22, 2024  
**Status**: Planning Phase  
**Goal**: Seamlessly migrate from single-layer Qdrant Cloud to multi-layer pgvector + Neo4j + Graphiti system

## 📋 Executive Summary

This plan outlines the migration strategy from your current Qdrant Cloud-based memory system to the new multi-layer RAG architecture featuring:
- **pgvector** (PostgreSQL) for vector embeddings
- **Neo4j** for graph relationships and temporal episodes
- **Graphiti** for episodic memory clustering
- **Enhanced retrieval** with semantic, relational, and temporal search

## 🔍 Current System Analysis

### **1. Current Infrastructure**
- **Vector Store**: Qdrant Cloud (`openmemory_prod` collection)
- **Memory Client**: mem0 with Qdrant provider
- **Embedding Model**: OpenAI text-embedding-3-small
- **LLM**: GPT-4o-mini for memory extraction

### **2. Current Endpoints**

#### **MCP Tools** (`mcp_tools.py`, `mcp_server.py`)
- `add_memories`: Ingests text into mem0/Qdrant
- `search_memory`: Semantic search with optional tag filtering
- `list_memories`: Retrieves all memories with pagination
- `deep_memory_query`: Comprehensive search including documents

#### **API Endpoints** (`memories.py`)
- `POST /api/v1/memories/`: Create new memory
- `GET /api/v1/memories/search`: Search memories
- `POST /api/v1/narrative/generate`: Generate life narrative

#### **Frontend Features**
- Create New Memory (UI form)
- Deep Life Query (Gemini-powered analysis)
- Generate Narrative (Gemini biographer)

### **3. Key Observations**
- All endpoints use `get_memory_client()` which initializes mem0 with Qdrant
- Configuration is centralized in `settings.py`
- PostHog tracking is integrated for analytics
- Tag-based filtering is supported
- Document chunking is handled separately

## 🎯 Migration Strategy

### **Phase 1: Infrastructure Compatibility Layer** (Week 1)

#### **1.1 Create Unified Memory Client**
```python
# openmemory/api/app/utils/unified_memory.py
class UnifiedMemoryClient:
    """Compatibility layer supporting both old and new systems"""
    
    def __init__(self, use_new_system=False):
        self.use_new_system = use_new_system
        
        if use_new_system:
            # Initialize new multi-layer system
            self.mem0_client = self._init_mem0_pgvector()
            self.graphiti_client = self._init_graphiti()
            self.neo4j_driver = self._init_neo4j()
        else:
            # Use existing Qdrant system
            self.mem0_client = get_memory_client()
    
    async def add(self, text, user_id, metadata=None):
        if self.use_new_system:
            # Add to pgvector + create graph relationships
            result = await self._add_to_unified_system(text, user_id, metadata)
            # Create episodic memories asynchronously
            asyncio.create_task(self._create_episodes(user_id))
            return result
        else:
            # Use existing mem0/Qdrant
            return self.mem0_client.add(text, user_id=user_id, metadata=metadata)
    
    async def search(self, query, user_id, limit=10):
        if self.use_new_system:
            # Multi-layer search
            return await self._unified_search(query, user_id, limit)
        else:
            # Existing Qdrant search
            return self.mem0_client.search(query=query, user_id=user_id, limit=limit)
```

#### **1.2 Environment Configuration**
```python
# Add to settings.py
class Config:
    # ... existing config ...
    
    # New system configuration
    USE_UNIFIED_MEMORY = os.getenv("USE_UNIFIED_MEMORY", "false").lower() == "true"
    
    # PostgreSQL for pgvector
    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "")
    PG_DBNAME = os.getenv("PG_DBNAME", "mem0_unified")
    
    # Neo4j configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
```

### **Phase 2: API Integration** (Week 2)

#### **2.1 Update Memory Utils**
```python
# openmemory/api/app/utils/memory.py
def get_memory_client(custom_instructions: str = None):
    """Get appropriate memory client based on configuration"""
    if config.USE_UNIFIED_MEMORY:
        from app.utils.unified_memory import UnifiedMemoryClient
        return UnifiedMemoryClient(use_new_system=True)
    else:
        # Existing Qdrant implementation
        return _get_qdrant_memory_client(custom_instructions)
```

#### **2.2 Enhance MCP Tools**
```python
# Update mcp_server.py search_memory function
async def search_memory(query: str, limit: int = None, tags_filter: Optional[list[str]] = None) -> str:
    memory_client = get_memory_client()
    
    if config.USE_UNIFIED_MEMORY:
        # Enhanced multi-layer search
        results = await memory_client.search_multilayer(
            query=query,
            user_id=supa_uid,
            limit=limit,
            search_types=["semantic", "graph", "episodic"],
            filters={"tags": tags_filter} if tags_filter else None
        )
        
        # Format results with source attribution
        formatted_results = []
        for result in results:
            formatted_results.append({
                "memory": result["content"],
                "confidence": result.get("score", 1.0),
                "source": result.get("source", "unified"),
                "relationships": result.get("relationships", []),
                "episode": result.get("episode_name")
            })
        
        return json.dumps(formatted_results, indent=2)
    else:
        # Existing implementation
        return await _search_memory_unified_impl(query, supa_uid, client_name, limit, tags_filter)
```

### **Phase 3: Enhanced Features** (Week 3)

#### **3.1 Episode-Aware Deep Query**
```python
# Enhanced deep_memory_query implementation
async def _deep_memory_query_impl(search_query: str, supa_uid: str, client_name: str, memory_limit: int = None, chunk_limit: int = None, include_full_docs: bool = True) -> str:
    
    if config.USE_UNIFIED_MEMORY:
        # Multi-layer comprehensive search
        memory_client = get_memory_client()
        
        # 1. Get semantic memories
        semantic_results = await memory_client.search_semantic(search_query, supa_uid, limit=memory_limit)
        
        # 2. Get graph relationships
        graph_results = await memory_client.search_graph(search_query, supa_uid)
        
        # 3. Get temporal episodes
        episode_results = await memory_client.search_episodes(search_query, supa_uid)
        
        # 4. Get document chunks (existing logic)
        chunk_results = chunking_service.search_chunks(db, search_query, str(user.id), limit=chunk_limit)
        
        # 5. Build enhanced context
        context = _build_multilayer_context(
            semantic_results,
            graph_results,
            episode_results,
            chunk_results
        )
        
        # 6. Generate response with source attribution
        response = await _generate_attributed_response(search_query, context)
        
        return response
    else:
        # Existing implementation
        # ... current deep query logic ...
```

#### **3.2 Narrative Generation with Episodes**
```python
# Enhanced narrative generation
async def generate_narrative(self, memories: List[str]) -> str:
    if config.USE_UNIFIED_MEMORY:
        # Get episodic structure
        episodes = await self._get_user_episodes(user_id)
        
        # Enhanced prompt with temporal structure
        prompt = f"""
        You are an expert biographer. Based on the following memories organized by episodes and themes,
        write a compelling narrative about this person's life journey.
        
        Episodes:
        {self._format_episodes(episodes)}
        
        Individual Memories:
        {"\n".join(memories)}
        
        Focus on:
        1. Character development and growth over time
        2. Key relationships and their evolution
        3. Major life themes and patterns
        4. Turning points and transformative moments
        """
        
        response = await self.model.generate_content_async(prompt)
        return response.text
```

### **Phase 4: Data Migration** (Week 4)

#### **4.1 Migration Script**
```python
# scripts/migrate_to_unified_memory.py
async def migrate_user_memories(user_id: str, batch_size: int = 100):
    """Migrate a single user's memories from Qdrant to unified system"""
    
    # 1. Export from Qdrant
    old_client = get_qdrant_client()
    new_client = UnifiedMemoryClient(use_new_system=True)
    
    offset = None
    migrated_count = 0
    
    while True:
        # Fetch batch from Qdrant
        results = old_client.scroll(
            collection_name=config.QDRANT_COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=batch_size,
            offset=offset
        )
        
        if not results[0]:
            break
        
        # Migrate each memory
        for point in results[0]:
            memory_data = {
                "text": point.payload.get("data", ""),
                "metadata": point.payload,
                "created_at": point.payload.get("created_at"),
                "vector": point.vector  # Preserve original embedding
            }
            
            # Add to new system
            await new_client.add_with_vector(
                text=memory_data["text"],
                user_id=user_id,
                metadata=memory_data["metadata"],
                vector=memory_data["vector"]
            )
            
            migrated_count += 1
        
        offset = results[1]
        if not offset:
            break
    
    # 2. Generate episodes for migrated memories
    await new_client.generate_user_episodes(user_id)
    
    return migrated_count
```

#### **4.2 Gradual Rollout**
```python
# Feature flag by user
def should_use_unified_memory(user_id: str) -> bool:
    """Determine if user should use new system"""
    
    # Option 1: Percentage rollout
    if config.UNIFIED_MEMORY_ROLLOUT_PERCENTAGE:
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        return (user_hash % 100) < config.UNIFIED_MEMORY_ROLLOUT_PERCENTAGE
    
    # Option 2: Explicit user list
    if config.UNIFIED_MEMORY_USER_IDS:
        return user_id in config.UNIFIED_MEMORY_USER_IDS.split(',')
    
    # Option 3: User preference
    user = get_user(user_id)
    return user.preferences.get('use_unified_memory', False)
```

### **Phase 5: Production Deployment** (Week 5)

#### **5.1 Infrastructure Setup**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: mem0_unified
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - pgvector_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  neo4j:
    image: neo4j:5.15.0
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes:
      - neo4j_data:/data
    ports:
      - "7474:7474"
      - "7687:7687"
  
  api:
    build: .
    environment:
      USE_UNIFIED_MEMORY: "true"
      PG_HOST: postgres
      NEO4J_URI: bolt://neo4j:7687
    depends_on:
      - postgres
      - neo4j
```

#### **5.2 Monitoring & Observability**
```python
# Add metrics for comparison
class MemoryMetrics:
    def track_operation(self, operation: str, system: str, duration: float, success: bool):
        posthog.capture(
            user_id="system",
            event="memory_operation",
            properties={
                "operation": operation,  # add, search, list
                "system": system,       # qdrant, unified
                "duration_ms": duration * 1000,
                "success": success
            }
        )
    
    def track_search_quality(self, query: str, system: str, results_count: int, relevance_scores: List[float]):
        posthog.capture(
            user_id="system",
            event="search_quality",
            properties={
                "system": system,
                "query_length": len(query),
                "results_count": results_count,
                "avg_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
                "max_relevance": max(relevance_scores) if relevance_scores else 0
            }
        )
```

## 🚀 Implementation Timeline

### **Week 1: Foundation**
- [ ] Set up local pgvector and Neo4j instances
- [ ] Implement UnifiedMemoryClient with compatibility layer
- [ ] Create configuration management
- [ ] Write unit tests for new client

### **Week 2: Integration**
- [ ] Update all endpoints to use new client conditionally
- [ ] Implement multi-layer search logic
- [ ] Add episode generation pipeline
- [ ] Test with synthetic data

### **Week 3: Enhancement**
- [ ] Enhance deep query with multi-layer retrieval
- [ ] Improve narrative generation with episodes
- [ ] Add relationship visualization endpoints
- [ ] Performance optimization

### **Week 4: Migration**
- [ ] Create migration scripts
- [ ] Test migration with sample users
- [ ] Implement rollback procedures
- [ ] Document migration process

### **Week 5: Deployment**
- [ ] Deploy infrastructure to staging
- [ ] Run A/B tests with small user group
- [ ] Monitor performance metrics
- [ ] Gradual rollout to all users

## 🔒 Risk Mitigation

### **1. Data Consistency**
- Dual-write during migration period
- Checksum validation for migrated data
- Ability to re-sync from Qdrant if needed

### **2. Performance**
- Cache frequently accessed episodes
- Optimize Neo4j queries with indexes
- Use connection pooling for all databases

### **3. Rollback Strategy**
- Feature flags for instant rollback
- Keep Qdrant data for 30 days post-migration
- Automated health checks with fallback

## 📊 Success Metrics

### **Technical Metrics**
- Query latency: < 500ms for 95th percentile
- Ingestion throughput: > 100 memories/second
- Episode generation: < 2 seconds per batch
- System availability: 99.9% uptime

### **Quality Metrics**
- Search relevance: > 20% improvement in user satisfaction
- Episode coherence: > 80% accuracy in temporal grouping
- Relationship accuracy: > 90% for extracted entities

### **Business Metrics**
- User engagement: Increase in deep queries by 30%
- Feature adoption: 80% of users using episodic search
- Cost efficiency: 40% reduction in vector storage costs

## 🎯 Next Steps

1. **Immediate Actions**:
   - Review and approve migration plan
   - Set up development environment with new infrastructure
   - Create proof of concept with test user

2. **Team Preparation**:
   - Technical documentation for new system
   - Training on Neo4j and Graphiti
   - Update runbooks and monitoring

3. **Communication**:
   - Announce enhanced features to users
   - Prepare migration notifications
   - Create user documentation for new capabilities

## 📝 Conclusion

This migration plan provides a safe, gradual path from your current Qdrant-based system to the new multi-layer RAG architecture. The compatibility layer ensures zero downtime, while feature flags enable controlled rollout and instant rollback if needed.

The new system will provide:
- **Richer memory representation** with graph relationships
- **Temporal intelligence** through episodic clustering
- **Better search quality** with multi-layer retrieval
- **Enhanced narratives** with structured life episodes

By following this plan, you'll upgrade your memory system while maintaining stability and improving user experience. 