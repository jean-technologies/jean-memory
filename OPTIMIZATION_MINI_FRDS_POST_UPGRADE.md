# Jean Memory Optimization Mini-FRDs and Mini-EDDs (Post-2GB Upgrade)

## ✅ Infrastructure Upgrade Complete

**Backend upgraded to 2GB RAM** - This document has been revised to reflect our new capabilities and optimize for 50-100 concurrent users.

## Current Infrastructure Reality

**Backend**: 2GB RAM, 1 vCPU (Render Standard plan)
**Databases**: Qdrant MICRO (1GB), Neo4j Free, Supabase Free
**User Scale Target**: 50-100 concurrent users
**Available Memory**: ~1400MB after overhead

---

## **Item 1: Smart Query Classification (Zero Memory, Maximum Impact)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Pattern-match simple queries (greetings, basic questions) to completely bypass AI planning and database calls, providing instant responses.

2. **Why** – 25-40% of queries are simple and don't need context. This zero-memory optimization provides 95% speedup for these queries, reducing overall system load.

3. **Scope** 
   
   **In Scope:**
   - Comprehensive pattern library (greetings, farewells, simple questions)
   - Template-based instant responses
   - Language variation support
   - Confidence scoring for classification
   
   **Out of Scope:**
   - ML-based classification
   - User-specific patterns
   - Complex NLP analysis

4. **Acceptance Criteria**
   - Identifies 90%+ of simple queries correctly
   - Response time: 2-12s → 0.2s (95% improvement)
   - Zero false positives on complex queries
   - Handles 60% of total query volume at scale
   - Zero memory overhead

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Regex-based pattern matching with confidence scoring, executed before any expensive operations.

2. **Key Components / Code Areas**
   - `app/utils/query_classifier.py` - Classification engine
   - `app/tools/orchestration.py` - Integration point
   - `app/responses/templates.py` - Response templates
   - Pattern configuration in YAML

3. **Implementation Steps**
   - Build comprehensive pattern library (500+ patterns)
   - Implement confidence-based classification
   - Create response template system
   - Add bypass logic in jean_memory tool
   - Implement A/B testing framework

4. **Risks & Mitigation**
   - False positives → Multi-pattern confirmation required
   - Pattern maintenance → Monthly review process
   - Language variations → Gradual expansion with metrics

5. **Testing Plan**
   - 1000+ query test suite
   - A/B testing with quality metrics
   - User satisfaction monitoring
   - Load testing with 80% simple queries

---

## **Item 2: Full Context Plan Caching (200MB Allocation)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Implement robust 200MB LRU cache for AI context plans with 30-minute TTL, leveraging our 2GB memory.

2. **Why** – Context planning takes 2-12s and represents 60% of response time. With proper caching, we achieve 70-90% improvement for 60-80% of queries.

3. **Scope**
   
   **In Scope:**
   - 200MB memory allocation (10% of total)
   - Intelligent cache key generation
   - 30-minute TTL with sliding window
   - Cache warming for common patterns
   - Distributed cache preparation
   
   **Out of Scope:**
   - Cross-server cache sharing
   - Persistent cache storage
   - User-specific cache tuning

4. **Acceptance Criteria**
   - Cache size strictly limited to 200MB
   - 60-80% cache hit rate at scale
   - 70-90% latency reduction for hits
   - Automatic eviction under memory pressure
   - Zero impact on memory stability

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – In-memory LRU cache with size tracking, automatic eviction, and memory pressure integration.

2. **Key Components / Code Areas**
   - `app/utils/context_cache.py` - Enhanced cache manager
   - `app/mcp_orchestration.py` - Cache integration
   - `app/middleware/memory_monitor.py` - Pressure detection
   - Cache metrics dashboard

3. **Implementation Steps**
   - Implement size-aware LRU cache
   - Create intelligent key generation
   - Add cache warming on startup
   - Integrate memory monitoring
   - Build cache analytics dashboard

4. **Risks & Mitigation**
   - Memory overflow → Strict size enforcement
   - Stale data → Version-aware cache keys
   - Cache stampede → Request coalescing

5. **Testing Plan**
   - Memory limit testing
   - Cache effectiveness at scale
   - Eviction policy validation
   - Performance under load

---

## **Item 3: Parallel Processing Architecture**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Enable parallel execution of independent operations using asyncio, now viable with 2GB RAM.

2. **Why** – Sequential processing wastes time. Parallel execution provides 40-60% speedup for complex queries without quality loss.

3. **Scope**
   
   **In Scope:**
   - Parallel vector searches (4-6 concurrent)
   - Concurrent database queries
   - Parallel AI analysis tasks
   - Dynamic concurrency adjustment
   - Memory-aware throttling
   
   **Out of Scope:**
   - Multi-process architecture
   - Distributed processing
   - GPU acceleration

