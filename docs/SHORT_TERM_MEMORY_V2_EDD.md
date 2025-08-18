# Short-term Memory V2 - Engineering Design Document

**Version**: 2.0  
**Date**: January 2025  
**Status**: Ready for Implementation

## Technical Architecture

### System Overview
Enhance the existing `ContextCacheManager` with a new `FAISSSessionCache` layer that provides server-side semantic search capabilities using FAISS vector similarity search.

### Key Components

#### 1. FAISSSessionCache Class
**Location**: `app/utils/mcp_modules/cache_manager.py`  
**Purpose**: Manage per-user FAISS indices for semantic search

**Data Structures**:
```python
_session_indices: Dict[str, faiss.Index]  # user_id -> FAISS index
_session_memories: Dict[str, List[Dict]]  # user_id -> memory objects
_session_timestamps: Dict[str, datetime]   # user_id -> last access time
```

**Core Methods**:
- `cache_session_memories_with_faiss()`: Index memories with FAISS
- `search_session_memories_semantic()`: Perform semantic search
- `cleanup_expired_sessions()`: Remove expired indices
- `get_cache_stats()`: Return monitoring metrics

#### 2. Enhanced ContextCacheManager
**Location**: `app/utils/mcp_modules/cache_manager.py`  
**Changes**: Add semantic search methods while preserving existing functionality

**New Methods**:
- `cache_session_memories_with_faiss()`: Wrapper for FAISS caching
- `search_session_memories_semantic()`: Wrapper for semantic search
- `get_faiss_stats()`: Expose FAISS metrics

#### 3. Enhanced jean_memory Tool
**Location**: `app/tools/orchestration.py`  
**Changes**: Integrate semantic search into existing flow

**Modifications**:
- Add semantic search branch for simple queries (<150 chars)
- Enhanced pre-loading with 50 memories (vs 30)
- Embedding generation for queries
- Fallback to existing keyword search

#### 4. RenderMemoryManager
**Location**: `app/utils/mcp_modules/cache_manager.py`  
**Purpose**: Manage memory within Render's 512MB limit

**Features**:
- Automatic cleanup of expired sessions (30min TTL)
- Hard limit of 50 concurrent user sessions
- Memory health monitoring
- Periodic cleanup task integration

## Implementation Details

### FAISS Index Configuration
- **Index Type**: `IndexFlatL2` (exact L2 distance search)
- **Dimension**: 1536 (OpenAI embedding size)
- **Distance Threshold**: 0.8 (for relevance filtering)

### Memory Management Strategy
- **Per-User Memory**: ~6MB (index + memories)
- **Max Concurrent Users**: 50 (300MB total)
- **Session TTL**: 30 minutes
- **Cleanup Frequency**: Every 10 minutes

### Embedding Integration
- **Source**: Reuse existing mem0 OpenAI embeddings
- **Method**: `mem0_client._get_embedding()`
- **Consistency**: Same embeddings for indexing and querying

### Error Handling
- Graceful fallback to keyword search on FAISS failure
- Logging at all critical points
- Session cleanup on errors
- Memory limit protection

## API Changes

### Modified Endpoints
None - all changes are internal to existing tools

### New Internal APIs
```python
# Semantic search
await search_session_memories_semantic(user_id, query_embedding, limit=5)

# Enhanced caching
await cache_session_memories_with_faiss(user_id, memories)

# Memory monitoring
get_faiss_stats() -> Dict
get_memory_health() -> Dict
```

## Database Schema
No changes - uses existing memory structure with embedded vectors

## Performance Characteristics

### Time Complexity
- **Index Creation**: O(n) for n memories
- **Search**: O(n) for exact search (acceptable for <100 memories)
- **Cleanup**: O(1) per session

### Space Complexity
- **Per User**: 6MB (1536 * 4 bytes * 50 memories + overhead)
- **Total System**: 300MB for 50 concurrent users

### Response Times
- **Cache Hit**: <10ms
- **Cache Miss + Fallback**: ~50ms (existing speed)
- **Index Creation**: <100ms for 50 memories

## Security Considerations
- Session isolation ensures user data separation
- No persistent storage of FAISS indices
- Automatic cleanup prevents data accumulation
- Existing authentication/authorization unchanged

## Deployment Strategy

### Dependencies
```txt
faiss-cpu==1.7.4
numpy>=1.21.0  # Already present
```

### Environment Variables
None required - uses existing configuration

### Rollback Plan
1. Remove FAISS import statements
2. Disable semantic search branches in jean_memory
3. Existing keyword search continues functioning

## Testing Strategy

### Unit Tests
- FAISS index creation and search
- Session cleanup logic
- Memory limit enforcement
- Embedding generation

### Integration Tests
- End-to-end semantic search flow
- MCP client compatibility
- Fallback behavior
- Concurrent user handling

### Performance Tests
- 50 concurrent user load test
- Memory usage monitoring
- Response time benchmarks
- Cleanup effectiveness

## Monitoring & Observability

### Metrics to Track
- Active user sessions
- Memory usage (MB)
- Search hit rates
- Response times
- Cleanup frequency

### Logging
- FAISS operations (INFO level)
- Memory cleanup (INFO level)
- Errors (ERROR level)
- Performance stats (DEBUG level)

## Risk Mitigation

### Technical Risks
1. **Memory Overflow**: Hard limits + periodic cleanup
2. **FAISS Failures**: Automatic fallback to keyword search
3. **Embedding Errors**: Skip semantic search, use existing flow
4. **Session Leaks**: TTL-based cleanup + monitoring

### Operational Risks
1. **Render Limits**: Conservative 50-user limit
2. **Performance Degradation**: Monitoring + alerts
3. **Data Loss**: In-memory only, no persistence needed