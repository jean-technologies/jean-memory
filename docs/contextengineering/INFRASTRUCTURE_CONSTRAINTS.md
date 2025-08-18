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
**Plan**: Standard  
**Specifications**:
- **Memory**: 2 GB
- **CPU**: 1 vCPU
- **Region**: Virginia (US East)
- **Instances**: 1 (no auto-scaling)

**Current Capabilities** (Post-Upgrade):
- Sufficient memory for context caching
- Can handle multiple concurrent operations
- Background tasks have adequate resources
- Python process overhead (~150MB) leaves ~1.85GB for operations
- Stable performance under normal load

### 5. Render.com Frontend (Next.js)
**Service**: jean-memory-ui-virginia  
**Plan**: Standard  
**Specifications**:
- **Memory**: 2 GB
- **CPU**: 1 vCPU
- **Region**: Virginia (US East)
- **Instances**: 1

**Current Capabilities** (Post-Upgrade):
- Adequate memory for build process
- Full SSR capabilities enabled
- Can implement moderate client-side caching

## Infrastructure Bottleneck Analysis

### Memory Constraints Impact

| Service | Available Memory | Critical Operations | Impact |
|---------|-----------------|-------------------|---------|
| **Backend API** | ~1.85 GB | Context orchestration, AI responses | Can cache context plans, supports parallel processing |
| **Qdrant** | 1 GB | Vector storage & search | Limited to ~80K active vectors after overhead |
| **Neo4j** | Shared (minimal) | Graph traversals | Complex queries timeout or fail |
| **PostgreSQL** | 1 GB shared | Narrative caching, metadata | Connection pool exhaustion under load |

### CPU Constraints Impact

| Service | CPU Power | Bottlenecked Operations | Latency Impact |
|---------|-----------|------------------------|----------------|
| **Backend API** | 1 vCPU | AI planning, synthesis | +1-2s per complex request |
| **Qdrant** | 2 ARM cores | Similarity search | +100-200ms at scale |
| **Neo4j** | Shared | Graph algorithms | Algorithms not viable |
| **PostgreSQL** | 2 vCPUs shared | pgvector operations | +200-500ms for chunk search |

## Performance Implications

### 1. Context Engineering Constraints

With 2GB backend memory:
- **Can implement**: Full context plan caching (~200MB)
- **Supports**: Large LRU cache (up to 500MB)
- **Result**: 70-85% cache hit rate achievable

### 2. Vector Search Limitations

With 1GB Qdrant memory:
- **Practical limit**: 50,000 vectors per user
- **Search degradation**: Begins at 30,000 vectors
- **Mitigation required**: Aggressive memory pruning

### 3. Background Processing Issues

With upgraded backend memory:
- **Can run**: 3-5 background tasks simultaneously
- **Narrative generation**: Can process in parallel (limited by CPU)
- **Memory saves**: Real-time processing without OOM concerns

### 4. Scaling Limitations

| Metric | Current Capacity | Hard Limit | Bottleneck |
|--------|-----------------|------------|------------|
| **Concurrent Users** | 30-40 | 60 | Backend CPU/Qdrant |
| **Requests/sec** | 5-10 | 20 | CPU + connections |
| **Active Memories** | 50K/user | 100K/user | Qdrant memory |
| **Graph Complexity** | 2-hop | 3-hop | Neo4j timeout |

## Optimization Strategy Adjustments

### Must Revise from Original Roadmap:

1. **AI Context Plan Caching**
   - Original: 30-minute TTL, unlimited cache
   - **Current Capacity**: 15-minute TTL, 200MB cache size
   - Standard LRU eviction with monitoring

2. **Narrative Pre-computation**
   - Original: Background generation for all users
   - **Revised**: Only for active users (last 24h)
   - Queue-based with memory monitoring

3. **Memory Search Caching**
   - Original: 10-minute TTL, all results
   - **Current Capacity**: 5-minute TTL, top 20 results
   - Maximum 100MB total cache

4. **Parallel Processing**
   - Original: Unlimited parallel operations
   - **Current Capacity**: Max 5 concurrent async operations
   - Smart request queuing with priority

## Critical Thresholds & Monitoring

### Memory Warning Levels

```python
# Backend API Memory Monitoring (2GB)
MEMORY_THRESHOLDS = {
    "SAFE": 0.6,      # < 60% (< 1.2GB)
    "WARNING": 0.75,  # 75% (1.5GB) - optimize background tasks
    "CRITICAL": 0.85, # 85% (1.7GB) - limit complex queries
    "FATAL": 0.95     # 95% (1.9GB) - emergency mode
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

### Priority 1: Backend Memory (COMPLETED)
**Upgraded**: 512 MB → 2 GB (Standard Plan)  
**Cost**: +$19/month  
**Achieved Impact**: 
- ✅ Full context caching enabled
- ✅ Support for 30-40 concurrent users
- ✅ OOM crashes eliminated

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
    
    if used_mb > 1600:  # 1600MB threshold for 2GB container
        gc.collect()  # Force garbage collection
        
        # Re-check after GC
        memory_info = process.memory_info()
        used_mb = memory_info.rss / 1024 / 1024
        
        if used_mb > 1600:
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

Jean Memory's infrastructure has been upgraded and now operates at **40-60% capacity** during normal usage. The backend memory upgrade to 2GB has resolved the primary bottleneck. The current critical constraints are **Qdrant memory (1GB)** and **backend CPU (1 vCPU)** for scaling beyond 40 concurrent users.

**Immediate Recommendations** (Post-Upgrade):
1. ✅ Backend upgraded to 2GB RAM (completed)
2. Focus optimization on Qdrant and CPU efficiency
3. Implement advanced caching strategies now possible
4. Plan for Qdrant upgrade as next priority

**Long-term Success Requires**:
- Minimum 2GB backend memory
- Upgraded Qdrant instance
- Dedicated PostgreSQL resources
- Proper monitoring and alerting

With the backend upgrade complete, the system now supports:
- 30-40 concurrent users (up from 10-15)
- 20-30% faster performance
- Stable operation during normal usage
- Significant optimization potential unlocked

Next bottlenecks to address:
- Qdrant memory for vector storage scaling
- CPU for complex AI operations
- PostgreSQL connection pooling