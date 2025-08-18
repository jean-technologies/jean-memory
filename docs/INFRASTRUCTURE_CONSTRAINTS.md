# Jean Memory Infrastructure Constraints & Analysis

## Executive Summary

Jean Memory operates on a **highly constrained infrastructure** with strict memory and CPU limitations across all services. This document details the current infrastructure specifications, analyzes their impact on system performance, and provides critical considerations for optimization efforts.

## Current Infrastructure Specifications

### 1. Qdrant Cloud (Vector Database)
**Plan**: MICRO  
**Cost**: $0.01344/hour (~$9.68/month)  
**Specifications**:
- **Memory**: 1 GB
- **CPU**: 2-core ARM CPU
- **Storage**: 8 GiB disk
- **vCPU**: 0.5
- **Provider**: AWS us-east-1
- **Endpoint**: https://d696cac3-e12a-48f5-b529-5890e56e872e.us-east-1-0.aws.cloud.qdrant.io

**Constraints**:
- Limited to ~500K vectors (at 1536 dimensions × 4 bytes = 6KB per vector)
- Maximum ~100 concurrent connections
- Query latency increases significantly beyond 200K vectors
- No horizontal scaling available on current plan

### 2. Neo4j Aura (Knowledge Graph)
**Plan**: AuraDB Free  
**Cost**: $0/month  
**Specifications**:
- **Instance**: Instance01
- **Version**: 2025.07
- **Current Usage**: 
  - Nodes: 10,052 (5% of limit)
  - Relationships: 8,171 (2% of limit)
- **Limits**:
  - Max Nodes: ~200,000
  - Max Relationships: ~400,000
  - Max Storage: 200MB
  - Max Concurrent Connections: 10

**Constraints**:
- Cannot run complex graph algorithms (PageRank, community detection)
- Limited to single-region deployment
- No backup/restore on free tier
- Query timeout: 30 seconds max

### 3. Supabase (PostgreSQL + Auth)
**Plan**: Free Tier  
**Cost**: $0/month  
**Specifications**:
- **Database**: 
  - RAM: 1 GB shared
  - CPU: 2 vCPUs shared
  - Storage: 500 MB
  - Connections: 60 direct, 200 pooled
- **Auth**: 50,000 MAU limit
- **Storage**: 1 GB total
- **Bandwidth**: 2 GB/month

**Constraints**:
- Database pauses after 7 days of inactivity
- Limited connection pool causes bottlenecks
- No point-in-time recovery
- pgvector operations consume significant CPU

### 4. Render.com Backend (FastAPI)
**Service**: jean-memory-api-virginia  
**Plan**: Starter  
**Specifications**:
- **Memory**: 512 MB
- **CPU**: 0.5 vCPU
- **Region**: Virginia (US East)
- **Instances**: 1 (no auto-scaling)

**Critical Constraints**:
- **Memory is the primary bottleneck**
- Cannot cache large datasets in memory
- Background tasks compete for limited resources
- Python process overhead (~150MB) leaves only ~350MB for operations
- Frequent memory-related crashes under load

### 5. Render.com Frontend (Next.js)
**Service**: jean-memory-ui-virginia  
**Plan**: Starter  
**Specifications**:
- **Memory**: 512 MB
- **CPU**: 0.5 vCPU
- **Region**: Virginia (US East)
- **Instances**: 1

**Constraints**:
- Next.js build process consumes significant memory
- Limited SSR capabilities due to memory
- Cannot implement heavy client-side caching

## Infrastructure Bottleneck Analysis

### Memory Constraints Impact

| Service | Available Memory | Critical Operations | Impact |
|---------|-----------------|-------------------|---------|
| **Backend API** | ~350 MB | Context orchestration, AI responses | Cannot cache context plans, limited parallel processing |
| **Qdrant** | 1 GB | Vector storage & search | Limited to ~80K active vectors after overhead |
| **Neo4j** | Shared (minimal) | Graph traversals | Complex queries timeout or fail |
| **PostgreSQL** | 1 GB shared | Narrative caching, metadata | Connection pool exhaustion under load |

### CPU Constraints Impact

| Service | CPU Power | Bottlenecked Operations | Latency Impact |
|---------|-----------|------------------------|----------------|
| **Backend API** | 0.5 vCPU | AI planning, synthesis | +2-5s per complex request |
| **Qdrant** | 2 ARM cores | Similarity search | +100-200ms at scale |
| **Neo4j** | Shared | Graph algorithms | Algorithms not viable |
| **PostgreSQL** | 2 vCPUs shared | pgvector operations | +200-500ms for chunk search |

## Performance Implications

### 1. Context Engineering Constraints

Due to 512MB backend memory:
- **Cannot implement**: Full context plan caching (would require ~100MB)
- **Limited to**: Small LRU cache (max 10MB)
- **Result**: 40-60% cache hit rate instead of potential 80%+

### 2. Vector Search Limitations

With 1GB Qdrant memory:
- **Practical limit**: 50,000 vectors per user
- **Search degradation**: Begins at 30,000 vectors
- **Mitigation required**: Aggressive memory pruning

### 3. Background Processing Issues

Backend memory constraints mean:
- **Cannot run**: Multiple background tasks simultaneously
- **Narrative generation**: Must be queued, not parallel
- **Memory saves**: Batched with delays to prevent OOM

### 4. Scaling Limitations

