# Claude Code Multi-Agent Implementation Guide

## Implementation Overview

This guide provides a practical roadmap for implementing the Claude Code multi-agent workflow using **multi-terminal coordination** with database-backed cross-session communication.

## ✅ Phase 1 Status: COMPLETE (January 2025)

**Implemented Components:**
- Virtual user ID parsing: `{user_id}__session__{session_id}__{agent_id}`
- Database session registration in `claude_code_sessions` and `claude_code_agents` tables
- Session-aware Claude profile with multi-agent context detection
- Multi-terminal MCP connections via HTTP v2 transport
- Tested with planner and implementer agents in separate terminals

## 🚧 Phase 2 Status: IN PROGRESS (January 2025)

**✅ Completed Implementation:**
- All 5 coordination tools implemented in `/app/tools/coordination.py`:
  - `analyze_task_conflicts` - Task analysis and agent distribution planning
  - `create_task_distribution` - Terminal command and prompt generation
  - `claim_file_lock` - Cross-session file locking
  - `sync_progress` - Progress broadcasting across terminals
  - `check_agent_status` - Agent monitoring
- Tools registered in `tool_registry.py`
- Claude profile schema updated with coordination tool definitions
- Database schema deployed to Supabase with 4 coordination tables
- MCP decorators added to all coordination functions
- Multi-terminal MCP connections tested (3 terminals: planner + 2 implementers)

**❌ Current Blocking Issue:**
- **Tools Not Appearing in MCP Interface**: Despite being implemented and registered, coordination tools are not showing up in Claude Code's tools list
- **Root Cause**: Unknown - tools are properly defined in Claude profile schema and registered in tool registry
- **Debug Status**: Added logging to diagnose agent_id parsing and tool schema generation

**🔍 Investigation Results:**
- Tools schema contains all 5 coordination tools with proper MCP schemas
- Agent ID parsing logic appears correct for virtual user ID pattern
- MCP connections established successfully but only show 2 tools (`jean_memory`, `store_document`)
- Tool registry contains all coordination functions
- No obvious filtering or conditional logic preventing tool exposure

**Next Steps to Unblock:**
1. **Debug Deployment**: Check server logs for tool schema generation errors
2. **MCP Protocol Investigation**: Verify if tools are being filtered during MCP protocol transmission
3. **Schema Validation**: Ensure tool schemas pass MCP validation requirements
4. **Alternative Approach**: Consider bypassing tool schema and using direct function calls if MCP exposure fails

This guide provides a practical roadmap for implementing the Claude Code multi-agent workflow leveraging **native Claude Code subagents and hooks** with minimal custom development required.

## Implementation Strategy: Native Features First

### Core Principles
1. **Native Claude Code Features** - Use built-in subagents and hooks system
2. **Minimal Custom Development** - 50-80% less code than pure custom approach
3. **User Workflow Focused** - Align with the 5-phase user experience
4. **Instant Performance** - Native agent switching and hooks-based coordination
5. **Zero Learning Curve** - Uses Claude Code's intended multi-agent patterns

## Phase-by-Phase Implementation

### Phase 1: Subagents Creation (Day 1)

**Goal**: Create specialized subagents for multi-agent workflow using Claude Code's native system

