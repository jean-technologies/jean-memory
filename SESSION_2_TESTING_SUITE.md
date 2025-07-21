# Session 2: Enhanced Testing & Validation Suite

## Session Overview

**Branch:** `session-2-testing-suite`
**Duration:** 3-4 days
**Priority:** High - Critical for production readiness
**Dependencies:** None (parallel to Session 1)

## Objective

Create comprehensive testing infrastructure for Jean Memory V3 with automated validation, performance benchmarks, and production-ready monitoring to ensure reliability across all components.

## Implementation Plan

### Step 2.1: Test Infrastructure Setup (Day 1)
**Commit checkpoint:** `session-2-step-1-test-infrastructure`

#### Tasks:
1. **Create testing directory structure:**
   ```
   tests/
   ├── unit/
   │   ├── test_stm_service.py
   │   ├── test_ltm_service.py
   │   ├── test_memory_shuttle.py
   │   └── test_adk_services.py
   ├── integration/
   │   ├── test_memory_flow.py
   │   ├── test_api_endpoints.py
   │   └── test_v2_integration.py
   ├── performance/
   │   ├── test_benchmarks.py
   │   ├── test_load.py
   │   └── test_memory_limits.py
   ├── fixtures/
   │   ├── sample_data.py
   │   └── test_configs.py
   └── conftest.py
   ```

2. **Configure pytest with async support:**
   ```python
   # Add to requirements.txt
   pytest-asyncio>=0.25.0
   pytest-benchmark>=4.0.0
   pytest-mock>=3.12.0
   pytest-cov>=4.0.0
   locust>=2.20.0
   
   # Create pytest.ini
   [tool:pytest]
   asyncio_mode = auto
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   markers =
       unit: Unit tests
       integration: Integration tests
       performance: Performance tests
       slow: Slow running tests
   ```

3. **Create test configuration and fixtures:**
   ```python
   # tests/conftest.py
   @pytest.fixture
   async def memory_service():
       service = JeanMemoryV3Service()
       await service.initialize()
       yield service
       await service.cleanup()
   
   @pytest.fixture
   def sample_memories():
       return [
           {"content": "Test memory 1", "user_id": "test_user"},
           {"content": "Test memory 2", "user_id": "test_user"},
       ]
   ```

#### Testing Protocol:
```bash
# Test basic pytest setup
python -m pytest --version
python -m pytest tests/ --collect-only

# Test async fixtures
python -m pytest tests/conftest.py -v
```

### Step 2.2: Unit Tests Implementation (Day 2)
**Commit checkpoint:** `session-2-step-2-unit-tests`

#### Tasks:
1. **STM Service Unit Tests:**
   ```python
   # tests/unit/test_stm_service.py
   class TestSTMService:
       async def test_memory_creation(self, memory_service):
           # Test memory creation and storage
           
       async def test_memory_search(self, memory_service):
           # Test search functionality
           
       async def test_salience_calculation(self):
           # Test memory prioritization
           
       async def test_resource_limits(self):
           # Test memory limits and eviction
   ```

2. **LTM Service Unit Tests:**
   ```python
   # tests/unit/test_ltm_service.py
   class TestLTMService:
       async def test_v2_api_integration(self):
           # Test V2 API calls with mocking
           
       async def test_error_handling(self):
           # Test connection failures and retries
           
       async def test_rate_limiting(self):
           # Test rate limit handling
   ```

3. **Memory Shuttle Unit Tests:**
   ```python
   # tests/unit/test_memory_shuttle.py
   class TestMemoryShuttle:
       async def test_background_sync(self):
           # Test STM → LTM synchronization
           
       async def test_batch_processing(self):
           # Test batch upload efficiency
           
       async def test_deduplication(self):
           # Test duplicate memory detection
   ```

4. **ADK Services Unit Tests:**
   ```python
   # tests/unit/test_adk_services.py
   class TestADKServices:
       async def test_session_management(self):
           # Test session creation and state
           
       async def test_memory_service_routing(self):
           # Test hybrid memory routing
   ```

