# Performance Evaluations

This directory contains performance evaluations based on the V2 Testing Strategy requirements for Jean Memory's orchestration system.

## Performance Requirements from V2 Strategy

Based on the [V2 Testing Strategy](../../docs/new/JEAN_MEMORY_TESTING_STRATEGY_V2.md), our performance targets are:

| Metric | Path | Target (P95) | Rationale |
|--------|------|--------------|-----------|
| **Fast Path End-to-End Latency** | Fast Path | **< 3 seconds** | Critical user-facing metric |
| **Deep Analysis Latency** | Deep Analysis | **< 60 seconds** | Background processing budget |
| **Timeout Resilience** | Fast Path | **100%** | Must always return something |

## Performance Test Categories

### 1. Fast Path Benchmarks (`fast_path_benchmarks.py`)
Tests the critical user-facing response time:

**Test Scenarios:**
- New conversation initialization
- Continuing conversation context retrieval
- No-context queries (should be fastest)
- Cache hit vs cache miss performance
- Different context strategies (targeted vs comprehensive)

**Measurements:**
- End-to-end response time from tool call to context return
- Time to first byte (TTFB) for immediate responses
- Context quality vs speed tradeoffs
- Memory usage during context generation

### 2. Resilience Tests (`resilience_tests.py`)
Tests graceful degradation when components fail:

**Failure Scenarios:**
- AI planner timeout (> 5 seconds)
- Memory search service unavailable
- Database connection timeout
- Context cache miss under load
- Background task queue overflow

**Resilience Requirements:**
- Fast path must return within 3 seconds even if AI planning fails
- Fallback context must be provided when deep analysis fails
- No exceptions should bubble up to the user
- System should degrade gracefully with informative logs

### 3. Load Testing (`load_testing.py`)
Tests performance under concurrent load:

**Load Scenarios:**
- Multiple simultaneous users (5, 10, 25 concurrent)
- Mixed workload (new + continuing conversations)
- Background task processing under load
- Context cache performance under pressure

**Metrics:**
- P50, P95, P99 latency under load
- Throughput (requests/second)
- Error rate under stress
- Resource utilization (CPU, memory, database connections)

### 4. Memory Performance (`memory_benchmarks.py`)
Tests memory-related performance:

**Memory Operations:**
- Memory search latency by result count
- Memory triage decision speed
- Background memory saving throughput
- Large context generation performance

## Key Performance Tests

### Fast Path Performance Test
```python
async def test_fast_path_latency():
    """Test that fast path always responds within 3 seconds"""
    scenarios = [
        ("New conversation", "Hi, I'm John", True),
        ("Continuing", "Help with Python", False),
        ("No context", "What's 2+2?", False)
    ]
    
    for description, message, is_new in scenarios:
        start_time = time.time()
        context = await jean_memory(message, is_new, needs_context=True)
        response_time = time.time() - start_time
        
        assert response_time < 3.0, f"{description}: {response_time:.2f}s > 3.0s"
        assert context, f"{description}: No context returned"
```

### Resilience Test
```python
async def test_ai_planner_timeout_resilience():
    """Test graceful degradation when AI planner times out"""
    
    # Mock AI planner to timeout
    with patch('app.mcp_orchestration.MCPAIService.create_context_plan') as mock_plan:
        mock_plan.side_effect = asyncio.TimeoutError("AI planning timed out")
        
        start_time = time.time()
        context = await jean_memory("Help me with my project", False, True)
        response_time = time.time() - start_time
        
        # Should still respond within 3 seconds with fallback
        assert response_time < 3.0, f"Timeout resilience failed: {response_time:.2f}s"
        assert context, "No fallback context provided"
        assert "error" not in context.lower(), "Error leaked to user context"
```