**Reference**: [Claude Code Subagents Documentation](https://docs.anthropic.com/en/docs/claude-code/sub-agents)

```bash
# Use Claude Code's native /agents command to create subagents
# Run this in your project directory with Claude Code active

/agents
# Select "Create New Agent" -> "Project-level"
# Create the following agents:
```

**Planner Subagent**
```markdown
# .claude/agents/multi-agent-planner.md
---
name: multi-agent-planner
description: MUST BE USED for task analysis and multi-agent coordination. Analyzes task conflicts, dependencies, and creates execution plans for 2-5 implementation agents based on project complexity.
tools: jean_memory, analyze_task_conflicts, create_task_distribution
---

You are the Multi-Agent Planning Specialist for coordinated development workflows.

When users provide multiple tasks or complex multi-step requirements:

1. **Task Analysis**: Use @analyze_task_conflicts to detect file collisions and dependencies
2. **Agent Assignment**: Determine optimal task distribution across 1-4 implementation agents (scalable 2-5 agent architecture)  
3. **Coordination Setup**: Configure hooks-based coordination for conflict prevention
4. **Execution Planning**: Generate specialized prompts for each implementation subagent

CRITICAL: Always analyze for file conflicts before distributing tasks to prevent merge conflicts.

Your responses should include:
- Conflict analysis results
- Recommended agent assignments
- Coordination strategy
- Next steps for implementation agents
```

**Implementation Subagent**
```markdown
# .claude/agents/multi-agent-implementer.md
---
name: multi-agent-implementer  
description: Implementation specialist for coordinated multi-agent development. Use after planning phase for executing assigned development tasks with conflict prevention.
tools: jean_memory, claim_file_lock, sync_progress, Read, Edit, Write, Bash, Grep, Glob
---

You are a Multi-Agent Implementation Specialist focused on coordinated development.

Before making any file changes:

1. **Coordination Check**: Use @claim_file_lock to prevent conflicts with other agents
2. **Implementation**: Execute your assigned functionality following the coordination plan
3. **Progress Updates**: Use @sync_progress to notify other agents of completion status
4. **Quality Assurance**: Ensure changes integrate properly with concurrent work

CRITICAL: Always coordinate file access to prevent conflicts in multi-agent scenarios.

Follow the coordination protocols established by the planner agent.
```

### Phase 2: Hooks Configuration (Day 1)

**Goal**: Set up automatic coordination and conflict prevention using Claude Code's hooks system

**Reference**: [Claude Code Hooks Documentation](https://docs.anthropic.com/en/docs/claude-code/hooks-guide)

```bash
# Use Claude Code's native /hooks command
/hooks
# Configure the following hooks:
```

**File Conflict Prevention Hook**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 -c \"import json, sys, os, time; data=json.load(sys.stdin); file_path=data.get('tool_input',{}).get('file_path',''); lock_dir='/tmp/claude_locks'; os.makedirs(lock_dir, exist_ok=True); lock_file=f'{lock_dir}/{os.path.basename(file_path)}.lock'; sys.exit(2 if os.path.exists(lock_file) else os.mknod(lock_file))\""
          }
        ]
      }
    ]
  }
}
```

**Change Notification Hook**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write",
        "hooks": [
          {
            "type": "command", 
            "command": "python3 -c \"import json, sys, os, time; data=json.load(sys.stdin); file_path=data.get('tool_input',{}).get('file_path',''); change_dir='/tmp/claude_changes'; os.makedirs(change_dir, exist_ok=True); change_file=f'{change_dir}/{int(time.time())}_{os.path.basename(file_path)}.json'; open(change_file, 'w').write(json.dumps({'file': file_path, 'agent': os.getenv('CLAUDE_AGENT_TYPE', 'unknown'), 'timestamp': time.time()}))\""
          }
        ]
      }
    ]
  }
}
```

### Phase 3: Minimal MCP Coordination Tools (Day 2)

**Goal**: Add only essential coordination tools not handled by native features

**Reference**: [Claude Code MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)

#### Planning Phase MCP Tools
```python
@mcp.tool(description="[Planning] Analyze task conflicts and create subagent coordination plan")
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Used by planner subagent for task analysis and agent assignment"""
    
    # Lightweight codebase analysis for file dependencies
    # Generate subagent invocation prompts
    # Create coordination strategy using hooks system
    analysis = {
        "conflicts": [],
        "subagent_assignments": {},
        "coordination_strategy": "hooks",
        "execution_sequence": [],
        "timestamp": datetime.now().isoformat()
    }
    
    return analysis

@mcp.tool(description="[Planning] Generate subagent prompts and coordination setup")
async def create_task_distribution(analysis: Dict) -> Dict:
    """Create specialized prompts for implementer subagents"""
    
    # Generate subagent invocation instructions
    # Set up hooks-based coordination 
    # Return ready-to-use subagent prompts
    return {
        "subagent_prompts": [],
        "hooks_config": {},
        "coordination_ready": True
    }
```

