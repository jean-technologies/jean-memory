# Claude Code Multi-Agent Final Architecture Design

## Summary of Analysis

### Issues Identified:
1. **Performance**: Jean Memory ingestion (2-4s) and search (2-6s) too slow for real-time coordination
2. **Precision**: Full user memory search returns irrelevant results for session coordination
3. **Scale**: Searching 10,000+ memories is overkill for file locking and change coordination

### Solution: Hybrid Architecture with Google ADK

**Core Principle**: Use the right tool for the right job
- **Google ADK**: Fast session coordination and agent communication
- **Jean Memory**: Long-term context when explicitly needed

## Recommended Architecture

### 1. Dual Memory System

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude Code Multi-Agent Session             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Fast Coordination Layer (Google ADK)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Session State (1-50ms operations)                  │   │
│  │  ├─ File locks                                      │   │
│  │  ├─ Recent changes                                  │   │
│  │  ├─ Agent messages                                  │   │
│  │  └─ Coordination metadata                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Context Layer (Jean Memory)                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  User's Long-term Memory (2-6s operations)          │   │
│  │  ├─ Project history                                 │   │
│  │  ├─ Code documentation                              │   │
│  │  ├─ User preferences                                │   │
│  │  └─ Domain knowledge                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Control Layer Options

#### Option A: Dashboard Control (Recommended)

**Human-in-the-loop coordination through Jean Memory dashboard:**

```
┌─────────────────────────────────────────────────────────────┐
│                Jean Memory Dashboard                        │
├─────────────────────────────────────────────────────────────┤
│  Claude Code Sessions Panel                                │
│  ┌─────────────────────┐  ┌─────────────────────────────┐   │
│  │ Active Sessions     │  │ Create New Session          │   │
│  │ ├─ webscraper_dev   │  │ ├─ Session name             │   │
│  │ │  ├─ research      │  │ ├─ Add agents               │   │
│  │ │  └─ implementation│  │ └─ Generate connection URLs │   │
│  │ ├─ api_refactor     │  └─────────────────────────────┘   │
│  │ │  ├─ backend       │                                   │
│  │ │  └─ frontend      │  ┌─────────────────────────────┐   │
│  │ └─ + New Session    │  │ Session Monitor             │   │
│  └─────────────────────┘  │ ├─ Active file locks        │   │
│                           │ ├─ Recent agent changes     │   │
│                           │ ├─ Agent communication      │   │
│                           │ └─ Performance metrics      │   │
│                           └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- **Human oversight**: User can monitor and control agent coordination
- **Visual feedback**: See what agents are working on in real-time
- **Easy session management**: Create/destroy sessions through UI
- **Conflict resolution**: Human can resolve agent conflicts when needed

#### Option B: Autonomous Multi-Agent (Advanced)

**Fully autonomous coordination without human intervention:**

```
Agent Manager Service:
├─ Session lifecycle management
├─ Automatic conflict resolution  
├─ Load balancing between agents
├─ Performance optimization
└─ Error recovery
```

**Benefits:**
- **Fully autonomous**: No human intervention required
- **Advanced coordination**: AI-powered conflict resolution
- **Scalable**: Can handle many concurrent sessions

**Drawbacks:**
- **Complex**: Requires sophisticated coordination logic
- **Risk**: Agents could conflict or interfere without oversight
- **Development time**: Significant additional complexity

### 3. Minimal Implementation Path

#### Phase 1: Basic ADK Integration (1-2 days)

**Setup:**
1. Add Google ADK to dependencies
2. Set up Express Mode account and Agent Engine
3. Initialize ADK services in MCP router

**Implementation:**
```python
# app/services/adk_coordination.py
from google.adk.sessions import InMemorySessionService, VertexAiSessionService
from google.adk.memory import InMemoryMemoryService

class ADKCoordinationService:
    def __init__(self):
        # Use in-memory for development, Vertex AI for production
        self.session_service = InMemorySessionService()
        self.memory_service = InMemoryMemoryService()
    
    async def get_or_create_session(self, session_info: dict):
        """Get existing session or create new one"""
        try:
            return await self.session_service.get_session(
                app_name=session_info['session_name'],
                user_id=session_info['base_user_id'],
                session_id=session_info['session_name']
            )
        except:
            return await self.session_service.create_session(
                app_name=session_info['session_name'],
                user_id=session_info['base_user_id'],
                session_id=session_info['session_name'],
                state={
                    'file_locks': {},
                    'recent_changes': [],
                    'agent_messages': [],
                    'active_agents': []
                }
            )
```

#### Phase 2: Enhanced MCP Router (Half day)

**Session Detection:**
```python
# app/routing/mcp.py - Enhanced request handler
async def handle_request_logic(request: Request, body: dict, background_tasks: BackgroundTasks):
    # ... existing auth logic ...
    
    # NEW: Detect session mode
    session_info = parse_session_info(user_id_from_header)
    if session_info and client_name_from_header == "claude code":
        # Initialize ADK session
        adk_service = get_adk_service()
        session = await adk_service.get_or_create_session(session_info)
        request.state.adk_session = session
        request.state.session_info = session_info
    
    # Continue with existing logic...

