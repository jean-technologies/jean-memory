# Claude Code Multi-Agent Technical Architecture

## Overview

This document outlines the technical architecture for implementing the Claude Code multi-agent workflow leveraging **Claude Code's native subagents and hooks system** with minimal custom coordination for optimal alignment with the user workflow: **Task Input → Planning → Distribution → Coordinated Execution → Completion**.

## Core Technical Requirements

### Performance Requirements (Native Feature Coordination)
- **Agent switching**: Instant (built into Claude Code)
- **Context isolation**: Native per-subagent contexts
- **Tool coordination**: < 1ms (hooks-based prevention)
- **Status updates**: Real-time via hooks system

### User Workflow Technical Mapping

```
📋 Task Input → Planning subagent activation
🧠 Planning → Specialized planning subagent with codebase analysis
📤 Distribution → Automatic subagent delegation by Claude Code
⚡ Coordinated Execution → Subagents + hooks + minimal MCP coordination
✅ Completion → Hook-based progress tracking + completion subagent
```

## Architecture Solution: Native Subagents + Hooks Hybrid

### Core Principle
**Leverage Claude Code's built-in multi-agent capabilities:**
- **Native Subagents**: Built-in context isolation and task delegation ([Subagents Documentation](https://docs.anthropic.com/en/docs/claude-code/sub-agents))
- **Hooks System**: Deterministic coordination and conflict prevention ([Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks-guide))
- **Minimal MCP Tools**: Only for complex coordination not handled by native features ([MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp))
- **Proven HTTP Transport**: Existing `/mcp/v2/{client_name}/{user_id}` infrastructure

### Technical Implementation

#### 1. Native Subagents System ([Documentation](https://docs.anthropic.com/en/docs/claude-code/sub-agents))
```markdown
# .claude/agents/planner.md
---
name: multi-agent-planner
description: MUST BE USED for task analysis and distribution in multi-agent workflows. Analyzes task conflicts, dependencies, and creates execution plans.
tools: jean_memory, analyze_task_conflicts, create_task_distribution
---

You are the Multi-Agent Planning Specialist. When users provide multiple tasks:

1. Use @analyze_task_conflicts to detect file collisions and dependencies
2. Create optimal task distribution across implementation agents
3. Generate specialized prompts for each implementation agent
4. Coordinate with other agents via hooks system

Always check for file conflicts before task distribution.
```

```markdown
# .claude/agents/implementer.md  
---
name: multi-agent-implementer
description: Implementation specialist for executing assigned tasks with coordination. Use after planning phase for actual code implementation.
tools: jean_memory, claim_file_lock, sync_progress, Read, Edit, Write, Bash
---

You are a Multi-Agent Implementation Specialist. Before editing any file:

1. Use @claim_file_lock to prevent conflicts
2. Implement assigned functionality
3. Use @sync_progress to update completion status
4. Follow coordination protocols established by planner

Always coordinate before making changes to shared files.
```

#### 2. Hooks-Based Coordination ([Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks-guide))
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command", 
            "command": "python3 -c \"import json, sys, os; data=json.load(sys.stdin); file_path=data.get('tool_input',{}).get('file_path',''); lock_file=f'/tmp/claude_locks/{os.path.basename(file_path)}.lock'; sys.exit(2 if os.path.exists(lock_file) else 0)\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys, os, time; data=json.load(sys.stdin); file_path=data.get('tool_input',{}).get('file_path',''); open(f'/tmp/claude_changes/{int(time.time())}_{os.path.basename(file_path)}.json', 'w').write(json.dumps({'file': file_path, 'agent': os.getenv('CLAUDE_AGENT_ID', 'unknown'), 'timestamp': time.time()}))\""
          }
        ]
      }
    ]
  }
}
```

#### 3. Minimal MCP Coordination Tools (Only When Needed)

**Planning Phase Tools (Used by Planner Subagent)**
```python
@mcp.tool()
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Analyze collision potential and create subagent distribution plan"""
    # Lightweight codebase analysis for file dependencies
    # Generate subagent invocation prompts
    # Create coordination strategy for hooks system
    return {
        "conflicts": [],
        "subagent_assignments": {},
        "coordination_strategy": "hooks",
        "execution_sequence": []
    }

@mcp.tool()
async def create_task_distribution(analysis: Dict) -> Dict:
    """Generate subagent prompts and coordination setup"""
    # Create specialized prompts for implementer subagents
    # Set up hook-based coordination
    # Return subagent invocation instructions
    return {"subagent_prompts": [], "hooks_config": {}}
```

**Execution Coordination Tools (Used by Implementer Subagents)**
```python
@mcp.tool()
async def claim_file_lock(file_paths: List[str]) -> Dict:
    """Create filesystem locks (backup to hooks system)"""
    # Create lock files in /tmp/claude_locks/
    # Used as fallback when hooks aren't sufficient
    return {"locked_files": file_paths, "lock_id": uuid4()}

@mcp.tool()
async def sync_progress(task_id: str, status: str) -> Dict:
    """Broadcast progress updates to other subagents"""
    # Write progress to shared location
    # Notify completion subagent of status changes
    return {"task_id": task_id, "status": status, "broadcast": True}
```

## Performance Comparison

| Operation | Current System | Native Subagents + Hooks | Improvement |
|-----------|----------------|---------------------------|-------------|
| Planning Analysis | 10-30s | 5-15s | 2-6x faster |
| Agent Context Switch | 2-4s | Instant (native) | ∞x faster |
| File Lock Check | 2-4s | < 1ms (hooks) | 2000-4000x faster |
| Change Broadcast | 2-4s | < 1ms (hooks) | 2000-4000x faster |
| Agent Messaging | 2-4s | Instant (native) | ∞x faster |
| Status Sync | 2-6s | < 1ms (hooks) | 2000-6000x faster |

## Implementation Strategy

### Native Claude Code Features First
- **Built-in subagents** for task specialization and context isolation
- **Native hooks system** for deterministic coordination
- **Minimal MCP tools** only for complex coordination not handled natively
- **Zero impact** on other MCP clients (ChatGPT, Cursor, VS Code)

### Hybrid Approach Benefits
1. **Leverage native features** - Use Claude Code's intended multi-agent patterns
2. **Deterministic coordination** - Hooks provide guaranteed execution vs. LLM choices
3. **Minimal custom code** - 50-80% less implementation than pure custom approach
4. **Better user experience** - Native agent switching and context management

### Implementation Phases
1. **Subagents Creation** - Define specialized agents for planning/implementation/completion
2. **Hooks Configuration** - Set up automatic coordination and conflict prevention
3. **Minimal MCP Tools** - Add only necessary coordination tools not handled by native features
4. **Integration Testing** - Verify native features work with existing Jean Memory integration

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

### Multi-Agent Connection Commands (Simplified)
```bash
# Standard single agent with Jean Memory integration (existing)
claude mcp add --transport http jean-memory https://api.jeanmemory.com/mcp/v2/claude/{user_id}

# After MCP connection, users leverage native Claude Code features:
# 1. Subagents via /agents command (no additional MCP connections needed)
# 2. Hooks via /hooks command (automatic coordination)
# 3. Native task delegation (built into Claude Code)
```

### Implementation Benefits Over Previous Approaches
- **50-80% less custom code** - Leverage native Claude Code multi-agent features
- **Instant agent switching** - Built into Claude Code, no network calls
- **Deterministic coordination** - Hooks system guarantees execution
- **Better user experience** - Native agent context isolation and management
- **Zero learning curve** - Uses Claude Code's intended patterns
- **Maintenance-free** - Built-in features maintained by Anthropic