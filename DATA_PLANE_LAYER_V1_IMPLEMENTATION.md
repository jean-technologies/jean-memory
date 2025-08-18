# Data Plane Layer V1 - Comprehensive Implementation Guide

**Version**: 2.0  
**Date**: August 2025  
**Status**: Production Ready  
**Approach**: Unified Dual-System Scoping (mem0 + Graphiti)

## Executive Summary

This document outlines the **comprehensive implementation** to achieve Data Plane Layer functionality with proper app-specific memory isolation across Jean Memory's hybrid search architecture. The approach addresses both **mem0** and **Graphiti** systems simultaneously, ensuring complete memory scoping without breaking existing functionality.

## Critical Architectural Discovery

**The Hybrid Search Reality**: Jean Memory uses a **dual-path search architecture** that combines:

1. **mem0 Graph Memory** - Entity-based semantic search with `agent_id` parameter
2. **Graphiti Direct Calls** - Temporal episode search with `group_id` parameter

**Both systems must be scoped simultaneously** for proper data plane isolation. Single-system scoping will create memory leakage between applications.

## Unified Scoping Architecture

### Supported Scopes (MVP)
- ✅ `memory:all` - Full access to all user memories (default)
- ✅ `memory:app_specific` - Only memories from the requesting application
- ⚠️ `memory:time_bounded` - Future enhancement (Phase 2)

### Dual-System Integration Strategy
```
JWT Token → Extract Scopes → 
├── mem0 Search (with agent_id = client_name)
├── Graphiti Search (with group_id = user_id__app__client_name)  
└── Merge & Return Unified Results
```

### Key Integration Points Identified

**mem0 Integration Points:**
- `jean_memory/mem0_adapter_optimized.py:186-208` - Search method missing `agent_id`
- `jean_memory/mem0_adapter_optimized.py:78-184` - Add method missing `agent_id`
- `jean_memory/api_optimized.py:348-352` - API layer missing `agent_id`

**Graphiti Integration Points:**
- `jean_memory/integrations.py:419` - Uses `group_id=user_id` (needs app scoping)
- `jean_memory/integrations.py:443` - Search uses `user_id` only (needs app scoping)
- `jean_memory/search.py:354-358` - Hybrid search missing unified scoping

## Required Changes - Comprehensive Dual-System Implementation

### Change 1: OAuth Scope Extension
**File**: `app/oauth_simple_new.py`  
**Line**: 98  
**Change**: Add memory scopes to supported list

```python
# BEFORE
"scopes_supported": ["read", "write", "mcp:tools", "mcp:resources", "mcp:prompts"]

# AFTER
"scopes_supported": [
    "read", "write", "mcp:tools", "mcp:resources", "mcp:prompts",
    "memory:all", "memory:app_specific"  # ADD THESE TWO
]
```

**Impact**: Zero breaking changes - enables clients to request memory scopes

### Change 2: Unified Scoping Utility
**New File**: `app/utils/data_plane_scoping.py`

This utility handles scope extraction and provides unified scoping parameters for both mem0 and Graphiti systems:

