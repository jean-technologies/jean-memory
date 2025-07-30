# Claude Code Multi-Agent Implementation Guide

## Implementation Overview

This guide provides a practical roadmap for implementing the Claude Code multi-agent workflow with minimal risk and maximum alignment with user needs.

## Implementation Strategy: Minimal & Isolated

### Core Principles
1. **Claude Code Exclusive** - Zero impact on other MCP clients
2. **Minimal Changes** - Leverage existing infrastructure 
3. **User Workflow Focused** - Align with the 5-phase user experience
4. **Performance First** - 40-1200x speed improvements for coordination

## Phase-by-Phase Implementation

### Phase 1: Session Detection & Routing (Week 1)

**Goal**: Enable session-aware MCP routing without breaking existing functionality

```python
# app/routing/mcp.py - Enhanced routing
@mcp_router.post("/v2/{client_name}/{user_id}")
async def handle_http_v2_transport(client_name: str, user_id: str, request: Request):
    # Parse session info from user_id if present
    session_info = parse_session_info(user_id)
    if session_info and client_name == "claude code":
        request.state.session_info = session_info
    
    # Continue with existing logic...
```

**Testing**: Verify standard Claude Code connections work unchanged

### Phase 2: Google ADK Integration (Week 1)

**Goal**: Set up fast coordination infrastructure

```bash
# Setup Google ADK Express Mode (5 minutes)
# 1. Sign up at https://console.cloud.google.com/expressmode
# 2. Create Agent Engine
# 3. Get API credentials
```

```python
# Basic ADK service initialization
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()

# Session state structure for user workflow
session_state_template = {
    "task_list": [],           # Phase 1: Task Input
    "task_analysis": {},       # Phase 2: Planning results  
    "task_assignments": {},    # Phase 3: Distribution
    "file_locks": {},          # Phase 4: Execution coordination
    "agent_status": {},        # Phase 4: Progress tracking
    "completion_status": {}    # Phase 5: Final status
}
```

### Phase 3: Core Coordination Tools (Week 2)

**Goal**: Implement tools that support the user workflow phases

#### Planning Phase Tools
```python
@mcp.tool(description="[Planning] Analyze task conflicts and dependencies")
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Phase 2: Intelligent Planning - Analyze collision potential"""
    # Codebase analysis for file dependencies
    # Task dependency detection
    # Optimal distribution strategy
    return {
        "conflicts": [],
        "dependencies": {},
        "recommended_sequence": []
    }
```

#### Execution Coordination Tools  
```python
@mcp.tool(description="[Execution] Check what other agents are working on")
async def check_agent_status() -> Dict:
    """Phase 4: Real-time coordination"""
    # Fast session state lookup (1-5ms)
    
@mcp.tool(description="[Execution] Claim files to prevent conflicts") 
async def claim_file_lock(file_paths: List[str]) -> Dict:
    """Phase 4: Collision prevention (1-5ms response)"""
    # ADK-powered file locking
    
@mcp.tool(description="[Execution] Share completion status")
async def sync_progress(task_id: str, status: str) -> Dict:
    """Phase 4: Progress tracking (5-50ms response)"""
    # Real-time status updates
```

### Phase 4: Conditional Tool Loading (Week 2)

**Goal**: Session tools only appear for Claude Code multi-agent sessions

```python
# app/clients/claude.py - Enhanced Claude Profile
class ClaudeProfile(BaseClientProfile):
    def get_tools_schema(self, include_annotations: bool = False):
        # Standard tools (unchanged)
        tools = [jean_memory_tool, store_document_tool]
        
        # Add session tools only for multi-agent sessions
        user_id = user_id_var.get()
        if user_id and "__session__" in user_id:
            session_tools = [
                analyze_task_conflicts_tool,
                check_agent_status_tool, 
                claim_file_lock_tool,
                sync_progress_tool
            ]
            tools.extend(session_tools)
            
            # Add session context to tool descriptions
            session_name = user_id.split("__")[2]
            agent_id = user_id.split("__")[3]
            tools[0]["description"] += f"\n🤖 SESSION: '{session_name}' | AGENT: '{agent_id}'"
        
        return tools
```

## User Experience Implementation