#### Testing Protocol:
```bash
# Run unit tests
python -m pytest tests/unit/ -v

# Test with coverage
python -m pytest tests/unit/ --cov=services --cov=adk

# Test specific components
python -m pytest tests/unit/test_stm_service.py -v
```

### Step 2.3: Integration Tests Implementation (Day 3)
**Commit checkpoint:** `session-2-step-3-integration-tests`

#### Tasks:
1. **End-to-End Memory Flow Tests:**
   ```python
   # tests/integration/test_memory_flow.py
   class TestMemoryFlow:
       async def test_complete_memory_lifecycle(self):
           # Create → Search → Update → Delete flow
           
       async def test_stm_to_ltm_sync(self):
           # Test complete sync workflow
           
       async def test_cross_service_integration(self):
           # Test STM + Graph + Shuttle integration
   ```

2. **API Endpoint Integration Tests:**
   ```python
   # tests/integration/test_api_endpoints.py
   class TestAPIEndpoints:
       def test_health_endpoint(self, client):
           # Test health check
           
       async def test_memory_crud_operations(self, client):
           # Test full CRUD via API
           
       async def test_search_endpoints(self, client):
           # Test search functionality
           
       async def test_session_endpoints(self, client):
           # Test session management
   ```

3. **V2 Production Integration Tests:**
   ```python
   # tests/integration/test_v2_integration.py
   class TestV2Integration:
       async def test_v2_api_connectivity(self):
           # Test connection to production V2
           
       async def test_data_format_compatibility(self):
           # Test V2 ↔ V3 data format conversion
           
       async def test_fallback_behavior(self):
           # Test fallback when V2 unavailable
   ```

#### Testing Protocol:
```bash
# Run integration tests
python -m pytest tests/integration/ -v

# Test with real services (requires setup)
JEAN_MEMORY_V2_API_KEY=test_key python -m pytest tests/integration/test_v2_integration.py

# Test API endpoints
python -m pytest tests/integration/test_api_endpoints.py -v
```

### Step 2.4: Performance & Load Testing (Day 4)
**Commit checkpoint:** `session-2-step-4-performance-tests`

#### Tasks:
1. **Performance Benchmark Tests:**
   ```python
   # tests/performance/test_benchmarks.py
   class TestPerformanceBenchmarks:
       @pytest.mark.benchmark(group="memory_creation")
       def test_stm_memory_creation_speed(self, benchmark):
           # Benchmark memory creation performance
           
       @pytest.mark.benchmark(group="search")
       def test_search_performance(self, benchmark):
           # Benchmark search performance
           
       async def test_concurrent_operations(self):
           # Test concurrent memory operations
   ```

2. **Load Testing with Locust:**
   ```python
   # tests/performance/locustfile.py
   class MemoryUser(HttpUser):
       wait_time = between(1, 3)
       
       def on_start(self):
           # Setup test user
           
       @task(3)
       def create_memory(self):
           # Load test memory creation
           
       @task(2)
       def search_memories(self):
           # Load test search
   ```

3. **Memory Limit and Stress Tests:**
   ```python
   # tests/performance/test_memory_limits.py
   class TestMemoryLimits:
       async def test_max_memories_limit(self):
           # Test STM memory limit enforcement
           
       async def test_memory_eviction_lru(self):
           # Test LRU eviction behavior
           
       async def test_resource_cleanup(self):
           # Test proper resource cleanup
   ```

4. **Performance Monitoring Setup:**
   ```python
   # tests/performance/performance_monitor.py
   class PerformanceMonitor:
       def collect_metrics(self):
           # Collect performance metrics
           
       def generate_report(self):
           # Generate performance report
   ```

#### Testing Protocol:
```bash
# Run performance benchmarks
python -m pytest tests/performance/test_benchmarks.py --benchmark-only

# Run load tests
locust -f tests/performance/locustfile.py --host=http://localhost:8766

# Memory stress test
python -m pytest tests/performance/test_memory_limits.py -v -s
```

## Automated Testing Workflows

