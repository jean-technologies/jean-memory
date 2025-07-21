# Session 1: Google ADK Integration Core

## Session Overview

**Branch:** `session-1-google-adk-core`
**Duration:** 3-4 days
**Priority:** High - Critical for V3 Hybrid architecture
**Dependencies:** None (builds on Phase 1.1 foundation)

## Objective

Integrate Google ADK (Agent Development Kit) as the primary interface while preserving Jean Memory V2 competitive advantages through intelligent hybrid routing.

## Implementation Plan

### Step 1.1: Google ADK Dependencies Setup (Day 1)
**Commit checkpoint:** `session-1-step-1-dependencies`

#### Tasks:
1. **Add Google ADK SDK dependencies:**
   ```bash
   # Add to requirements.txt
   google-ai-generativelanguage>=0.5.0
   google-cloud-aiplatform>=1.40.0
   google-auth>=2.20.0
   ```

2. **Configure Google Cloud authentication:**
   - Add Google Cloud project configuration to `config.py`
   - Add service account key handling
   - Add Vertex AI Memory Bank configuration

3. **Environment variables:**
   ```env
   # Add to .env.example
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   GOOGLE_ADK_MEMORY_BANK_ID=your-memory-bank-id
   VERTEX_AI_LOCATION=us-central1
   ```

#### Testing Protocol:
```bash
# Test imports
python -c "
from google.ai import generativelanguage as glm
from google.cloud import aiplatform
print('✅ Google ADK imports successful')
"

# Test authentication (will need service account)
python -c "
import os
from google.auth import default
try:
    credentials, project = default()
    print(f'✅ Google Cloud auth successful: {project}')
except Exception as e:
    print(f'⚠️  Auth setup needed: {e}')
"
```

### Step 1.2: Google Memory Service Implementation (Day 2)
**Commit checkpoint:** `session-1-step-2-memory-service`

#### Tasks:
1. **Create `services/google_memory_service.py`:**
   ```python
   class GoogleADKMemoryService:
       """Google ADK Memory Service integration"""
       
       def __init__(self):
           # Initialize Vertex AI Memory Bank client
           # Configure memory bank parameters
           
       async def add_memory_to_google_adk(self, content, user_id, metadata):
           # Add memory to Google Memory Bank
           # Return Google ADK memory ID
           
       async def search_google_memories(self, query, user_id, limit=10):
           # Search Google Memory Bank
           # Return standardized results
   ```

2. **Implement memory format converters:**
   - Jean Memory V2 format ↔ Google ADK format
   - Metadata mapping and preservation
   - User ID prefix management for isolation

3. **Add to hybrid memory service routing:**
   - Integrate Google ADK as Tier 1 (fastest)
   - Update `adk/memory_service.py` routing logic

#### Testing Protocol:
```bash
# Test Google memory service
python -c "
from services.google_memory_service import GoogleADKMemoryService
import asyncio

async def test():
    service = GoogleADKMemoryService()
    await service.initialize()
    print('✅ Google ADK Memory Service initialized')
    
asyncio.run(test())
"

# Test memory format conversion
python -c "
from services.google_memory_service import GoogleADKMemoryService
service = GoogleADKMemoryService()
result = service.convert_to_google_format({
    'content': 'Test memory',
    'user_id': 'test_user',
    'metadata': {'source': 'test'}
})
print(f'✅ Format conversion: {result}')
"
```

### Step 1.3: Hybrid Memory Orchestrator (Day 3)
**Commit checkpoint:** `session-1-step-3-hybrid-orchestrator`

#### Tasks:
1. **Implement three-tier memory routing:**
   ```
   Tier 1: Google ADK InMemory (2-5ms)
   Tier 2: Jean V3 STM FAISS (5-15ms) 
   Tier 3: Jean V2 Production (100-250ms)
   ```

2. **Create `services/hybrid_orchestrator.py`:**
   ```python
   class HybridMemoryOrchestrator:
       """Routes memory operations across three tiers intelligently"""
       
       async def add_memory_hybrid(self, content, user_id):
           # Tier 1: Instant Google ADK storage
           google_result = await self.google_service.add_memory(...)
           
           # Background: Tiers 2 & 3
           asyncio.create_task(self._background_sync(content, user_id))
           
           return google_result
           
       async def search_memory_hybrid(self, query, user_id):
           # Parallel search all tiers
           # Intelligent result merging and ranking
   ```

3. **Implement intelligent routing logic:**
   - Memory size-based routing
   - User activity pattern analysis
   - Performance-based tier selection

#### Testing Protocol:
```bash
# Test hybrid orchestrator
python -c "
from services.hybrid_orchestrator import HybridMemoryOrchestrator
import asyncio

async def test():
    orchestrator = HybridMemoryOrchestrator()
    await orchestrator.initialize()
    
    # Test memory addition
    result = await orchestrator.add_memory_hybrid(
        'Test hybrid memory', 'test_user'
    )
    print(f'✅ Hybrid add: {result}')
    
    # Test search
    results = await orchestrator.search_memory_hybrid(
        'test', 'test_user'
    )
    print(f'✅ Hybrid search: {len(results)} results')
    
asyncio.run(test())
"
```

