# Short-term Memory V1 Implementation

**Version**: 1.0  
**Date**: January 2025  
**Status**: Minimal Viable Solution  
**Objective**: Add session-local memory caching to existing context engineering without architectural changes

## Problem Statement

The current `jean_memory` tool has excellent AI-powered context engineering but requires cloud database queries for every context request. This creates latency for simple, repeated queries within the same session.

## Minimal Solution

**Leverage existing `ContextCacheManager`** (30-minute TTL) to cache pre-loaded user memories at session start, enabling instant context lookup for simple queries while preserving complex orchestration for deep analysis.

## Implementation

### 1. Enhance ContextCacheManager (Zero Risk)

Extend existing cache manager in `app/utils/mcp_modules/cache_manager.py`:

```python
class ContextCacheManager:
    # Existing methods...
    
    @staticmethod
    def cache_session_memories(user_id: str, memories: List[Dict]) -> None:
        """Cache user memories for session-local instant access"""
        cache_key = f"session_memories_{user_id}"
        ContextCacheManager.update_context_cache(cache_key, {
            "memories": memories,
            "loaded_at": datetime.now().isoformat()
        }, user_id)
    
    @staticmethod
    def get_session_memories(user_id: str) -> List[Dict]:
        """Get cached session memories"""
        cache_key = f"session_memories_{user_id}"
        cached = ContextCacheManager.get_cached_context(cache_key)
        return cached.get("context_data", {}).get("memories", []) if cached else []
    
    @staticmethod
    def search_session_memories(user_id: str, query: str, limit: int = 5) -> str:
        """Fast keyword search in session memories"""
        memories = ContextCacheManager.get_session_memories(user_id)
        if not memories:
            return ""
        
        query_words = set(query.lower().split())
        relevant = []
        
        for mem in memories:
            content = mem.get('memory', mem.get('content', '')).lower()
            if any(word in content for word in query_words if len(word) > 2):
                relevant.append(mem.get('memory', mem.get('content', '')))
        
        return "\n".join(relevant[:limit])
```

### 2. Modify jean_memory Tool (Minimal Change)

Add session memory pre-loading in `app/tools/orchestration.py`:

```python
@mcp.tool(description="🌟 ALWAYS USE THIS TOOL...")
async def jean_memory(user_message: str, is_new_conversation: bool, needs_context: bool = True) -> str:
    # Existing setup...
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid or not client_name:
        return "Error: User ID not available"

    orchestrator = get_smart_orchestrator()
    
    # NEW: Pre-load session memories for new conversations
    if is_new_conversation:
        await preload_session_memories(supa_uid, orchestrator)
    
    # Existing background tasks (unchanged)...
    background_tasks.add_task(
        orchestrator.triage_and_save_memory_background,
        user_message, supa_uid, client_name
    )
    
    # NEW: Fast session lookup for simple queries
    if needs_context and not is_new_conversation and len(user_message) < 150:
        session_context = orchestrator.cache_manager.search_session_memories(supa_uid, user_message)
        if session_context:
            logger.info("⚡ [Session Cache] Using cached memories for fast response")
            return orchestrator._append_system_directive(f"---\n[Session Context]\n{session_context}\n---")
    
    # Existing logic (unchanged)...
    if is_new_conversation:
        narrative = await orchestrator._get_cached_narrative(supa_uid)
        # ... existing new conversation logic
    
    if not needs_context:
        # ... existing no-context logic
    
    # Existing standard orchestration for complex queries
    return await orchestrator._standard_orchestration(user_message, supa_uid, client_name, is_new_conversation)

# NEW: Helper function
async def preload_session_memories(user_id: str, orchestrator) -> None:
    """Pre-load user memories into session cache"""
    try:
        # Check if already loaded
        if orchestrator.cache_manager.get_session_memories(user_id):
            return
        
        # Load recent memories using existing search
        search_results = await orchestrator._get_tools()['search_memory'](
            query="personal background preferences current", limit=30
        )
        
        memories = json.loads(search_results) if search_results else []
        orchestrator.cache_manager.cache_session_memories(user_id, memories)
        
        logger.info(f"⚡ [Session Cache] Pre-loaded {len(memories)} memories for {user_id}")
    except Exception as e:
        logger.warning(f"⚡ [Session Cache] Pre-loading failed: {e}")
```

### 3. Zero Changes Required

- **No changes to `SmartContextOrchestrator`**
- **No changes to database layer**
- **No changes to MCP protocol**
- **No changes to authentication**
- **No changes to background processing**

## Logic Flow

### New Conversation
1. Pre-load 30 recent memories into `ContextCacheManager` (30-min TTL)
2. Continue with existing cached narrative logic
3. Background triage and analysis unchanged

### Continuing Conversation - Simple Query (<150 chars)
1. **NEW**: Check session cache for instant context
2. If found: Return immediately (⚡ **~50ms**)
3. If not found: Fall back to existing standard orchestration

### Continuing Conversation - Complex Query
1. Skip session cache
2. Use existing standard orchestration unchanged
3. Full AI planning and deep analysis preserved

## Performance Improvements

| Scenario | Before | After | Improvement |
|----------|---------|-------|-------------|
| Simple context query | 2-3s (cloud search) | ~50ms (cache hit) | **40-60x faster** |
| Complex orchestration | 2-10s | 2-10s | Unchanged |
| New conversation | 1-3s | 1-3s + preload | Minimal impact |

## Implementation Timeline

### Day 1: Cache Enhancement
- Add 3 methods to existing `ContextCacheManager`
- Zero risk - pure additions

### Day 2: Tool Integration  
- Add session memory pre-loading
- Add fast lookup logic
- 10 lines of code changes

### Day 3: Testing & Monitoring
- Test session cache hit rates
- Monitor performance improvements
- Verify no regressions

## Risk Assessment

- **Breaking Changes**: None
- **Performance Impact**: Positive only
- **Memory Usage**: +5MB per active user session
- **Complexity**: Minimal - leverages existing systems
- **Rollback**: Simple - remove 10 lines of code

## Success Metrics

- **Cache Hit Rate**: >40% for simple queries
- **Response Time**: <100ms for cached responses  
- **Memory Usage**: <10MB additional per 100 active users
- **Zero Regressions**: All existing functionality unchanged

## Future Enhancements

- Smart pre-loading based on conversation topics
- FAISS local indexing for semantic search
- Redis integration for distributed sessions

---

This implementation provides **immediate performance gains** with **zero architectural risk** by building on your existing, proven caching infrastructure.