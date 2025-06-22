# R&D Improvement Plan - Immediate Actions

## System Check Summary

### Current State
- ✅ **mem0 Vector (Qdrant)**: 153 memories stored, search working
- ✅ **mem0 Graph (Neo4j)**: 30 Memory nodes, entity extraction working
- ✅ **RAG Pipeline**: Proper LLM responses with context
- ⚠️ **Graphiti Episodes**: No episodes created (0 found)
- ❌ **PostgreSQL Metadata**: Type mismatch (json vs jsonb)

## Immediate Improvements (This Week)

### 1. Fix Graphiti Episode Generation

**Problem**: Episodes are not being created despite having the code
**Root Cause**: Insufficient memories per temporal group

```python
# Current code only creates episodes if group has 2+ memories
if len(group_memories) >= 2:
    await create_temporal_episode(...)
```

**Solution**: Improve temporal grouping and episode creation

```python
# enhanced_episode_generation.py
async def create_smart_episodes(memories: List[Dict], graphiti_client):
    """Create episodes using multiple strategies"""
    
    # Strategy 1: Time-based clustering (same day/week)
    time_clusters = cluster_by_time_window(memories, window_hours=24)
    
    # Strategy 2: Topic-based clustering
    topic_clusters = cluster_by_semantic_similarity(memories, threshold=0.7)
    
    # Strategy 3: Entity-based clustering
    entity_clusters = cluster_by_shared_entities(memories)
    
    # Create episodes for each clustering strategy
    for cluster_type, clusters in [
        ("temporal", time_clusters),
        ("topical", topic_clusters),
        ("entity", entity_clusters)
    ]:
        for cluster_id, cluster_memories in clusters.items():
            if len(cluster_memories) >= 1:  # Allow single-memory episodes
                await create_episode(
                    graphiti_client,
                    memories=cluster_memories,
                    episode_type=cluster_type,
                    episode_name=f"{cluster_type}_{cluster_id}"
                )
```

### 2. Enhanced Memory Preprocessing

**Current Issue**: Simple memory content without rich context

```python
# memory_preprocessor.py
class MemoryPreprocessor:
    """Enhanced memory preprocessing for better ingestion"""
    
    async def preprocess(self, raw_memory: str) -> Dict[str, Any]:
        # Extract temporal markers
        temporal_info = self.extract_temporal_context(raw_memory)
        
        # Extract entities with confidence
        entities = await self.extract_entities_with_confidence(raw_memory)
        
        # Detect memory type
        memory_type = self.classify_memory_type(raw_memory)
        
        # Generate embedding-friendly summary
        summary = await self.generate_summary(raw_memory)
        
        return {
            "original": raw_memory,
            "summary": summary,
            "temporal_context": temporal_info,
            "entities": entities,
            "memory_type": memory_type,
            "keywords": self.extract_keywords(raw_memory),
            "sentiment": self.analyze_sentiment(raw_memory)
        }
    
    def extract_temporal_context(self, text: str) -> Dict:
        """Extract time-related information"""
        # Use dateparser and custom patterns
        patterns = {
            'recurring': r'(every|daily|weekly|monthly)',
            'past': r'(yesterday|last week|ago)',
            'future': r'(tomorrow|next|will)',
            'ongoing': r'(currently|now|these days)'
        }
        # ... implementation
```

### 3. Hybrid Search Implementation

**Goal**: Combine vector, graph, and temporal search

```python
# hybrid_search.py
class HybridSearchEngine:
    def __init__(self, mem0_client, graphiti_client):
        self.mem0 = mem0_client
        self.graphiti = graphiti_client
    
    async def search(self, query: str, user_id: str) -> SearchResults:
        # 1. Vector search (semantic similarity)
        vector_results = await self.mem0.search(query, user_id, limit=20)
        
        # 2. Graph search (entity relationships)
        entities = await self.extract_query_entities(query)
        graph_results = await self.search_by_entities(entities, user_id)
        
        # 3. Temporal search (time-based)
        temporal_markers = self.extract_temporal_markers(query)
        temporal_results = await self.search_by_time(temporal_markers, user_id)
        
        # 4. Merge and rank results
        merged_results = self.merge_results(
            vector_results, 
            graph_results, 
            temporal_results
        )
        
        # 5. Re-rank using cross-encoder
        final_results = await self.rerank_results(query, merged_results)
        
        return final_results
```