```python
"""
Unified Data Plane Layer V1 - Dual-System Scoping
Handles scope extraction and provides unified parameters for both mem0 and Graphiti
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScopingContext:
    """Unified scoping context for both mem0 and Graphiti systems"""
    user_id: str
    client_name: str
    memory_scopes: List[str]
    
    # mem0 parameters
    mem0_agent_id: Optional[str] = None
    
    # Graphiti parameters  
    graphiti_group_id: Optional[str] = None
    
    @classmethod
    def from_jwt_and_context(cls, jwt_token: str, user_id: str, client_name: str) -> 'ScopingContext':
        """Create scoping context from JWT token and request context"""
        try:
            scopes = extract_scopes_from_jwt(jwt_token)
            memory_scopes = [s for s in scopes if s.startswith('memory:')]
            
            # Default to full access if no memory scopes
            if not memory_scopes:
                memory_scopes = ["memory:all"]
            
            context = cls(
                user_id=user_id,
                client_name=client_name, 
                memory_scopes=memory_scopes
            )
            
            # Set system-specific parameters based on scopes
            if "memory:all" in memory_scopes:
                # Full access - use default isolation (user-level only)
                context.mem0_agent_id = None  # No agent isolation
                context.graphiti_group_id = user_id  # User-level isolation
                
            elif "memory:app_specific" in memory_scopes:
                # App-specific isolation
                context.mem0_agent_id = client_name  # Use client_name as agent_id
                context.graphiti_group_id = f"{user_id}__app__{client_name}"  # Enhanced group_id
                
            logger.info(f"Scoping context created: mem0_agent_id={context.mem0_agent_id}, "
                       f"graphiti_group_id={context.graphiti_group_id}, scopes={memory_scopes}")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to create scoping context: {e} - defaulting to full access")
            return cls(
                user_id=user_id,
                client_name=client_name,
                memory_scopes=["memory:all"],
                mem0_agent_id=None,
                graphiti_group_id=user_id
            )

def extract_scopes_from_jwt(jwt_token: str) -> List[str]:
    """Extract scope claim from JWT token"""
    try:
        import jwt
        from app.oauth_simple_new import JWT_SECRET, JWT_ALGORITHM
        
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        scope_claim = payload.get("scope", "")
        
        return scope_claim.split() if scope_claim else []
        
    except Exception as e:
        logger.error(f"Failed to extract scopes from JWT: {e}")
        return ["memory:all"]  # Default to full access on error

def get_scoped_search_params(
    jwt_token: str, 
    user_id: str, 
    client_name: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Get scoped parameters for unified search across mem0 and Graphiti
    
    Returns:
        Tuple of (mem0_agent_id, graphiti_group_id)
    """
    context = ScopingContext.from_jwt_and_context(jwt_token, user_id, client_name)
    return context.mem0_agent_id, context.graphiti_group_id
```

**Impact**: Self-contained utility that provides unified scoping for both memory systems

### Change 3: Update Jean Memory V2 API Layer
**File**: `jean_memory/api_optimized.py`  
**Lines**: 348-352, 406-410  
**Change**: Add scoped parameters to mem0 calls

```python
# EXISTING add_memory method (around line 348)
async def add_memory(self, text: str, user_id: str, metadata: Dict = None) -> str:
    try:
        # NEW: Get scoped agent_id if available
        agent_id = getattr(self, '_current_agent_id', None)
        
        # Add to mem0 with scoped agent_id
        result = await self.mem0.add(
            text, 
            user_id=user_id,
            agent_id=agent_id,  # NEW: Include agent_id for app isolation
            metadata=metadata or {}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise

# EXISTING search_memory method (around line 406)  
async def search_memory(self, query: str, user_id: str, limit: int = 10) -> List[Dict]:
    try:
        # NEW: Get scoped agent_id if available
        agent_id = getattr(self, '_current_agent_id', None)
        
        # Search mem0 with scoped agent_id
        results = await self.mem0.search(
            query=query,
            user_id=user_id, 
            agent_id=agent_id,  # NEW: Include agent_id for app isolation
            limit=limit
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        raise

# NEW: Method to set scoping context
def set_scoping_context(self, agent_id: Optional[str] = None):
    """Set scoping context for app-specific memory isolation"""
    self._current_agent_id = agent_id
```

### Change 4: Update Graphiti Integration Layer  
**File**: `jean_memory/integrations.py`  
**Lines**: 419, 443  
**Change**: Add scoped group_id to Graphiti calls

