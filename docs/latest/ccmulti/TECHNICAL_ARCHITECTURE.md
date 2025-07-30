# Claude Code Multi-Agent Technical Architecture

## Overview

This document outlines the technical architecture for implementing the Claude Code multi-agent workflow with minimal risk and maximal alignment with the user workflow: **Task Input → Planning → Distribution → Coordinated Execution → Completion**.

## Core Technical Requirements

### Performance Requirements (Real-time Coordination)
- **File lock checks**: < 200ms (current: 2-4s)
- **Change broadcasts**: < 500ms (current: 2-4s)  
- **Sync operations**: < 1s (current: 2-6s)
- **Agent messaging**: < 300ms (current: 2-4s)

### User Workflow Technical Mapping

```
📋 Task Input → Simple JSON task list
🧠 Planning → Codebase analysis agent with collision detection
📤 Distribution → Automated prompt generation per agent
⚡ Coordinated Execution → Real-time shared memory tools
✅ Completion → Progress tracking dashboard
```

## Architecture Solution: Hybrid Memory System

### Core Principle
**Use the right tool for the right job:**
- **Google ADK**: Fast session coordination (1-50ms operations)
- **Jean Memory**: Long-term context when explicitly needed (2-6s operations)

### Technical Implementation

#### 1. Session Detection (Minimal Changes)
```python
# Virtual User ID Pattern for Session Isolation
# Standard: user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
# Session:  user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464__session__webscraper__research"

def parse_session_info(user_id: str) -> Optional[Dict]:
    if "__session__" in user_id:
        parts = user_id.split("__")
        if len(parts) >= 4:
            return {
                "base_user_id": parts[0],
                "session_name": parts[2],
                "agent_id": parts[3],
                "is_session": True
            }
    return None
```

#### 2. Google ADK Integration
```python
# Fast coordination using Google ADK
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()

# Session state for coordination
session.state = {
    "file_locks": {},
    "agent_messages": [],
    "recent_changes": [],
    "task_assignments": {},
    "completion_status": {}
}
```

#### 3. Coordination Tools for User Workflow

**Phase 2: Planning Tools**
```python
@mcp.tool()
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Analyze collision potential between tasks"""
    # Codebase analysis for dependency detection
    # File overlap analysis
    # Execution sequence optimization
```

**Phase 4: Execution Coordination Tools**
```python
@mcp.tool() 
async def check_agent_status() -> Dict:
    """See what other agents are working on"""

@mcp.tool()
async def claim_file_lock(file_paths: List[str]) -> Dict:
    """Prevent file conflicts - 1-5ms response time"""

@mcp.tool()
async def sync_progress(task_id: str, status: str) -> Dict:
    """Share completion status - 5-50ms response time"""
```

## Performance Comparison

| Operation | Current System | ADK Integration | Improvement |
|-----------|----------------|-----------------|-------------|
| Planning Analysis | 10-30s | 5-15s | 2-6x faster |
| File Lock Check | 2-4s | 1-5ms | 400-4000x faster |
| Change Broadcast | 2-4s | 1-10ms | 200-4000x faster |
| Agent Messaging | 2-4s | 1-5ms | 400-4000x faster |
| Status Sync | 2-6s | 5-50ms | 40-1200x faster |

## Implementation Strategy

### Claude Code Exclusive Implementation
- **Zero impact** on other MCP clients (ChatGPT, Cursor, VS Code)
- **Backward compatible** with existing Claude Code connections
- **Session isolation** using virtual user IDs

### Minimal Risk Approach
1. **Additive integration** - New session tools alongside existing memory tools
2. **Smart routing** - Detect session context automatically
3. **Fallback compatibility** - Standard tools always available

### Google ADK Express Mode (Free Tier)
- **100 Session Entities** (sufficient for development)
- **10,000 Event Entities** (supports extensive coordination)
- **200 Memory Entities** (adequate for session coordination)
- **90-day free tier** perfect for implementation and testing

## Database Schema (Already Implemented)

```sql
-- Session management tables (existing)
CREATE TABLE claude_code_sessions (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    user_id UUID REFERENCES users(id),
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE claude_code_agents (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES claude_code_sessions(id),
    name VARCHAR NOT NULL,
    connection_url VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'disconnected'
);
```

## Risk Mitigation

### High Priority Risks
1. **ADK Integration Complexity** → Start with Express Mode, simple implementation
2. **Session Detection Logic** → Conservative detection with explicit markers
3. **Performance Expectations** → Even 10x improvement provides value

### Success Criteria
- **Core functionality**: File locking, agent messaging, status sync
- **Performance targets**: 10-100x faster coordination operations  
- **Quality gates**: Zero impact on existing clients
- **User experience**: Seamless workflow from task input to completion

This architecture directly supports the user workflow while providing the technical foundation for collision-free multi-agent development.