def parse_session_info(user_id: str) -> Optional[Dict]:
    """Parse session info from virtual user_id"""
    if "__session__" in user_id:
        parts = user_id.split("__")
        if len(parts) >= 4:
            return {
                "base_user_id": parts[0],
                "session_name": parts[2], 
                "agent_id": parts[3],
                "virtual_user_id": user_id,
                "is_session": True
            }
    return None
```

#### Phase 3: Fast Coordination Tools (1 day)

**Session-optimized tools:**
```python
# app/tools/adk_coordination.py
@mcp.tool(description="🔒 [Session] Fast file locking using ADK")
async def adk_claim_files(file_paths: List[str], operation: str = "write") -> Dict:
    """Ultra-fast file locking using ADK session state"""
    session = get_current_adk_session()
    
    # Check locks in session state (1-5ms operation)
    current_locks = session.state.get('file_locks', {})
    conflicts = check_lock_conflicts(file_paths, current_locks)
    
    if conflicts:
        return {"success": False, "conflicts": conflicts}
    
    # Acquire locks
    for file_path in file_paths:
        current_locks[file_path] = {
            'agent': get_current_agent_id(),
            'operation': operation,
            'acquired_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
    
    # Update session state (1-5ms operation)
    session.state['file_locks'] = current_locks
    await session_service.append_event(session, create_lock_event(current_locks))
    
    return {"success": True, "locked_files": file_paths}

@mcp.tool(description="📢 [Session] Instant agent messaging")
async def adk_send_message(message: str, message_type: str = "info") -> Dict:
    """Instant messaging between agents using ADK"""
    session = get_current_adk_session()
    
    messages = session.state.get('agent_messages', [])
    messages.append({
        'from': get_current_agent_id(),
        'message': message,
        'type': message_type,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Keep only last 100 messages
    messages = messages[-100:]
    session.state['agent_messages'] = messages
    
    await session_service.append_event(session, create_message_event(messages))
    return {"success": True, "message_sent": True}
```

#### Phase 4: Intelligent Context Routing (1 day)

**Smart memory routing:**
```python
# app/tools/hybrid_memory.py
async def smart_context_search(query: str, context_type: str = "auto") -> Dict:
    """Route queries to appropriate memory system"""
    
    # Coordination queries → ADK (fast)
    coordination_keywords = ["lock", "change", "message", "status", "sync"]
    if any(keyword in query.lower() for keyword in coordination_keywords):
        return await adk_coordination_search(query)
    
    # Context queries → Jean Memory (comprehensive)
    context_keywords = ["remember", "history", "documentation", "previous"]
    if any(keyword in query.lower() for keyword in context_keywords):
        return await jean_memory_search(query)
    
    # Auto-detect based on query complexity
    if len(query.split()) < 5:  # Simple queries
        return await adk_coordination_search(query)
    else:  # Complex queries
        return await jean_memory_search(query)

async def adk_coordination_search(query: str) -> Dict:
    """Fast session-specific search"""
    session = get_current_adk_session()
    memory_service = get_adk_memory_service()
    
    # Search session-specific memory (10-50ms)
    results = await memory_service.search_memory(
        app_name=session.app_name,
        user_id=session.user_id,
        query=query
    )
    
    return format_coordination_results(results)

async def jean_memory_search(query: str) -> Dict:
    """Comprehensive context search"""
    user_id = get_base_user_id()  # Original user ID, not virtual
    
    # Use existing jean_memory for full context (2-6s)
    results = await jean_memory.search(query, user_id)
    return format_context_results(results)
```

### 4. Performance Expectations

#### Coordination Operations (ADK-powered):
- **File lock check**: 1-5ms (vs current 2-4s) - **400-4000x faster**
- **Change broadcast**: 1-10ms (vs current 2-4s) - **200-4000x faster**  
- **Agent messaging**: 1-5ms (vs current 2-4s) - **400-4000x faster**
- **Sync operations**: 5-50ms (vs current 2-6s) - **40-1200x faster**

#### Context Operations (Jean Memory):
- **Long-term context**: 2-6s (unchanged, used only when needed)
- **Project history**: 2-6s (unchanged, used only when needed)

### 5. Development Timeline

**Week 1: Core Implementation**
- Day 1-2: ADK setup and basic integration
- Day 3: Enhanced MCP routing with session detection
- Day 4-5: Fast coordination tools implementation

**Week 2: Enhancement and Testing**
- Day 1-2: Intelligent context routing
- Day 3: Dashboard integration for session management
- Day 4-5: Testing with multiple agents and performance benchmarking

**Week 3: Production Readiness**
- Day 1-2: Express Mode → Vertex AI migration planning
- Day 3-4: Error handling and edge case testing
- Day 5: Documentation and deployment preparation

### 6. Control Layer Recommendation: Dashboard-First

**Rationale:**
- **User visibility**: Users can see what their agents are doing
- **Safety**: Human oversight prevents agent conflicts
- **Debugging**: Easy to understand coordination issues
- **Gradual adoption**: Users can opt into multi-agent gradually

**Implementation:**
1. **Session Management Panel**: Create/manage Claude Code sessions
2. **Real-time Monitoring**: View active locks, changes, messages
3. **Agent Status**: See which agents are connected and active
4. **Intervention Tools**: Human can resolve conflicts or pause agents

This hybrid architecture solves both performance and precision issues while providing a clear development path and user control mechanism.