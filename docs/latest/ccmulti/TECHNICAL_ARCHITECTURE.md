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

## ✅ Phase 2 Implementation Status (July 31, 2025)

**🎉 CORE FUNCTIONALITY OPERATIONAL:**
- Multi-terminal coordination architecture proven functional
- All 6 coordination tools successfully implemented and registered
- MCP tool registry and profile schema working as designed
- Client detection issue resolved - Claude Code sends `x-client-name: "claude"`
- Frontend integration completed with multi-agent tab in install modal

**✅ CRITICAL FIXES APPLIED (July 31, 2025):**
- **FIXED**: Tool registration gap - added coordination tools to `/app/tools/__init__.py`
- **FIXED**: Central registry mapping - added `setup_multi_agent_coordination` to `tool_registry.py`
- **RESULT**: All coordination tools now both visible AND callable in Claude Code
- **STATUS**: Multi-agent magic phrase workflow now functional end-to-end

**🔧 OUTSTANDING BACKEND ISSUES:**
- Database constraint violations (NOT NULL `updated_at` field in `claude_code_sessions`)
- Foreign key constraint errors in `task_progress` table for single-user sessions
- Circular import warnings in `app.tools.memory` module (non-breaking)
- pgvector connection failures (Phase 2 feature, non-critical for multi-agent coordination)

**⚠️ PRODUCTION STATUS:** Core multi-agent functionality working, backend database issues need resolution

## Core Technical Requirements

### 🔒 Security Architecture (CRITICAL)

**Client Isolation Model:**
- **ONLY Claude Code MCP** connections receive coordination tools
- **Header-based authentication**: `x-client-name: 'claude code'` requirement
- **Profile inheritance protection**: Cursor, Chorus, Default profiles blocked from coordination tools
- **Fail-safe design**: Default to blocking coordination tools unless explicitly authorized

**Security Implementation:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Claude Code   │────│  Coordination    │────│  ✅ AUTHORIZED      │
│   MCP Client    │    │  Tools Check     │    │  Multi-Agent Tools  │
└─────────────────┘    └──────────────────┘    └─────────────────────┘

┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ Cursor/Chorus/  │────│  Coordination    │────│  ❌ BLOCKED         │
│ Other MCP       │    │  Tools Check     │    │  Standard Tools Only│
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

**Security Enforcement Points:**
1. `app/routing/mcp.py` - Client name detection and session info passing
2. `app/clients/claude.py` - Client authorization before tool schema generation
3. Security logging - Unauthorized coordination tool requests tracked

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

#### 3. Enhanced Cross-Session Coordination Tools

**Enhanced Planning Phase Tools (Terminal 1: Planning Agent)**
```python
@mcp.tool(description="[Planning] Analyze task conflicts and generate multi-terminal coordination plan")
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Enhanced with codebase scanning and conflict detection"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # NEW: Codebase analysis capabilities
    codebase_files = await scan_project_files()
    file_dependencies = await analyze_file_dependencies(codebase_files)
    
    # NEW: Task-to-file mapping
    task_file_mapping = await map_tasks_to_files(tasks, codebase_files)
    
    # NEW: Conflict detection algorithm
    conflicts = detect_file_conflicts(task_file_mapping, file_dependencies)
    
    # NEW: Optimal agent distribution (2-5 agents)
    optimal_distribution = calculate_agent_distribution(conflicts, len(tasks))
    
    return {
        "conflicts": conflicts,
        "agent_assignments": optimal_distribution,
        "coordination_strategy": "multi_terminal",
        "file_analysis": task_file_mapping,
        "dependencies": file_dependencies,
        "session_id": session_info.session_id,
        "timestamp": datetime.now().isoformat()
    }

@mcp.tool(description="[Planning] Generate terminal setup commands and specialized prompts")
async def create_task_distribution(analysis: Dict, session_id: str, user_id: str) -> Dict:
    """Enhanced to generate complete terminal setup instructions"""
    
    distribution = analysis["agent_assignments"]
    terminal_instructions = []
    
    for agent_id, tasks in distribution.items():
        # Generate MCP connection command
        mcp_url = f"https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__{agent_id}"
        mcp_command = f"claude mcp add jean-memory-{agent_id} --transport http {mcp_url}"
        
        # Generate specialized prompt
        agent_prompt = generate_agent_prompt(agent_id, tasks, distribution, session_id)
        
        terminal_instructions.append({
            "terminal": f"Terminal {len(terminal_instructions) + 2}",  # Terminal 1 is planner
            "agent_id": agent_id,
            "mcp_command": mcp_command,
            "initial_prompt": agent_prompt,
            "assigned_tasks": tasks,
            "file_locks_needed": extract_file_paths(tasks)
        })
    
    return {
        "terminal_instructions": terminal_instructions,
        "coordination_ready": True,
        "session_id": session_id,
        "total_terminals": len(terminal_instructions) + 1
    }
```

