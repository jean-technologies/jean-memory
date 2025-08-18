# Jean Memory Optimization Mini-FRDs and Mini-EDDs (Infrastructure Constrained)

## 🚨 CRITICAL: Infrastructure-Constrained Revision

This document has been **completely revised** based on infrastructure analysis revealing severe memory constraints. The 512MB backend memory fundamentally changes optimization viability.

**Infrastructure Reality:**
- Backend: 512MB RAM (350MB usable after overhead)
- Qdrant: 1GB MICRO plan
- Neo4j: Free tier (10 connections, 30s timeout)
- Supabase: Free tier (60 connections, shared resources)

**Revised Priority Items:**
1. **Memory Monitoring & Guards** - CRITICAL for current constraints
2. **Smart Query Classification** - Zero memory, immediate 80%+ gains
3. **AI Context Plan Caching** - REVISED: 10MB limit, not unlimited
4. **Narrative Pre-computation** - REVISED: Sequential only, not parallel
5. **Memory Search Result Caching** - REVISED: 5MB/2-minute TTL
6. **Infrastructure Upgrade Justification** - Backend RAM upgrade analysis

## **Item 1: Memory Monitoring & Guards (NEW - CRITICAL)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Implement memory pressure detection and circuit breakers to prevent crashes and gracefully degrade under the 512MB memory constraint.

2. **Why** – Current 512MB backend memory (350MB usable) has zero margin for error. Memory monitoring prevents OOM crashes and enables graceful degradation, which is CRITICAL for system stability.

3. **Scope** 
   
   **In Scope:**
   - Real-time memory usage monitoring
   - Circuit breakers at 85% memory usage
   - Emergency mode (basic operations only) at 90%
   - Background task throttling based on memory pressure
   - Immediate garbage collection triggers
   
   **Out of Scope:**
   - Memory usage prediction
   - Dynamic memory allocation
   - Request queuing beyond basic rejection

4. **Acceptance Criteria**
   - Memory alerts trigger at 60%, 75%, 85% thresholds
   - Complex queries rejected at 85% memory usage
   - Emergency mode activates at 90% usage
   - Zero OOM crashes in production
   - System recovers automatically when memory pressure reduces

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Implement psutil-based memory monitoring with circuit breaker patterns in middleware, using tiered response based on memory pressure levels.

2. **Key Components / Code Areas**
   - `app/middleware/memory_monitor.py` - Memory monitoring middleware
   - `app/utils/circuit_breaker.py` - Circuit breaker implementation
   - `app/mcp_orchestration.py` - Memory-aware request handling
   - Memory pressure integration in tool execution

3. **Implementation Steps**
   - Add memory monitoring middleware to FastAPI
   - Implement circuit breaker for memory thresholds
   - Add memory pressure checks before expensive operations
   - Create emergency mode with basic responses only
   - Add memory usage logging and alerts

4. **Risks & Mitigation**
   - Memory calculation overhead → Lightweight psutil calls
   - False positives from memory spikes → Moving average calculation
   - Emergency mode too restrictive → Gradual degradation levels

5. **Testing Plan**
   - Memory stress testing with artificial load
   - Verify circuit breaker triggers at correct thresholds
   - Test emergency mode functionality
   - Monitor memory recovery patterns

## **Item 2: Smart Query Classification (REVISED - #1 PRIORITY)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Pattern-match greetings and simple queries to completely bypass AI planning and database calls, providing immediate responses.

2. **Why** – **REVISED PRIORITY**: This becomes our #1 optimization since it requires zero memory and provides immediate 80%+ speedup for 25-40% of queries. Critical for current constraints.

3. **Scope** 
   
   **In Scope:**
   - Pattern matching for greetings, farewells, simple questions
   - Message length and complexity heuristics
   - Complete bypass of AI planning and database calls
   - Instant response generation
   
   **Out of Scope:**
   - ML-based classification
   - User-specific pattern learning
   - Complex linguistic analysis

4. **Acceptance Criteria**
   - Correctly identifies 90%+ of simple greetings/farewells
   - Response time for simple queries: 2-12s → 0.2s (95% improvement)
   - Zero memory overhead
   - No false positives that skip needed context
   - Works across different languages/styles

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Implement regex-based pattern matching with predefined response templates, completely bypassing the AI planning and database layers for identified simple queries.

2. **Key Components / Code Areas**
   - `app/tools/orchestration.py` - Query classification logic
   - `app/utils/query_classifier.py` - Pattern matching implementation
   - `app/responses/simple_responses.py` - Template responses
   - Pattern configuration in settings

3. **Implementation Steps**
   - Create comprehensive pattern library for simple queries
   - Implement fast classification check before AI planning
   - Add template response system for classified queries
   - Configure bypass logic in jean_memory tool
   - Add classification accuracy monitoring

