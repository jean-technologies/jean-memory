# Claude Code Multi-Agent Technical Architecture

## Overview

This document outlines the technical architecture for implementing the Claude Code multi-agent workflow using **multiple Claude Code sessions** with cross-terminal coordination for optimal alignment with the user workflow: **Task Input → Planning → Distribution → Coordinated Execution → Completion**.

## ✅ Phase 1 Implementation Status (January 2025)

**Successfully Implemented:**
- Virtual user ID parsing in `/app/routing/mcp.py` 
- Database session registration with auto-creation
- Session-aware tool descriptions in `/app/clients/claude.py`
- Multi-terminal HTTP v2 transport endpoints at `/mcp/v2/claude/{virtual_user_id}`
- Cross-terminal coordination infrastructure

**Current Architecture Achievements:**
- Planner and implementer agents successfully connect via separate terminals
- Virtual user ID pattern `{user_id}__session__{session_id}__{agent_id}` working
- Database coordination ready for Phase 2 cross-session tools

## Core Technical Requirements

### Performance Requirements (Multi-Terminal Coordination)
- **Cross-session coordination**: < 50ms (database-backed)
- **Context isolation**: True process-level isolation per terminal
- **File conflict prevention**: < 10ms (database locking)
- **Status synchronization**: Real-time via database updates

### User Workflow Technical Mapping

```
📋 Task Input → Planning agent in Terminal 1
🧠 Planning → Dedicated Claude Code session with full context window
📤 Distribution → Launch 1-4 implementation agents in separate terminals (scalable 2-5 agent architecture)
⚡ Coordinated Execution → Multiple Claude Code sessions + cross-session coordination
✅ Completion → Database-tracked progress across all terminals
```

## Architecture Solution: Multi-Terminal Sessions + Database Coordination

### Core Principle
**Leverage existing infrastructure for true parallel execution:**
- **Multiple Claude Code Sessions**: Each agent runs in separate terminal with full context window
- **Database Coordination**: Use existing session schema for cross-terminal coordination
- **Virtual User ID Pattern**: Existing `{user_id}__session__{session_id}__{agent_id}` pattern
- **MCP HTTP Transport**: Proven `/mcp/v2/{client_name}/{user_id}` infrastructure
- **Cross-Session Tools**: Database-backed coordination tools ([MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp))

### Technical Implementation

#### 1. Multi-Terminal Session Management

**Scalable Session Creation (2-5 Agents)**
```bash
# Terminal 1: Planning Agent (Always Required)
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__planner

# Minimum Configuration (2 Agents)
# Terminal 2: Implementation Agent A
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_a

# Optimal Configuration (3 Agents) 
# Terminal 3: Implementation Agent B
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_b

# Maximum Configuration (4-5 Agents)
# Terminal 4: Implementation Agent C
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_c

# Terminal 5: Implementation Agent D
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_d
```

**Virtual User ID Pattern**
- Format: `{user_id}__session__{session_id}__{agent_id}`
- Purpose: Enables cross-session coordination while maintaining isolation
- Database Integration: Uses existing claude_code_sessions and claude_code_agents tables
- Session Detection: Backend parses virtual user ID to identify multi-agent context

#### 2. Cross-Session Coordination Tools

**Database-Backed Coordination**
```python
# Session coordination uses existing database schema
CREATE TABLE claude_code_sessions (
    id VARCHAR PRIMARY KEY,  -- session_id from virtual user ID
    name VARCHAR NOT NULL,
    user_id UUID REFERENCES users(id),  -- parsed from virtual user ID
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE claude_code_agents (
    id VARCHAR PRIMARY KEY,  -- agent_id from virtual user ID  
    session_id VARCHAR REFERENCES claude_code_sessions(id),
    name VARCHAR NOT NULL,  -- 'planner', 'impl_a', 'impl_b', 'impl_c', 'impl_d' (scalable 2-5 agents)
    connection_url VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'connected'
);
```

**Cross-Terminal Communication**
- Database-backed status updates
- File lock coordination via MCP tools
- Real-time progress tracking
- Session-aware tool routing

#### 3. Cross-Session Coordination Tools

**Planning Phase Tools (Terminal 1: Planning Agent)**
```python
@mcp.tool()
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Analyze collision potential and create cross-session distribution plan"""
    # Parse session info from virtual user ID
    session_info = parse_virtual_user_id(context.user_id)
    
    # Lightweight codebase analysis for file dependencies
    # Generate terminal-specific agent assignments
    # Create coordination strategy using database
    return {
        "conflicts": [],
        "terminal_assignments": {},
        "coordination_strategy": "database",
        "execution_sequence": [],
        "session_id": session_info.session_id
    }

@mcp.tool()
async def create_task_distribution(analysis: Dict) -> Dict:
    """Generate terminal-specific prompts and coordination setup"""
    # Create specialized prompts for implementation terminals
    # Set up database-backed coordination
    # Return terminal invocation instructions
    return {"terminal_prompts": [], "database_config": {}}
```