#### Execution Coordination MCP Tools
```python
@mcp.tool(description="[Execution] Create file locks as backup to hooks system")
async def claim_file_lock(file_paths: List[str]) -> Dict:
    """Fallback file locking for complex coordination scenarios"""
    
    # Create lock files in /tmp/claude_locks/
    # Used when hooks system needs additional coordination
    lock_dir = Path("/tmp/claude_locks")
    lock_dir.mkdir(exist_ok=True)
    
    locked_files = []
    for file_path in file_paths:
        lock_file = lock_dir / f"{Path(file_path).name}.lock"
        if not lock_file.exists():
            lock_file.touch()
            locked_files.append(file_path)
    
    return {"locked_files": locked_files, "lock_id": str(uuid.uuid4())}

@mcp.tool(description="[Execution] Broadcast progress updates between subagents") 
async def sync_progress(task_id: str, status: str) -> Dict:
    """Share completion status across subagents"""
    
    # Write progress to shared location for other subagents
    progress_dir = Path("/tmp/claude_progress")
    progress_dir.mkdir(exist_ok=True)
    
    progress_file = progress_dir / f"{task_id}.json"
    progress_file.write_text(json.dumps({
        "task_id": task_id,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "agent_type": "implementer"
    }))
    
    return {"task_id": task_id, "status": status, "broadcast": True}
```

### Phase 4: MCP Tool Integration (Day 2-3)

**Goal**: Add minimal coordination tools to existing Claude profile

```python
# app/clients/claude.py - Enhanced Claude Profile (minimal changes)
class ClaudeProfile(BaseClientProfile):
    def get_tools_schema(self, include_annotations: bool = False):
        # Standard tools (unchanged)
        tools = [jean_memory_tool, store_document_tool]
        
        # Add coordination tools for all Claude Code sessions
        # (Subagents will automatically inherit these tools)
        coordination_tools = [
            analyze_task_conflicts_tool,      # Planning phase (used by planner subagent)
            create_task_distribution_tool,    # Planning phase (used by planner subagent)
            claim_file_lock_tool,             # Execution coordination (used by implementer subagents)
            sync_progress_tool,               # Progress tracking (used by implementer subagents)
        ]
        tools.extend(coordination_tools)
        
        # Add multi-agent context indicator
        tools[0]["description"] += f"\n🤖 MULTI-AGENT READY: Subagents available via /agents command"
        
        return tools
```

**Subagent Tool Restrictions**
```markdown
# Planner subagent tools are automatically restricted via:
tools: jean_memory, analyze_task_conflicts, create_task_distribution

# Implementer subagent tools are automatically restricted via:  
tools: jean_memory, claim_file_lock, sync_progress, Read, Edit, Write, Bash, Grep, Glob
```

## User Experience Implementation

### Single MCP Connection (Simplified)
```bash
# Single Jean Memory connection provides all multi-agent capabilities (2-5 agent scalable architecture)
claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}

# After connection, users access multi-agent features natively:
# 1. /agents command - Create and manage subagents (https://docs.anthropic.com/en/docs/claude-code/sub-agents)
# 2. /hooks command - Set up automatic coordination (https://docs.anthropic.com/en/docs/claude-code/hooks-guide)
# 3. Native subagent invocation - "Use the planner subagent to..."
```

**Key Advantage**: No multiple MCP connections needed. All multi-agent functionality through native Claude Code features.

### Workflow Integration (Native Subagents + Hooks)

**Phase 1: Task Input (30 seconds)**
- User provides multiple tasks in conversation
- Claude Code automatically delegates to planner subagent based on task complexity
- Native subagent context isolation begins

**Phase 2: Planning (2-3 minutes)**  
- Planner subagent uses `@analyze_task_conflicts` tool
- Lightweight codebase analysis and dependency detection
- Generates specialized prompts for implementer subagents
- Sets up hooks-based coordination strategy

**Phase 3: Distribution (30 seconds)**
- Planner subagent provides ready-to-use implementer subagent invocations
- User approves distribution plan
- No manual session management needed

**Phase 4: Coordinated Execution (Duration varies)**
- User invokes implementer subagents with specialized prompts
- Hooks system automatically prevents file conflicts (< 1ms)
- Subagents use coordination tools when hooks need additional support:
  - `@claim_file_lock` - Backup file conflict prevention
  - `@sync_progress` - Cross-subagent status updates
- Real-time collision prevention via hooks + occasional MCP tools

**Phase 5: Completion (Automatic)**
- Hooks system automatically tracks all changes
- Progress monitoring through change notification hooks  
- Final status available via completion subagent
- Optional sync to Jean Memory for long-term persistence