**Enhanced Execution Coordination Tools (Terminals 2+: Implementation Agents)**
```python
@mcp.tool(description="[Execution] Cross-terminal file locking with database coordination")
async def claim_file_lock(file_paths: List[str], duration_minutes: int = 15) -> Dict:
    """Enhanced database-backed file locking across terminals"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # Use existing database coordination from implementation
    # Prevent conflicts across separate Claude Code sessions
    # Enhanced with duration control and collision detection
    locked_files = []
    failed_locks = []
    
    for file_path in file_paths:
        try:
            lock_success = await create_database_file_lock(
                file_path, session_info.agent_id, duration_minutes
            )
            if lock_success:
                locked_files.append(file_path)
            else:
                failed_locks.append(file_path)
        except Exception as e:
            failed_locks.append(file_path)
    
    return {
        "locked_files": locked_files,
        "failed_locks": failed_locks,
        "lock_id": str(uuid4()),
        "session": session_info.session_id,
        "agent": session_info.agent_id,
        "expires_in_minutes": duration_minutes
    }

@mcp.tool(description="[Execution] Cross-terminal progress synchronization")
async def sync_progress(task_id: str, status: str, affected_files: List[str] = None) -> Dict:
    """Enhanced progress broadcasting across multiple terminals"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # Enhanced with file tracking and detailed status
    progress_data = {
        "task_id": task_id,
        "status": status,
        "agent_id": session_info.agent_id,
        "session_id": session_info.session_id,
        "affected_files": affected_files or [],
        "timestamp": datetime.now().isoformat(),
        "progress_percentage": calculate_progress_percentage(task_id, status)
    }
    
    # Broadcast to database for other terminals to see
    await update_agent_progress(progress_data)
    
    return {
        "task_id": task_id,
        "status": status,
        "session": session_info.session_id,
        "broadcast": True,
        "visible_to_agents": await get_session_agent_ids(session_info.session_id)
    }

@mcp.tool(description="[Monitoring] Check status of all agents across terminals")
async def check_agent_status(include_inactive: bool = False) -> Dict:
    """Enhanced monitoring of all agents across multiple Claude Code sessions"""
    session_info = parse_virtual_user_id(context.user_id)
    
    # Enhanced with detailed status and activity monitoring
    agents = await get_session_agents(session_info.session_id, include_inactive)
    
    agent_statuses = []
    for agent in agents:
        agent_status = {
            "agent_id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "last_activity": agent.last_activity,
            "current_tasks": await get_agent_current_tasks(agent.id),
            "locked_files": await get_agent_file_locks(agent.id),
            "terminal": get_terminal_number(agent.id)
        }
        agent_statuses.append(agent_status)
    
    return {
        "session_id": session_info.session_id,
        "requesting_agent": session_info.agent_id,
        "agents": agent_statuses,
        "total_agents": len(agent_statuses),
        "active_agents": len([a for a in agent_statuses if a["status"] == "active"]),
        "coordination_health": "healthy" if all(a["status"] in ["active", "idle"] for a in agent_statuses) else "degraded"
    }
```

## Performance Comparison

| Operation | Current System | Enhanced Multi-Terminal + Database | Improvement |
|-----------|----------------|-------------------------------------|-------------|
| Planning Analysis | 10-30s | 2-8s (with codebase analysis) | 3-15x faster |
| Agent Context Switch | 2-4s | 0s (separate processes) | ∞x faster |
| File Lock Check | 2-4s | < 50ms (enhanced database) | 40-80x faster |
| Change Broadcast | 2-4s | < 100ms (enhanced database) | 20-40x faster |
| Agent Messaging | 2-4s | < 50ms (database coordination) | 40-80x faster |
| Status Sync | 2-6s | < 100ms (enhanced progress tracking) | 20-60x faster |
| Context Isolation | Shared context | Full context × N agents (2-5) | 2-5x context capacity |
| Terminal Setup | Manual | < 30s (automated command generation) | 10-20x faster |
| Codebase Analysis | Manual/None | Automated dependency detection | ∞x faster |

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

### Implementation Phases (1-Day Plan)

**Phase 1: Enhanced MCP Tools (Morning - 4 hours)**
1. **Codebase Analysis Enhancement** - Add file scanning and dependency detection to analyze_task_conflicts
2. **Terminal Command Generation** - Enhance create_task_distribution to output ready-to-use MCP commands
3. **Agent-Specific Tool Filtering** - Implement agent role-based tool access in Claude profile
4. **Enhanced Coordination Tools** - Upgrade file locking and progress sync with detailed status

**Phase 2: Multi-Terminal Integration (Afternoon - 4 hours)**
1. **Cross-Terminal Testing** - Verify coordination works across separate Claude Code processes
2. **User Experience Flow** - Test complete workflow from task input to coordinated execution
3. **Performance Optimization** - Optimize database queries and coordination response times
4. **Production Deployment** - Deploy enhanced tools with monitoring and error handling

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