4. **Risks & Mitigation**
   - False positives skip needed context → Conservative patterns, manual review
   - Pattern maintenance overhead → Centralized configuration
   - Cultural/language variations → Gradual expansion with feedback

5. **Testing Plan**
   - Test suite with 1000+ simple/complex query examples
   - A/B testing to verify no quality degradation
   - Performance benchmarking for classified queries
   - User feedback monitoring for missed context

## **Item 3: AI Context Plan Caching (REVISED - Memory Constrained)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – **REVISED**: Cache AI-generated context plans with aggressive 10MB size limit and 5-minute TTL due to memory constraints.

2. **Why** – **INFRASTRUCTURE REALITY**: Original unlimited cache not viable with 512MB total memory. Revised 10MB cache still provides 40-60% hit rate vs optimal 80%, but prevents OOM crashes.

3. **Scope** 
   
   **In Scope:**
   - **REVISED**: 10MB LRU cache maximum
   - **REVISED**: 5-minute TTL (not 30-minute)
   - Aggressive eviction policies
   - Memory pressure integration
   - Cache metrics and monitoring
   
   **Out of Scope:**
   - Unlimited cache size
   - Persistent cache across server restarts
   - Cache warming strategies

4. **Acceptance Criteria**
   - Cache never exceeds 10MB memory usage
   - Cache hit rate achieves 30%+ (reduced from 40% due to constraints)
   - Response time for cached queries reduces by 50%+ (reduced from 70%)
   - Automatic cache clearing at 85% system memory
   - Zero OOM crashes from cache usage

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Implement memory-bounded LRU cache with TTL using cachetools library, integrated with memory monitoring to ensure strict 10MB limit enforcement.

2. **Key Components / Code Areas**
   - `app/mcp_orchestration.py` - SmartContextOrchestrator._ai_create_context_plan()
   - `app/utils/bounded_cache.py` - Memory-bounded cache implementation
   - Memory monitoring integration for auto-clearing
   - Cache key generation and collision prevention

3. **Implementation Steps**
   - Implement bounded LRU cache with size tracking
   - Add cache integration to context planning flow
   - Implement memory pressure auto-clearing
   - Add cache metrics and monitoring
   - Configure aggressive eviction policies

4. **Risks & Mitigation**
   - Memory limit enforcement failure → Size tracking on every operation
   - Cache key collisions → Include user context and timestamp
   - Performance degradation from size checking → Efficient tracking methods

5. **Testing Plan**
   - Memory usage testing under various loads
   - Cache eviction testing at memory limits
   - Performance benchmarking with/without cache
   - Memory pressure integration testing

## **Item 4: Narrative Pre-computation (REVISED - Sequential Only)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – **REVISED**: Generate user narratives sequentially (not parallel) in background after memory saves, with memory monitoring to prevent OOM.

2. **Why** – **INFRASTRUCTURE REALITY**: Original parallel processing requires 200-300MB per operation, not viable with 512MB total. Sequential processing still achieves 90% improvement for covered users.

3. **Scope**
   
   **In Scope:**
   - **REVISED**: Queue-based sequential processing (max 1 concurrent)
   - Only for users active in last 24 hours
   - Memory threshold monitoring (pause at 70% usage)
   - Background narrative generation after memory updates
   
   **Out of Scope:**
   - Parallel narrative generation
   - Real-time narrative streaming
   - Narratives for all users

4. **Acceptance Criteria**
   - Narratives generate within 10 seconds of memory save (revised from 5s)
   - New conversation response time < 2 seconds for covered users
   - Background generation pauses at 70% memory usage
   - Zero impact on foreground operations
   - Covers 90%+ of active users (last 24h)

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Implement queue-based sequential narrative generation using FastAPI BackgroundTasks with memory monitoring integration to ensure safe operation within 512MB constraints.

2. **Key Components / Code Areas**
   - `app/services/background_processor.py` - Queue-based narrative service
   - `app/models.py` - UserNarrative model with activity tracking
   - `app/tools/orchestration.py` - Memory-aware trigger logic
   - Memory monitoring integration for queue throttling

3. **Implementation Steps**
   - Implement memory-aware background task queue
   - Add narrative generation trigger after memory saves
   - Create active user tracking (last 24h activity)
   - Implement queue throttling based on memory pressure
   - Add narrative staleness detection and regeneration

4. **Risks & Mitigation**
   - Queue backup during high activity → Priority based on user activity
   - Memory spikes during generation → Memory checks before each task
   - Stale narratives from queue delays → TTL-based regeneration triggers

5. **Testing Plan**
   - Queue performance testing under memory pressure
   - Verify narrative freshness with rapid memory updates
   - Test queue throttling and recovery
   - Monitor active user coverage and generation delays