### Step 1.4: Google ADK Session Integration (Day 4)
**Commit checkpoint:** `session-1-step-4-session-integration`

#### Tasks:
1. **Implement Google ADK SessionService:**
   ```python
   class GoogleADKSessionService:
       """Google ADK Session management with state persistence"""
       
       async def create_google_session(self, user_id, metadata):
           # Create Google ADK session
           # Set up state management
           
       async def add_session_to_memory(self, session_id, content):
           # Add session context to Google Memory Bank
           # Update session state
   ```

2. **Integrate with existing session management:**
   - Update `adk/session_service.py` 
   - Add Google session prefixes for isolation
   - Implement session state synchronization

3. **Add session analytics and monitoring:**
   - Session creation/duration tracking
   - Memory usage per session
   - Performance metrics collection

#### Testing Protocol:
```bash
# Test Google ADK session integration
python -c "
from adk.session_service import InMemorySessionService
from services.google_memory_service import GoogleADKSessionService
import asyncio

async def test():
    # Test session creation
    session_service = GoogleADKSessionService()
    session_id = await session_service.create_google_session(
        'test_user', {'app': 'test'}
    )
    print(f'✅ Google session created: {session_id}')
    
    # Test memory addition to session
    await session_service.add_session_to_memory(
        session_id, 'Session memory content'
    )
    print('✅ Session memory added')
    
asyncio.run(test())
"

# Test integration with existing system
curl -X POST "http://localhost:8766/sessions/" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "metadata": {"provider": "google_adk"}
  }'
```

## Manual Testing Checklist

After each commit checkpoint:

### Basic Functionality Tests:
- [ ] Service starts without errors
- [ ] Health endpoint responds successfully
- [ ] Google ADK authentication works
- [ ] Memory creation through Google ADK succeeds
- [ ] Search returns results from Google Memory Bank
- [ ] Session creation and management works

### Integration Tests:
- [ ] Hybrid routing works correctly
- [ ] Memory format conversion preserves data
- [ ] Performance meets targets (< 10ms for Google ADK operations)
- [ ] Fallback to Jean V2 works when Google ADK unavailable

### Performance Tests:
- [ ] Memory creation < 5ms average (Tier 1)
- [ ] Search latency < 10ms for cached items
- [ ] Background sync doesn't block foreground operations
- [ ] Resource usage stays within limits

## Debug Logging Strategy

### Log Configuration:
```python
# Add to services/google_memory_service.py
logger = logging.getLogger(__name__)

# Structured logging for debugging
logger.info("🔗 Google ADK operation", extra={
    "operation": "add_memory",
    "user_id": user_id,
    "tier": "google_adk",
    "execution_time_ms": elapsed,
    "memory_size_bytes": len(content),
    "session_id": session_id
})
```

### Debug Commands:
```bash
# Monitor Google ADK operations
tail -f jean_memory_v3.log | grep "Google ADK"

# Check performance metrics
python -c "
from services.hybrid_orchestrator import HybridMemoryOrchestrator
import asyncio

async def debug():
    orch = HybridMemoryOrchestrator()
    await orch.initialize()
    stats = await orch.get_performance_stats()
    print(f'Debug stats: {stats}')
    
asyncio.run(debug())
"
```

## Integration Handoff

### For Session 5 (Final Integration):

1. **Completed interfaces:**
   - `GoogleADKMemoryService` - memory operations
   - `GoogleADKSessionService` - session management  
   - `HybridMemoryOrchestrator` - intelligent routing

2. **Configuration requirements:**
   - Google Cloud project setup
   - Service account credentials
   - Memory Bank configuration

3. **Integration points:**
   - Updated `adk/memory_service.py` with Google ADK routing
   - Enhanced `services/memory_service.py` with hybrid orchestration
   - Modified API routes to use hybrid services

4. **Testing artifacts:**
   - Performance benchmarks
   - Integration test results
   - Debug logs for analysis

## Known Limitations

1. **Google Cloud Setup Required:**
   - Service account with Memory Bank access
   - Vertex AI API enabled
   - Billing account configured

2. **Network Dependencies:**
   - Google Cloud API connectivity required
   - Fallback to local tiers when offline

3. **Rate Limiting:**
   - Google ADK rate limits apply
   - Automatic fallback to lower tiers

## Success Criteria

- [ ] Google ADK successfully integrated as Tier 1 memory
- [ ] Memory operations < 10ms average through Google ADK
- [ ] Hybrid routing distributes load intelligently
- [ ] Session management works with Google ADK
- [ ] All tests pass consistently
- [ ] Performance targets achieved
- [ ] Ready for Session 5 integration

**Next:** Session 2 (Testing Suite) can run in parallel
**Dependencies:** None - this session is self-contained