4. **Acceptance Criteria**
   - 4-6 parallel operations sustained
   - 40-60% latency reduction
   - No race conditions or deadlocks
   - Automatic throttling at 70% memory
   - Maintains result quality

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – asyncio.gather() with semaphore-based concurrency control and memory monitoring.

2. **Key Components / Code Areas**
   - `app/utils/parallel_executor.py` - Execution framework
   - `app/mcp_orchestration.py` - Strategy parallelization
   - `app/utils/concurrency_manager.py` - Resource management
   - Performance monitoring

3. **Implementation Steps**
   - Identify parallelizable operations
   - Implement execution framework
   - Add concurrency controls
   - Integrate memory throttling
   - Create performance metrics

4. **Risks & Mitigation**
   - Memory spikes → Dynamic concurrency reduction
   - Database overload → Connection pooling
   - Result ordering → Maintain operation sequence

5. **Testing Plan**
   - Concurrent operation testing
   - Memory spike simulation
   - Load testing at scale
   - Race condition detection

---

## **Item 4: Background Narrative Pre-computation (Parallel Enabled)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Generate user narratives in parallel background tasks, leveraging 400MB for processing.

2. **Why** – New conversations wait 15s for narrative generation. Pre-computation reduces this to 1.5s (90% improvement).

3. **Scope**
   
   **In Scope:**
   - 3 parallel narrative generations
   - Priority queue for active users
   - Incremental narrative updates
   - 48-hour coverage window
   - Automatic regeneration triggers
   
   **Out of Scope:**
   - Real-time narrative updates
   - Streaming narrative generation
   - Custom narrative formats

4. **Acceptance Criteria**
   - Narratives ready within 5s of memory save
   - 3 parallel generations sustained
   - 95% coverage of active users
   - Memory usage < 400MB
   - Zero impact on foreground operations

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Priority queue with parallel workers, memory monitoring, and intelligent scheduling.

2. **Key Components / Code Areas**
   - `app/services/narrative_processor.py` - Parallel processor
   - `app/queues/narrative_queue.py` - Priority queue
   - `app/models.py` - Narrative versioning
   - Background worker management

3. **Implementation Steps**
   - Implement parallel worker pool
   - Create priority queue system
   - Add memory-aware scheduling
   - Build regeneration triggers
   - Implement monitoring dashboard

4. **Risks & Mitigation**
   - Queue overflow → Priority-based eviction
   - Memory exhaustion → Worker throttling
   - Stale narratives → TTL-based regeneration

5. **Testing Plan**
   - Parallel generation testing
   - Queue performance at scale
   - Memory usage validation
   - Coverage metrics tracking

---

## **Item 5: Comprehensive Search Result Caching (100MB)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Implement 100MB cache for vector and graph search results with intelligent invalidation.

2. **Why** – Search operations are expensive. Caching provides 25-35% overall improvement with 30-40% hit rate.

3. **Scope**
   
   **In Scope:**
   - 100MB allocation for search cache
   - 10-minute sliding TTL
   - Semantic similarity matching
   - Partial result caching
   - Cache warming strategies
   
   **Out of Scope:**
   - Full result set caching
   - Cross-user cache sharing
   - Persistent cache storage

4. **Acceptance Criteria**
   - Cache size limited to 100MB
   - 30-40% hit rate achieved
   - 25-35% overall improvement
   - Intelligent invalidation working
   - Zero stale results

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – LRU cache with semantic matching, partial results, and smart invalidation.

2. **Key Components / Code Areas**
   - `app/utils/search_cache.py` - Cache implementation
   - `app/tools/memory.py` - Integration points
   - `app/utils/similarity.py` - Semantic matching
   - Cache analytics

3. **Implementation Steps**
   - Build size-aware cache
   - Implement semantic matching
   - Add invalidation logic
   - Create warming strategy
   - Build analytics dashboard

4. **Risks & Mitigation**
   - Stale results → Aggressive invalidation
   - Memory overhead → Partial result storage
   - Cache misses → Semantic similarity fallback

5. **Testing Plan**
   - Cache effectiveness testing
   - Invalidation accuracy
   - Memory limit validation
   - Performance benchmarking

---

## **Item 6: Memory Monitoring & Management**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Real-time memory monitoring with automatic optimization for 50-100 concurrent users.

2. **Why** – With 2GB serving 50-100 users, we need proactive management to prevent degradation and OOM.

3. **Scope**
   
   **In Scope:**
   - Real-time memory tracking
   - Automatic cache clearing
   - Performance metrics dashboard
   - Alert system (60%, 75%, 85%)
   - Predictive analysis
   
   **Out of Scope:**
   - Memory usage prediction
   - Automatic scaling
   - Cross-server coordination