### GitHub Actions CI/CD:
```yaml
# .github/workflows/test.yml
name: Jean Memory V3 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: python -m pytest tests/unit/ --cov=services
    
    - name: Run integration tests
      run: python -m pytest tests/integration/
    
    - name: Run performance benchmarks
      run: python -m pytest tests/performance/ --benchmark-only
```

### Local Testing Scripts:
```bash
# scripts/run_tests.sh
#!/bin/bash

echo "🧪 Running Jean Memory V3 Test Suite..."

# Unit tests
echo "📝 Unit Tests..."
python -m pytest tests/unit/ -v --cov=services --cov=adk

# Integration tests
echo "🔗 Integration Tests..."
python -m pytest tests/integration/ -v

# Performance tests
echo "⚡ Performance Tests..."
python -m pytest tests/performance/test_benchmarks.py --benchmark-only

echo "✅ All tests completed!"
```

## Manual Testing Checklist

After each commit checkpoint:

### Unit Test Validation:
- [ ] All unit tests pass (> 95% pass rate)
- [ ] Code coverage > 80% for core services
- [ ] No failing assertions
- [ ] Performance benchmarks within targets

### Integration Test Validation:
- [ ] End-to-end memory flow works
- [ ] API endpoints respond correctly
- [ ] V2 integration maintains compatibility
- [ ] Session management functions properly

### Performance Test Validation:
- [ ] Memory creation < 10ms average
- [ ] Search performance < 50ms for cached items
- [ ] Concurrent operations handle load
- [ ] Memory limits enforced correctly

### Load Test Validation:
- [ ] Service handles 100+ concurrent users
- [ ] No memory leaks under load
- [ ] Graceful degradation under stress
- [ ] Error rates < 1% under normal load

## Debug Logging Strategy

### Test-Specific Logging:
```python
# Add to test configuration
import logging

# Configure test logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test_debug.log"),
        logging.StreamHandler()
    ]
)

# Test-specific logger
test_logger = logging.getLogger("jean_memory_v3_tests")
```

### Debug Commands:
```bash
# Run tests with detailed logging
python -m pytest tests/ -v -s --log-cli-level=DEBUG

# Analyze test performance
python -c "
from tests.performance.performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
report = monitor.generate_report()
print(report)
"

# Check test coverage gaps
python -m pytest tests/ --cov=services --cov-report=html
open htmlcov/index.html
```

## Integration Handoff

### For Session 5 (Final Integration):

1. **Completed test infrastructure:**
   - Comprehensive unit test suite (80+ tests)
   - Integration test coverage for all flows
   - Performance benchmarking framework
   - Load testing capabilities

2. **Testing artifacts:**
   - Test coverage reports
   - Performance benchmark results
   - Load testing results
   - CI/CD pipeline configuration

3. **Integration points:**
   - Automated testing in CI/CD
   - Performance regression detection
   - Production monitoring setup
   - Error tracking and alerting

4. **Documentation:**
   - Testing best practices
   - Performance targets and SLAs
   - Debugging runbooks
   - Test maintenance procedures

## Quality Gates

### Code Quality Requirements:
- [ ] Test coverage > 80%
- [ ] All unit tests pass
- [ ] Integration tests validate key flows
- [ ] Performance benchmarks meet targets
- [ ] Load tests demonstrate scalability
- [ ] No critical bugs in test suite

### Performance Targets:
- [ ] Memory creation: < 10ms average
- [ ] Search operations: < 50ms average
- [ ] Concurrent users: 100+ supported
- [ ] Memory usage: < 512MB for STM
- [ ] Error rate: < 1% under load

## Success Criteria

- [ ] Comprehensive test suite covers all V3 components
- [ ] Automated testing pipeline functional
- [ ] Performance benchmarks establish baselines
- [ ] Load testing validates scalability
- [ ] Integration tests ensure component compatibility
- [ ] Debug capabilities enable rapid issue resolution
- [ ] Quality gates enforce production readiness
- [ ] Ready for Session 5 integration

**Next:** Session 3 (Performance) depends on this session's benchmarks
**Parallel:** Session 1 (Google ADK) can run simultaneously