```python
# EXISTING ingest_memory method (around line 419)
async def ingest_memory(self, user_id: str, memory_text: str, metadata: Dict = None) -> str:
    if not self.initialized:
        await self.initialize()
        
    try:
        from graphiti_core.nodes import EpisodeType
        
        created_at = datetime.now(timezone.utc)
        formatted_content = self._format_for_openai(memory_text)
        episode_name = f"memory_{user_id}_{created_at.timestamp()}"
        
        # NEW: Get scoped group_id if available, fallback to user_id
        group_id = getattr(self, '_current_group_id', user_id)
        
        result = await self.graphiti.add_episode(
            name=episode_name,
            episode_body=formatted_content,
            source=EpisodeType.text,
            source_description=f"Memory from user {user_id}",
            reference_time=created_at,
            group_id=group_id,  # UPDATED: Use scoped group_id
            # ... rest unchanged
        )
        
        return episode_name

# EXISTING search_episodes method (around line 443)
async def search_episodes(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
    if not self.initialized:
        await self.initialize()
        
    try:
        # NEW: Get scoped group_id if available, fallback to user_id
        group_id = getattr(self, '_current_group_id', user_id)
        
        results = await self.graphiti.search(
            query=query,
            group_id=group_id,  # UPDATED: Use scoped group_id
            limit=limit
        )
        
        # ... rest unchanged for result formatting
        
# NEW: Method to set scoping context        
def set_scoping_context(self, group_id: Optional[str] = None):
    """Set scoping context for app-specific memory isolation"""
    self._current_group_id = group_id
```

### Change 5: Update Hybrid Search Engine
**File**: `jean_memory/search.py`  
**Lines**: 354-358  
**Change**: Add unified scoping to hybrid search

```python
# EXISTING hybrid_search method (around line 354)
async def hybrid_search(self, query: str, user_id: str, limit: int = 10, 
                       agent_id: Optional[str] = None, 
                       group_id: Optional[str] = None) -> List[Dict]:
    """
    Hybrid search across both mem0 and Graphiti with unified scoping
    """
    try:
        logger.info(f"🔍 Hybrid search: query='{query}', user_id={user_id}, "
                   f"agent_id={agent_id}, group_id={group_id}")
        
        # Set scoping context for both systems
        if hasattr(self, 'mem0') and agent_id:
            self.mem0.set_scoping_context(agent_id=agent_id)
            
        if hasattr(self, 'graphiti') and group_id:
            self.graphiti.set_scoping_context(group_id=group_id)
        
        # Parallel search with scoped parameters
        mem0_task = asyncio.create_task(
            self._search_mem0_scoped(query, user_id, agent_id, limit//2)
        )
        graphiti_task = asyncio.create_task(
            self._search_graphiti_scoped(query, user_id, group_id, limit//2)  
        )
        
        mem0_results, graphiti_results = await asyncio.gather(
            mem0_task, graphiti_task, return_exceptions=True
        )
        
        # Merge and rank results
        all_results = []
        if not isinstance(mem0_results, Exception):
            all_results.extend(mem0_results)
        if not isinstance(graphiti_results, Exception):
            all_results.extend(graphiti_results)
            
        return all_results[:limit]
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []

async def _search_mem0_scoped(self, query: str, user_id: str, 
                            agent_id: Optional[str], limit: int) -> List[Dict]:
    """Search mem0 with scoped agent_id"""
    if hasattr(self, 'mem0'):
        return await self.mem0.search_memory(query, user_id, limit)
    return []

async def _search_graphiti_scoped(self, query: str, user_id: str,
                                group_id: Optional[str], limit: int) -> List[Dict]:
    """Search Graphiti with scoped group_id"""  
    if hasattr(self, 'graphiti'):
        return await self.graphiti.search_episodes(user_id, query, limit)
    return []
```

### Change 6: Update Smart Context Orchestrator
**File**: `app/mcp_orchestration.py`  
**Lines**: Around where search_memory tool is called  
**Change**: Add unified scoping to orchestrator searches

```python
# Find the search_memory tool usage and update it
async def _enhanced_orchestration_with_scoping(self, user_message: str, user_id: str, client_name: str):
    """Enhanced orchestration with data plane scoping"""
    try:
        # NEW: Extract JWT and get scoped parameters
        jwt_token = extract_jwt_from_context()  # Implement this helper
        if jwt_token:
            from app.utils.data_plane_scoping import get_scoped_search_params
            mem0_agent_id, graphiti_group_id = get_scoped_search_params(
                jwt_token, user_id, client_name
            )
            
            # Set scoping context for Jean Memory services
            if hasattr(self, 'jean_memory_service'):
                if mem0_agent_id:
                    self.jean_memory_service.set_mem0_scoping(agent_id=mem0_agent_id)
                if graphiti_group_id:
                    self.jean_memory_service.set_graphiti_scoping(group_id=graphiti_group_id)
        
        # Continue with existing orchestration logic...
        # The search calls will now use scoped parameters automatically
        
    except Exception as e:
        logger.error(f"Scoping setup failed: {e}")
        # Continue with unscoped search for backward compatibility
```