4. **Acceptance Criteria**
   - Real-time monitoring active
   - Alerts trigger correctly
   - Automatic optimization works
   - Zero OOM crashes
   - Dashboard accessible

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – psutil-based monitoring with Prometheus metrics and automated responses.

2. **Key Components / Code Areas**
   - `app/middleware/memory_monitor.py` - Core monitoring
   - `app/utils/memory_optimizer.py` - Optimization logic
   - `app/metrics/prometheus.py` - Metrics export
   - Grafana dashboard

3. **Implementation Steps**
   - Implement monitoring middleware
   - Create optimization strategies
   - Build metrics pipeline
   - Design Grafana dashboard
   - Configure alert rules

4. **Risks & Mitigation**
   - Monitoring overhead → Sampling strategy
   - False positives → Moving averages
   - Alert fatigue → Smart thresholds

5. **Testing Plan**
   - Memory pressure simulation
   - Alert accuracy testing
   - Optimization validation
   - Dashboard usability

---

## **Item 7: Connection Pool Optimization**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Configure optimized connection pooling for databases with 100MB allocation.

2. **Why** – Poor connection management causes timeouts and failures. Proper pooling provides 15-25% improvement and 2x capacity.

3. **Scope**
   
   **In Scope:**
   - SQLAlchemy pool (20 connections)
   - Qdrant connection reuse
   - Neo4j connection management
   - Pool monitoring
   - Circuit breakers
   
   **Out of Scope:**
   - Custom connection pools
   - Database proxies
   - Connection multiplexing

4. **Acceptance Criteria**
   - 20 PostgreSQL connections maintained
   - Zero connection timeouts
   - 15-25% latency improvement
   - Handles 100 concurrent users
   - Monitoring operational

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – SQLAlchemy pooling with monitoring and circuit breakers for all databases.

2. **Key Components / Code Areas**
   - `app/database.py` - Pool configuration
   - `app/utils/connection_manager.py` - Management logic
   - `app/metrics/db_metrics.py` - Monitoring
   - Circuit breaker implementation

3. **Implementation Steps**
   - Configure SQLAlchemy pools
   - Implement connection monitoring
   - Add circuit breakers
   - Create health checks
   - Build monitoring dashboard

4. **Risks & Mitigation**
   - Connection leaks → Automatic cleanup
   - Pool exhaustion → Queue management
   - Database limits → Circuit breakers

5. **Testing Plan**
   - Connection limit testing
   - Failover validation
   - Load testing
   - Monitoring accuracy

---

## Implementation Priority Matrix

### Phase 1: Immediate Wins (Week 1)
- **Item 1**: Smart Query Classification (P0)
- **Item 2**: Context Plan Caching (P0)
- **Item 3**: Parallel Processing (P0)

### Phase 2: Scale Enablers (Week 2)
- **Item 4**: Narrative Pre-computation (P0)
- **Item 5**: Search Result Caching (P1)
- **Item 6**: Memory Monitoring (P1)

### Phase 3: Optimization (Week 3)
- **Item 7**: Connection Pooling (P1)
- Load testing and tuning
- Performance validation

## Success Metrics with 2GB RAM

| Metric | Target | Measurement |
|--------|--------|-------------|
| Simple query bypass | 60% | Query classification rate |
| Cache hit rate | 60-80% | Cache statistics |
| Parallel operations | 4-6 | Concurrency metrics |
| Narrative coverage | 95% | Active user percentage |
| Response time improvement | 70-90% | End-to-end latency |
| Concurrent users | 50-100 | Load testing |
| Memory stability | <85% usage | Monitoring dashboard |
| Zero OOM crashes | 0 | Error logs |

## Risk Management

### Memory Risks at Scale
- **Risk**: 100 users exhausting 2GB
- **Mitigation**: Aggressive caching limits, monitoring
- **Trigger**: Plan Qdrant upgrade at 50 users

### Database Bottlenecks
- **Risk**: Qdrant MICRO limiting performance
- **Current Limit**: ~80K vectors total
- **Mitigation**: Query optimization, result caching
- **Upgrade Path**: SMALL plan at 50+ users

### Connection Exhaustion
- **Risk**: Supabase 60 connection limit
- **Mitigation**: Connection pooling, circuit breakers
- **Monitoring**: Real-time connection tracking

## Capacity Planning

### Current State (2GB RAM)
- Users: 50-100 concurrent
- Cache: 300MB total
- Processing: 400MB parallel operations
- Reserve: 200MB emergency

### Next Upgrade Trigger (100+ users)
- Qdrant: MICRO → SMALL ($40/month)
- Backend: Consider 4GB if needed
- Supabase: Pro plan for dedicated resources

This revised plan fully leverages the 2GB upgrade while preparing for 50-100 concurrent users.