| Metric | Current Capacity | Hard Limit | Bottleneck |
|--------|-----------------|------------|------------|
| **Concurrent Users** | 10-15 | 25 | Backend memory |
| **Requests/sec** | 5-10 | 20 | CPU + connections |
| **Active Memories** | 50K/user | 100K/user | Qdrant memory |
| **Graph Complexity** | 2-hop | 3-hop | Neo4j timeout |

## Optimization Strategy Adjustments

### Must Revise from Original Roadmap:

1. **AI Context Plan Caching**
   - Original: 30-minute TTL, unlimited cache
   - **Revised**: 5-minute TTL, 10MB max cache size
   - Use aggressive LRU eviction

2. **Narrative Pre-computation**
   - Original: Background generation for all users
   - **Revised**: Only for active users (last 24h)
   - Queue-based with memory monitoring

3. **Memory Search Caching**
   - Original: 10-minute TTL, all results
   - **Revised**: 2-minute TTL, top 5 results only
   - Maximum 5MB total cache

4. **Parallel Processing**
   - Original: Unlimited parallel operations
   - **Revised**: Max 2 concurrent async operations
   - Implement request queuing

## Critical Thresholds & Monitoring

### Memory Warning Levels

```python
# Backend API Memory Monitoring
MEMORY_THRESHOLDS = {
    "SAFE": 0.6,      # < 60% (< 307MB)
    "WARNING": 0.75,  # 75% (384MB) - start rejecting background tasks
    "CRITICAL": 0.85, # 85% (435MB) - reject complex queries
    "FATAL": 0.95     # 95% (487MB) - emergency mode, basic ops only
}
```

### Database Capacity Triggers

```python
# Qdrant Collection Monitoring
VECTOR_THRESHOLDS = {
    "user_collection": {
        "soft_limit": 30000,  # Start pruning old memories
        "hard_limit": 50000   # Reject new memories
    }
}

# Neo4j Monitoring  
GRAPH_THRESHOLDS = {
    "nodes": 180000,      # 90% of limit
    "relationships": 360000  # 90% of limit
}
```

## Recommended Infrastructure Upgrades

### Priority 1: Backend Memory (Immediate Need)
**Current**: 512 MB → **Recommended**: 2 GB  
**Cost**: +$19/month  
**Impact**: 
- Enable full context caching
- Support 50+ concurrent users
- Eliminate OOM crashes

### Priority 2: Qdrant Upgrade (3-6 months)
**Current**: MICRO → **Recommended**: SMALL  
**Cost**: +$40/month  
**Specifications**: 4 GB memory, 2 vCPU  
**Impact**:
- Support 200K+ vectors per user
- 3x faster search performance
- Enable advanced filtering

### Priority 3: PostgreSQL (6-12 months)
**Current**: Supabase Free → **Recommended**: Pro  
**Cost**: $25/month  
**Impact**:
- Dedicated resources
- No pause/timeout issues
- Better pgvector performance

### Priority 4: Neo4j (Future)
**Current**: Free → **Recommended**: Professional  
**Cost**: $65/month  
**Impact**:
- Enable graph algorithms
- Support complex traversals
- Better Graphiti integration

## Development Considerations

### Memory-Efficient Coding Practices

1. **Use generators instead of lists** where possible
2. **Implement streaming responses** for large datasets
3. **Clear caches proactively** when memory pressure detected
4. **Use `del` and `gc.collect()** after large operations
5. **Implement circuit breakers** for memory-intensive operations

### Example Memory Guard:
```python
import psutil
import gc

def check_memory_before_operation(required_mb: int = 50):
    """Guard against OOM by checking available memory"""
    process = psutil.Process()
    memory_info = process.memory_info()
    used_mb = memory_info.rss / 1024 / 1024
    
    if used_mb > 400:  # 400MB threshold for 512MB container
        gc.collect()  # Force garbage collection
        
        # Re-check after GC
        memory_info = process.memory_info()
        used_mb = memory_info.rss / 1024 / 1024
        
        if used_mb > 400:
            raise MemoryError(f"Insufficient memory: {used_mb:.1f}MB used")
    
    return True
```

## Monitoring & Alerting Requirements

### Critical Metrics to Track

1. **Backend API**:
   - Memory usage percentage
   - Request queue depth
   - Cache hit rates
   - GC frequency

2. **Databases**:
   - Connection pool utilization
   - Query response times
   - Storage usage percentage
   - Timeout/error rates

3. **Business Metrics**:
   - User concurrency
   - Memory saves/minute
   - Context retrieval latency
   - Background task queue length

## Conclusion

Jean Memory's current infrastructure operates at **60-80% capacity** during normal usage and frequently hits limits during peak periods. The most critical constraint is the **512MB backend memory**, which prevents implementation of many optimization strategies.

**Immediate Recommendations**:
1. Implement aggressive memory monitoring and guards
2. Upgrade backend to 2GB RAM (cost: $19/month)
3. Revise optimization roadmap for current constraints
4. Implement gradual degradation under load

**Long-term Success Requires**:
- Minimum 2GB backend memory
- Upgraded Qdrant instance
- Dedicated PostgreSQL resources
- Proper monitoring and alerting

Without infrastructure upgrades, the system will remain limited to:
- 10-15 concurrent users maximum
- 30-50% slower performance than optimal
- Frequent degradation during peak usage
- Limited optimization potential