## **Item 5: Memory Search Result Caching (REVISED - Minimal Memory)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – **REVISED**: Cache frequently accessed memory search results with maximum 5MB memory and 2-minute TTL due to memory constraints.

2. **Why** – **INFRASTRUCTURE REALITY**: Original 10-minute cache with unlimited size not viable. Revised 5MB/2-minute cache still provides 15-25% improvement for repeated searches.

3. **Scope**
   
   **In Scope:**
   - **REVISED**: Maximum 5MB total cache size
   - **REVISED**: 2-minute TTL (not 10-minute)
   - Top search results only (not full results)
   - Automatic cache clearing under memory pressure
   
   **Out of Scope:**
   - Large result caching
   - Long TTL caching
   - Distributed cache across instances

4. **Acceptance Criteria**
   - Cache never exceeds 5MB memory usage
   - Cache provides 15%+ improvement for repeated searches
   - Automatic cache clearing at 80% system memory
   - Zero impact on system stability
   - Easy cache bypass for debugging

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Implement ultra-lightweight search result cache using memory-mapped storage with strict 5MB limit and aggressive 2-minute TTL to work within memory constraints.

2. **Key Components / Code Areas**
   - `app/utils/micro_cache.py` - Minimal memory search cache
   - `app/tools/memory.py` - Cache integration in search flow
   - Memory monitoring integration for auto-clearing
   - Cache key optimization for minimal overhead

3. **Implementation Steps**
   - Implement micro-cache with strict size enforcement
   - Add cache integration to Qdrant search operations
   - Implement aggressive TTL and size-based eviction
   - Add memory pressure auto-clearing
   - Configure cache metrics for monitoring

4. **Risks & Mitigation**
   - Memory limit violations → Strict size tracking on every operation
   - Cache overhead impact → Minimal metadata storage only
   - Short TTL reducing effectiveness → Focus on immediate repeated queries

5. **Testing Plan**
   - Memory usage testing with various search patterns
   - Cache effectiveness measurement with 2-minute TTL
   - Memory pressure integration testing
   - Performance impact assessment

---

## **Item 6: Infrastructure Upgrade Justification (NEW)**

### **Part 1 — Mini-FRD (What & Why)**

1. **What** – Document the critical need for backend RAM upgrade from 512MB to 2GB to unlock meaningful optimization potential.

2. **Why** – Analysis shows 512MB memory prevents 80% of planned optimizations. $19/month upgrade enables full performance improvements and prevents frequent OOM crashes.

3. **Scope**
   
   **In Scope:**
   - Cost-benefit analysis of infrastructure upgrades
   - Performance impact quantification
   - User capacity improvements
   - Risk analysis of current constraints
   
   **Out of Scope:**
   - Other infrastructure providers
   - Microservices architecture
   - Database provider changes

4. **Acceptance Criteria**
   - Clear ROI calculation for each upgrade
   - Performance improvement estimates
   - User capacity projections
   - Risk mitigation for current infrastructure
   - Implementation timeline recommendations

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Comprehensive cost-benefit analysis with quantified performance impacts and risk assessment to justify critical infrastructure investments.

2. **Key Components / Code Areas**
   - Infrastructure cost analysis spreadsheet
   - Performance benchmarking data
   - User capacity modeling
   - Risk assessment framework

3. **Implementation Steps**
   - Gather current performance baseline metrics
   - Model performance improvements with upgraded infrastructure
   - Calculate cost-benefit ratios for each upgrade option
   - Document risk factors of maintaining current constraints
   - Create implementation timeline with priorities

4. **Risks & Mitigation**
   - Overestimating performance gains → Conservative estimates with ranges
   - Underestimating implementation complexity → Include migration costs
   - Budget approval delays → Provide multiple upgrade options

5. **Testing Plan**
   - Performance modeling validation
   - Cost calculation verification
   - Risk assessment accuracy
   - Timeline feasibility review




## **REMOVED ITEMS** (Not Feasible with Current Constraints)

### ❌ Context Strategy Optimization (Parallel Processing)
**Reason**: Requires 200-300MB memory per parallel operation. Not feasible with 512MB total memory.

**Would require**: Backend RAM upgrade to 2GB minimum

### ❌ Infrastructure Optimization (Connection Pooling)
**Reason**: Connection pools require significant memory overhead (50-100MB). Current infrastructure at capacity.

**Would require**: Memory monitoring and backend upgrade first

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Implement asyncio.gather() for parallel tool execution and optimize strategy implementations to eliminate redundant operations. Use connection pooling for database operations.

2. **Key Components / Code Areas**
   - `app/mcp_orchestration.py` - Strategy execution logic
   - `app/utils/mcp_modules/ai_service.py` - Parallel execution
   - Database connection pooling configuration

3. **Implementation Steps**
   - Analyze strategy execution patterns
   - Identify parallelizable operations
   - Implement parallel execution with asyncio
   - Optimize database query patterns
   - Add execution time monitoring
   - Tune timeout configurations