**Execution Coordination Tools (Terminals 2+: Implementation Agents)**
```python
@mcp.tool()
async def claim_file_lock(file_paths: List[str]) -> Dict:
    """Create cross-session file locks via database"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # Create database-backed locks visible across all terminals
    # Coordinate with other Claude Code sessions
    return {"locked_files": file_paths, "lock_id": uuid4(), "session": session_info.session_id}

@mcp.tool()
async def sync_progress(task_id: str, status: str) -> Dict:
    """Broadcast progress updates across terminals"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # Update database with progress visible to all session agents
    # Notify other terminals of status changes
    return {"task_id": task_id, "status": status, "session": session_info.session_id, "broadcast": True}

@mcp.tool()
async def check_agent_status() -> Dict:
    """Check status of other agents in the same session"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # Query database for other agents in same session
    # Return real-time status across all terminals
    return {"agents": [], "session": session_info.session_id}
```

## Performance Comparison

| Operation | Current System | Multi-Terminal + Database | Improvement |
|-----------|----------------|---------------------------|-------------|
| Planning Analysis | 10-30s | 5-15s | 2-6x faster |
| Agent Context Switch | 2-4s | 0s (separate processes) | ∞x faster |
| File Lock Check | 2-4s | < 50ms (database) | 40-80x faster |
| Change Broadcast | 2-4s | < 50ms (database) | 40-80x faster |
| Agent Messaging | 2-4s | < 50ms (database) | 40-80x faster |
| Status Sync | 2-6s | < 50ms (database) | 40-120x faster |
| Context Isolation | Shared context | Full context × N agents (2-5) | 2-5×x context capacity |

## Implementation Strategy

### Multi-Terminal Database Coordination
- **Separate Claude Code processes** for true context isolation and parallel execution
- **Database-backed coordination** using existing proven infrastructure
- **Cross-session MCP tools** for coordination between terminals
- **Zero impact** on other MCP clients (ChatGPT, Cursor, VS Code)

### Multi-Terminal Approach Benefits
1. **True parallel execution** - Each agent runs independently with full context window
2. **Process-level isolation** - Complete debugging and monitoring per terminal
3. **Database coordination** - Proven, reliable cross-session communication
4. **Context scaling** - Total context = context_per_agent × N agents (where N = 2-5)
5. **Familiar interface** - Each terminal works like standard Claude Code session

### Implementation Phases
1. **Virtual User ID Parsing** - Implement session detection from virtual user ID pattern
2. **Cross-Session Tools** - Add coordination tools that work across terminals
3. **Database Integration** - Leverage existing session management schema
4. **Terminal Orchestration** - Test coordination between multiple Claude Code processes

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
    name VARCHAR NOT NULL,  -- Scalable: 'planner', 'impl_a', 'impl_b', 'impl_c', 'impl_d'
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

## Implementation Updates from Claude Code MCP

### Connection Architecture
Based on our successful Claude Code MCP implementation:

```python
# HTTP v2 Transport Endpoint (proven to work)
@mcp_router.post("/v2/{client_name}/{user_id}")
async def handle_http_v2_transport(client_name: str, user_id: str, request: Request):
    # Direct backend routing - 50-75% faster than SSE
    # Parse session info from user_id for multi-agent support
```

### Protocol Considerations
1. **Transport**: Always use HTTP transport with `--transport http` flag
2. **URL Pattern**: `/mcp/v2/claude/{user_id}` for direct backend connection
3. **Capabilities**: Must advertise tool support in initialize response
4. **Authentication**: User ID in URL is simpler than OAuth for initial implementation

### Multi-Terminal Connection Commands
```bash
# Terminal 1: Planning Agent (full context window)
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__planner

# Scalable Implementation Agents (2-5 total agents)
# Terminal 2: Implementation Agent A (full context window)
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_a

# Terminal 3: Implementation Agent B (full context window) 
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_b

# Terminal 4-5: Additional Implementation Agents for large projects
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_c
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_d

# Each terminal provides:
# 1. Dedicated monitoring and debugging
# 2. Full context window for the agent
# 3. Independent process execution
# 4. Coordinated file access via MCP tools
```

### Implementation Benefits Over Previous Approaches
- **True parallel execution** - Multiple Claude Code processes with full context each
- **Process-level isolation** - Complete debugging and monitoring per terminal
- **Database coordination** - Proven, reliable cross-session communication
- **Context scaling** - Total effective context = context × N agents (2-5 scalable architecture)
- **Familiar interface** - Each terminal works like standard Claude Code
- **Existing infrastructure** - Leverages working database schema and MCP transport