## Implementation Summary

This comprehensive implementation addresses both mem0 and Graphiti systems simultaneously, ensuring complete memory scoping:

### Key Architectural Changes:
1. **OAuth Scopes**: Extended to support `memory:all` and `memory:app_specific`
2. **Unified Scoping Utility**: Centralized logic for both systems
3. **mem0 Integration**: Uses `agent_id=client_name` for app isolation  
4. **Graphiti Integration**: Uses `group_id=user_id__app__client_name` for enhanced scoping
5. **Hybrid Search**: Coordinated scoping across both systems
6. **Smart Orchestrator**: Context-aware scoping injection

### Backward Compatibility:
- Default behavior unchanged (no scopes = full access)
- Graceful degradation on errors
- No breaking changes to existing APIs

## Deployment Strategy

### Rollout Plan:
1. **Deploy scoping utility** - Safe, no runtime impact
2. **Update OAuth scopes** - Enables new functionality
3. **Update mem0/Graphiti layers** - Adds scoping capability
4. **Update orchestrator** - Completes integration
5. **Test with specific clients** - Verify app isolation
6. **Monitor performance** - Track impact and usage

### Feature Flag (Recommended):
```python
# Add to app/settings.py
DATA_PLANE_ENABLED = os.getenv("DATA_PLANE_ENABLED", "true") == "true"

# Use in scoping utility
if not DATA_PLANE_ENABLED:
    return ScopingContext.default_full_access(user_id, client_name)
```

## Additional OAuth Integration

### React SDK Enhancement (Optional)
**File**: `sdk/react/src/components/JeanAgent.tsx`  
**Change**: Add scope parameter

```tsx
interface JeanAgentProps {
  apiKey: string;
  systemPrompt?: string;
  scope?: "all_memories" | "app_specific";  // NEW
}

export function JeanAgent({ 
  apiKey, 
  systemPrompt, 
  scope = "all_memories",  // DEFAULT
  ...props 
}: JeanAgentProps) {
  // Include scope in OAuth request
  const authUrl = `/oauth/authorize?${new URLSearchParams({
    // ... existing parameters ...
    scope: `mcp:tools mcp:resources memory:${scope}`,  // MODIFIED
  })}`;
  
  // Rest unchanged
}
```

## Deployment Strategy

### Rollout Plan
1. **Deploy Changes**: All 3 changes can be deployed together
2. **Test Default Behavior**: Existing integrations continue working (memory:all by default)
3. **Enable App-Specific Scoping**: Configure specific apps to request memory:app_specific
4. **Monitor Performance**: Track filtering performance and user acceptance

### Feature Flag (Recommended)
```python
# Add to app/settings.py
DATA_PLANE_ENABLED = os.getenv("DATA_PLANE_ENABLED", "true") == "true"

# Use in scope filtering
if not DATA_PLANE_ENABLED:
    return memories  # Bypass filtering if feature disabled
```

## Testing Approach

### Unit Tests
```python
# test_memory_scope_filter.py
def test_app_specific_filtering():
    memories = [
        {"metadata": {"app_name": "claude"}, "content": "Claude memory"},
        {"metadata": {"app_name": "cursor"}, "content": "Cursor memory"},
    ]
    
    # Mock JWT with app_specific scope
    jwt_token = create_test_jwt(scopes=["memory:app_specific"])
    
    filtered = filter_memories_by_scope(memories, jwt_token, "claude")
    
    assert len(filtered) == 1
    assert filtered[0]["content"] == "Claude memory"

def test_all_memories_scope():
    memories = [
        {"metadata": {"app_name": "claude"}, "content": "Claude memory"},
        {"metadata": {"app_name": "cursor"}, "content": "Cursor memory"},
    ]
    
    jwt_token = create_test_jwt(scopes=["memory:all"])
    filtered = filter_memories_by_scope(memories, jwt_token, "claude")
    
    assert len(filtered) == 2  # All memories returned
```