4. **Risks & Mitigation**
   - Race conditions in parallel execution → Proper async/await patterns
   - Database connection exhaustion → Connection pool limits
   - Increased CPU usage → Resource monitoring, throttling

5. **Testing Plan**
   - Unit tests for parallel execution
   - Load tests with complex queries
   - Quality comparison before/after optimization
   - Resource usage monitoring

---

## **Infrastructure Upgrade Analysis**

### Critical Upgrade: Backend RAM (512MB → 2GB)
**Cost**: $19/month  
**Impact**: Unlocks 80% of optimization potential  
**Break-even**: Immediate  
**Justification**:
- Enables context plan caching (70-90% improvement)
- Allows narrative pre-computation (90% improvement)
- Prevents OOM crashes under load
- Supports 50+ concurrent users vs current 10-15

### Memory Budget Post-Upgrade (2GB):
```
Total RAM: 2048 MB
├── Python Process Overhead: 200 MB
├── FastAPI + Dependencies: 300 MB  
├── Context Plan Cache: 100 MB
├── Search Result Cache: 50 MB
├── Background Task Buffer: 200 MB
├── Emergency Reserve: 200 MB
└── Available Operations: 998 MB ✓
```

### Secondary Upgrades (Future Consideration):
- **Qdrant SMALL**: +$40/month (4x capacity)
- **Supabase Pro**: +$25/month (dedicated resources)
- **Neo4j Professional**: +$65/month (graph algorithms)

### **Part 2 — Mini-EDD (How)**

1. **Chosen Approach** – Configure SQLAlchemy connection pooling, optimize async patterns in FastAPI, tune Uvicorn workers, and implement Prometheus metrics with Grafana dashboards.

2. **Key Components / Code Areas**
   - `app/database.py` - Connection pool configuration
   - `main.py` - Uvicorn worker configuration
   - `app/middleware/memory_monitor.py` - Resource monitoring
   - Deployment configuration files

3. **Implementation Steps**
   - Configure SQLAlchemy connection pool
   - Optimize async database operations
   - Tune Uvicorn worker count and type
   - Implement Prometheus metrics export
   - Set up Grafana dashboards
   - Configure resource alerts

4. **Risks & Mitigation**
   - Connection pool exhaustion → Monitoring, dynamic sizing
   - Memory leaks from poor async → Profiling, testing
   - Over-provisioning workers → Start conservative, scale up

5. **Testing Plan**
   - Load test with increasing concurrent users
   - Monitor connection pool usage
   - Profile memory usage over time
   - Verify monitoring and alerting

---

## Revised Implementation Priority (Infrastructure Constrained)

### 🚨 BLOCKING: Infrastructure Upgrade
- **Backend RAM Upgrade**: 512MB → 2GB ($19/month) - CRITICAL

### Phase 1: Memory-Efficient Quick Wins (Week 1)
- **Item 1**: Memory Monitoring & Guards - Prevent crashes
- **Item 2**: Smart Query Classification - Zero memory, immediate impact

### Phase 2: Minimal Memory Optimizations (Week 2 - After RAM upgrade)
- **Item 3**: AI Context Plan Caching (10MB limit)
- **Item 4**: Narrative Pre-computation (sequential)

### Phase 3: Constrained Improvements (Week 3)
- **Item 5**: Memory Search Caching (5MB limit)
- **Item 6**: Infrastructure monitoring

## Revised Success Metrics (Infrastructure Constrained)

### With Current Infrastructure (512MB):
| Item | Primary Metric | Target | Measurement Method |
|------|---------------|--------|-------------------|
| 1 | OOM crash rate | 0% | System monitoring |
| 2 | Simple query latency | -80% | Performance monitoring |
| 3 | Cache hit rate | 30% | Log analysis |
| 4 | Narrative coverage | 90% active users | Coverage tracking |
| 5 | Search cache hit rate | 15% | Cache statistics |

### With Backend RAM Upgrade (2GB):
| Item | Primary Metric | Target | Measurement Method |
|------|---------------|--------|-------------------|
| 1-5 | Overall improvement | 70-80% | End-to-end timing |
| System | Concurrent users | 50+ | Load testing |
| System | Cache efficiency | 50-70% | Combined cache metrics |

## Risk Matrix

| Risk | Likelihood | Impact | Mitigation Strategy |
|------|-----------|--------|-------------------|
| Cache invalidation bugs | Medium | High | Comprehensive testing, monitoring |
| Memory leaks | Low | High | Profiling, resource limits |
| Quality regression | Low | High | Evaluation framework, A/B testing |
| Deployment failures | Low | Medium | Rollback plan, feature flags |
| Performance regression | Low | Medium | Benchmarking, gradual rollout |