### Connection URLs
```bash
# Standard Mode (updated based on implementation findings)
claude mcp add --transport http jean-memory https://api.jeanmemory.com/mcp/v2/claude/{user_id}

# Multi-Agent Session Mode  
claude mcp add --transport http jean-memory-{agent_id} https://api.jeanmemory.com/mcp/v2/claude/{user_id}__session__{session_name}__{agent_id}

# Example: Research Agent
claude mcp add --transport http jean-memory-research https://api.jeanmemory.com/mcp/v2/claude/user123__session__webscraper__research

# Example: Implementation Agent  
claude mcp add --transport http jean-memory-implementation https://api.jeanmemory.com/mcp/v2/claude/user123__session__webscraper__implementation
```

**Implementation Note**: Based on our Claude Code MCP testing, the `claude mcp add --transport http` command is more reliable than `npx install-mcp`. The HTTP transport provides better performance and stability.

### Workflow Integration

**Phase 1: Task Input (30 seconds)**
- User provides task list to planning agent
- Tasks stored in session state for all agents to access

**Phase 2: Planning (2-3 minutes)**  
- Planning agent uses `@analyze_task_conflicts` tool
- Codebase analysis and dependency detection
- Results stored in shared session state

**Phase 3: Distribution (1 minute)**
- System generates specialized prompts per agent
- Task assignments stored in session state
- Human approval workflow

**Phase 4: Coordinated Execution (Duration varies)**
- All agents equipped with coordination tools:
  - `@check_agent_status` - See current work (1-5ms)
  - `@claim_file_lock` - Prevent conflicts (1-5ms)  
  - `@sync_progress` - Share status (5-50ms)
- Real-time collision prevention at every step

**Phase 5: Completion (5 minutes)**
- Progress tracking via session state
- Completion verification
- Final review workflow

## Testing Strategy

### Unit Tests
```python
def test_session_detection():
    # Test virtual user ID parsing
    # Test standard mode unaffected
    
def test_coordination_tools():
    # Test file locking performance
    # Test conflict detection
    # Test status synchronization
```

### Integration Tests  
```python
def test_multi_agent_workflow():
    # Test 2+ agents in same session
    # Test shared memory access
    # Test coordination tool interactions
```

### Performance Tests
```python
def test_coordination_speed():
    # Verify < 50ms coordination operations
    # Compare against current 2-6s operations
    # Benchmark with multiple concurrent agents
```

## Rollout Plan

### Week 1: Foundation
- [ ] Google ADK setup and testing
- [ ] Session detection implementation
- [ ] Basic coordination tools
- [ ] MCP integration testing

### Week 2: Enhancement  
- [ ] Full coordination tool suite
- [ ] Performance optimization
- [ ] Multi-agent testing
- [ ] Documentation

### Week 3: Deployment
- [ ] Beta user testing
- [ ] Performance monitoring
- [ ] Feedback integration
- [ ] Production deployment

## Success Metrics

### Performance Targets
- **File operations**: 400-4000x faster (2-4s → 1-5ms)
- **Agent communication**: 200-4000x faster (2-4s → 1-10ms)  
- **Status synchronization**: 40-1200x faster (2-6s → 5-50ms)

### User Experience Goals
- **Zero conflicts**: Intelligent file collision prevention
- **Real-time coordination**: Sub-second agent synchronization
- **Familiar interface**: Each agent works like normal Claude Code
- **Seamless workflow**: Task input to completion without manual coordination

### Quality Gates
- All existing MCP clients unaffected
- Standard Claude Code mode unchanged  
- Session tools only appear in multi-agent mode
- < 100ms response time for all coordination operations

### Implementation Lessons from Claude Code MCP
Based on our recent implementation experience:
1. **Protocol Compliance**: Ensure MCP initialize response includes proper capabilities object - critical for tool discovery
2. **Transport Selection**: HTTP transport is significantly more reliable than stdio/SSE approaches
3. **URL Structure**: Direct user ID in URL works immediately; OAuth adds complexity but improves security
4. **Testing Strategy**: Test with actual Claude Code client early - protocol compliance issues aren't always visible in unit tests

This implementation guide ensures the technical architecture directly supports the user workflow while maintaining system stability and performance.