### 4. Fix PostgreSQL Metadata Integration

**Problem**: Column type mismatch (json vs jsonb)

```python
# database_adapter.py
class ProductionDatabaseAdapter:
    """Handle production database schema differences"""
    
    def get_memories_with_metadata(self, user_id: str) -> List[Dict]:
        query = """
        SELECT 
            id, user_id, content, 
            metadata::jsonb as metadata,  -- Cast to jsonb
            created_at, updated_at
        FROM memories
        WHERE user_id = %s 
        AND deleted_at IS NULL
        AND metadata IS NOT NULL
        AND metadata::text != '{}'  -- Text comparison instead of jsonb
        """
        # ... implementation
```

### 5. Query Understanding Enhancement

**Goal**: Better interpret user intent

```python
# query_processor.py
class QueryProcessor:
    """Enhanced query understanding"""
    
    async def process_query(self, query: str) -> QueryIntent:
        # 1. Classify query type
        query_type = await self.classify_query_type(query)
        # Types: factual, temporal, relationship, analytical
        
        # 2. Extract query components
        components = {
            "entities": await self.extract_entities(query),
            "temporal": self.extract_temporal_markers(query),
            "intent": await self.detect_intent(query),
            "scope": self.determine_scope(query)
        }
        
        # 3. Expand query with synonyms/related terms
        expanded_query = await self.expand_query(query)
        
        # 4. Generate search strategies
        strategies = self.generate_search_strategies(
            query_type, 
            components
        )
        
        return QueryIntent(
            original=query,
            type=query_type,
            components=components,
            expanded=expanded_query,
            strategies=strategies
        )
```

## Testing Strategy

### 1. Create Test Datasets
```python
# test_datasets.py
test_memories = {
    "temporal_test": [
        "I go to the gym every Monday and Wednesday",
        "Last week I started a new workout routine",
        "Tomorrow I'm meeting my trainer at 5pm"
    ],
    "entity_test": [
        "Had dinner with John at Luigi's restaurant",
        "John recommended the pasta at Luigi's",
        "Luigi's has the best Italian food in town"
    ],
    "episode_test": [
        "Started my trip to Paris on June 1st",
        "Visited the Eiffel Tower on June 2nd",
        "Had lunch at a cafe near the Louvre on June 2nd",
        "Flew back home on June 5th"
    ]
}
```

### 2. Benchmark Queries
```python
benchmark_queries = [
    # Temporal queries
    "What did I do last week?",
    "What are my recurring activities?",
    
    # Entity queries  
    "Tell me about John",
    "Where have I eaten recently?",
    
    # Analytical queries
    "How has my routine changed?",
    "What patterns do you see in my activities?",
    
    # Complex queries
    "Who did I meet at restaurants last month?",
    "What projects am I working on and who's involved?"
]
```

## Implementation Priority

1. **Day 1-2**: Fix Graphiti episode generation
   - Implement clustering strategies
   - Test with existing data
   - Verify episodes in Neo4j

2. **Day 3-4**: Enhance preprocessing
   - Build temporal extractor
   - Improve entity extraction
   - Add memory classification

3. **Day 5-6**: Implement hybrid search
   - Build search merger
   - Add re-ranking
   - Test with benchmarks

4. **Day 7**: Integration testing
   - Full pipeline test
   - Performance benchmarks
   - Quality metrics

## Success Metrics

1. **Episode Generation**
   - Target: >80% of memories assigned to episodes
   - Episode quality score: >0.7

2. **Search Quality**
   - Retrieval accuracy: >85%
   - Response relevance: >4/5 user rating
   - Latency: <500ms p95

3. **Entity Extraction**
   - Precision: >90%
   - Recall: >80%
   - Relationship accuracy: >85%

## Next Steps

1. Implement improvements in order of priority
2. Test with existing datasets
3. Collect metrics and iterate
4. Prepare for production deployment 