## Testing Strategy

### Subagent Testing
```bash
# Test subagent creation via /agents command
# Verify subagent tool restrictions work correctly
# Test subagent context isolation
# Validate native task delegation

def test_subagent_creation():
    # Test planner subagent with restricted tools
    # Test implementer subagent with coordination tools
    # Verify subagents appear in Claude Code /agents list
```

### Hooks Testing
```bash
# Test hooks configuration via /hooks command  
# Verify file conflict prevention works
# Test change notification hooks trigger correctly
# Validate hooks work with concurrent file access

def test_hooks_coordination():
    # Test PreToolUse hook prevents file conflicts
    # Test PostToolUse hook logs changes correctly
    # Verify hooks work with subagent tool calls
```

### MCP Tools Integration Testing
```python
def test_coordination_tools():
    # Test analyze_task_conflicts with planner subagent
    # Test claim_file_lock with implementer subagents
    # Test sync_progress across subagents
    # Verify tools integrate with native features
```

### End-to-End Workflow Testing
```bash
# Test complete user workflow:
# 1. Multi-task input → planner subagent activation
# 2. Task analysis → coordination plan generation  
# 3. Implementer subagent invocation → coordinated execution
# 4. Hooks prevent conflicts → completion tracking
```

## Rollout Plan (3 Days Total)

### Day 1: Native Features Setup
- [ ] Create planner and implementer subagents via /agents
- [ ] Configure conflict prevention hooks via /hooks
- [ ] Test native subagent switching and context isolation
- [ ] Verify hooks trigger correctly on file operations

### Day 2: MCP Tool Integration  
- [ ] Add minimal coordination tools to Claude profile
- [ ] Test coordination tools with subagents
- [ ] Verify tool restrictions work per subagent
- [ ] End-to-end workflow testing

### Day 3: Optimization & Deploy
- [ ] Performance optimization and error handling
- [ ] Documentation and user guides
- [ ] Production deployment with monitoring
- [ ] User feedback integration

## Success Metrics

### Performance Targets (Native Features + Hooks)
- **Agent switching**: Instant (native Claude Code feature)
- **File conflict prevention**: < 1ms (hooks-based)
- **Cross-agent coordination**: < 1ms (hooks + minimal MCP tools)
- **Context isolation**: Instant (native subagent contexts)

### User Experience Goals
- **Zero conflicts**: Automatic hooks-based collision prevention
- **Instant coordination**: Native subagent switching and communication
- **Familiar interface**: Standard Claude Code with /agents and /hooks commands
- **Seamless workflow**: Task input to completion via native delegation
- **Zero learning curve**: Uses Claude Code's intended multi-agent patterns

### Quality Gates
- All existing MCP clients unaffected
- Standard Claude Code mode unchanged  
- Subagents and hooks work with single MCP connection
- Native features perform as designed by Anthropic
- Minimal custom code required (50-80% reduction)

### Agent Scaling Architecture

**2 Agents** (Minimum):
- Simple multi-step features
- Basic coordination needs  
- 1 planner + 1 implementer
- Example: Add authentication to existing app

**3 Agents** (Optimal/Default):
- Standard complex features
- Moderate file interdependencies  
- 1 planner + 2 implementers
- Example: Build user dashboard with profile, settings, and notifications

**4-5 Agents** (Maximum):
- Large-scale feature development
- Complex system integrations
- 1 planner + 3-4 implementers
- Example: E-commerce system with cart, payments, inventory, and admin panels

### Implementation Benefits Over Previous Approaches
1. **Scalable Parallel Execution**: 2-5 Claude Code processes with full context windows each
2. **Process-Level Isolation**: Complete debugging and monitoring per terminal
3. **Database Coordination**: Proven, reliable cross-session communication
4. **Context Scaling**: Total effective context = context_per_terminal × N terminals (2-5)
5. **Familiar Interface**: Each terminal works like standard Claude Code session
6. **Existing Infrastructure**: Leverages working database schema and MCP transport
7. **Real Monitoring**: Dedicated terminal per agent enables isolated progress tracking

This multi-terminal approach ensures scalable parallel execution (2-5 agents) and process isolation while leveraging existing proven infrastructure for coordination.