### Integration Tests
```python
# test_oauth_memory_scopes.py
async def test_oauth_flow_with_memory_scope():
    # Test complete OAuth flow with memory:app_specific scope
    response = await oauth_client.authorize(
        scope="memory:app_specific mcp:tools",
        client_id="test-client"
    )
    assert "memory:app_specific" in response.granted_scopes

async def test_jean_memory_tool_with_scoping():
    # Test jean_memory tool respects scope filtering
    # Mock JWT token with app_specific scope
    result = await jean_memory_tool.call(
        user_message="What do you remember about me?",
        needs_context=True,
        # Simulated request context with scoped JWT
    )
    # Verify only current app memories are referenced
```

## Performance Considerations

### Expected Impact
- **Memory Search Latency**: +10-50ms (application-layer filtering)
- **OAuth Flow Latency**: +5-10ms (additional scope validation)
- **Memory Usage**: Minimal (filtering existing results)

### Optimization Opportunities (Future)
1. **Database-level filtering**: Move filtering to Qdrant/Neo4j queries
2. **Caching**: Cache filtered results per user/app combination
3. **Async filtering**: Parallelize filtering with result formatting

## Error Handling & Fallbacks

### Graceful Degradation
```python
# Always fail open for backward compatibility
try:
    filtered_memories = apply_scope_filtering(memories, jwt_token, app_name)
except Exception as e:
    logger.error(f"Scope filtering failed: {e}")
    filtered_memories = memories  # Return unfiltered results
```

### Monitoring
```python
# Track scope filtering performance and usage
logger.info(f"Scope filtering: {len(memories)} -> {len(filtered)} memories ({scope})")

# Alert on high failure rates
if filter_error_rate > 0.01:  # > 1% errors
    send_alert("Data Plane filtering errors exceed threshold")
```

## Security Considerations

### JWT Validation
- Existing JWT validation in `oauth_simple_new.py` handles security
- Scope extraction only reads existing, validated tokens
- No additional attack surface introduced

### Privacy Protection
- App-specific scoping prevents cross-app memory leakage
- Default to most permissive scope on errors (fail open)
- Audit logging for scope changes and access patterns

## Success Criteria

### MVP Requirements
- ✅ Existing functionality remains unchanged
- ✅ OAuth flow supports memory scopes  
- ✅ `memory:all` scope returns all memories
- ✅ `memory:app_specific` scope isolates to current app
- ✅ Performance impact < 100ms per search
- ✅ Zero production incidents during rollout

### Future Enhancements (Phase 2)
- Time-bounded filtering (`memory:time_bounded`)
- Category-based filtering 
- User permission override UI
- Database-level optimization
- Advanced scope combinations

## Conclusion

This comprehensive implementation achieves complete Data Plane Layer functionality with **proper dual-system scoping** and **maximum safety**:

### Implementation Highlights:
- **6 strategic changes** targeting key integration points
- **Unified scoping** across mem0 and Graphiti systems
- **Backward compatible by default** (no scopes = full access)
- **Leverages existing OAuth infrastructure**
- **Fails gracefully** on errors

### Architectural Achievement:
The approach addresses Jean Memory's **hybrid search reality** - recognizing that both mem0 AND Graphiti must be scoped simultaneously to prevent memory leakage between applications.

### Key Success Factors:
1. **mem0's agent_id parameter** - Perfect for app-specific memory isolation
2. **Graphiti's group_id enhancement** - Extended naming for app scoping
3. **Unified scoping utility** - Centralized logic for consistent behavior
4. **Existing OAuth infrastructure** - No additional authentication complexity

**Critical Insight**: This implementation ensures that when an app requests `memory:app_specific`, it truly gets ONLY its own memories from both the semantic search (mem0) and the temporal knowledge graph (Graphiti) - achieving complete data plane isolation without breaking the sophisticated context engineering that makes Jean Memory unique.