### Load Test Example
```python
async def test_concurrent_performance():
    """Test performance under concurrent load"""
    
    async def single_request():
        return await jean_memory("What are my current projects?", False, True)
    
    # Test with 10 concurrent users
    tasks = [single_request() for _ in range(10)]
    
    start_time = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.time()
    
    # Check that all requests completed
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) == 10, f"Only {len(successful)}/10 requests succeeded"
    
    # Check average response time
    avg_time = (end_time - start_time) / 10
    assert avg_time < 3.0, f"Average response time {avg_time:.2f}s > 3.0s under load"
```

## Performance Monitoring

### Continuous Monitoring
The evaluation framework provides continuous performance monitoring:

```python
# Performance metrics collection
performance_metrics = {
    'fast_path_p95_latency': measure_p95_latency(),
    'deep_analysis_completion_rate': measure_completion_rate(),
    'timeout_resilience_rate': measure_resilience_rate(),
    'context_quality_under_load': measure_quality_degradation()
}
```

### Alert Thresholds
Performance alerts are triggered when:
- Fast path P95 latency > 3.5 seconds (17% over target)
- Deep analysis completion rate < 95%
- Timeout resilience rate < 100%
- Context quality drops > 10% under load

## Running Performance Evaluations

### Quick Performance Check
```bash
# Run all performance tests
python -m evals.performance.run_all

# Run only fast path tests
python -m evals.performance.fast_path_benchmarks

# Test resilience
python -m evals.performance.resilience_tests --simulate-failures
```

### Load Testing
```bash
# Light load test
python -m evals.performance.load_testing --concurrent-users 5 --duration 60

# Heavy load test
python -m evals.performance.load_testing --concurrent-users 25 --duration 300

# Stress test until failure
python -m evals.performance.load_testing --stress-test --max-users 100
```

### Performance Profiling
```bash
# Profile specific operations
python -m evals.performance.fast_path_benchmarks --profile --output profile.stats

# Memory profiling
python -m evals.performance.memory_benchmarks --memory-profile
```

## Integration with CI/CD

Performance tests are integrated into the CI/CD pipeline:

### PR Checks (Fast)
- Fast path benchmark (< 30 seconds to run)
- Basic resilience test
- Performance regression detection

### Daily Performance Runs (Comprehensive)
- Full load testing suite
- Long-running resilience tests
- Performance trend analysis
- Alerting on degradation

### Performance Regression Detection
```python
def detect_performance_regression(current_metrics, baseline_metrics):
    """Detect if performance has regressed significantly"""
    
    for metric, current_value in current_metrics.items():
        baseline_value = baseline_metrics.get(metric)
        if baseline_value:
            regression_pct = (current_value - baseline_value) / baseline_value * 100
            
            if regression_pct > 15:  # 15% regression threshold
                raise PerformanceRegressionError(
                    f"{metric} regressed by {regression_pct:.1f}%: "
                    f"{baseline_value:.2f} -> {current_value:.2f}"
                )
```

## Expected Performance Improvements

### Phase 1: Meet Basic Requirements
- ✅ Fast path < 3 seconds (P95)
- ✅ 100% timeout resilience
- ✅ Background deep analysis < 60 seconds

### Phase 2: Optimize for Scale
- Fast path < 2 seconds (P95)
- Support 50+ concurrent users
- Context cache hit rate > 80%

### Phase 3: Advanced Performance
- Fast path < 1 second (P95)
- Predictive context pre-loading
- Adaptive performance tuning based on usage patterns

## Troubleshooting Performance Issues

### Common Performance Bottlenecks
1. **AI Planning Latency**: Gemini API calls taking > 2 seconds
2. **Memory Search**: Database queries scaling poorly with memory count
3. **Context Cache Misses**: Cache invalidation too aggressive
4. **Background Task Queue**: Memory saving tasks backing up

### Performance Debugging Tools
```bash
# Profile slow requests
python -m evals.performance.debug_slow_requests --threshold 5.0

# Analyze bottlenecks
python -m evals.performance.bottleneck_analysis --component all

# Database query analysis
python -m evals.performance.db_performance --analyze-queries
```

The goal is to ensure Jean Memory provides consistently fast, reliable performance that meets the V2 strategy requirements while gracefully handling failures and scaling with user growth.