# Claude Code Multi-Agent Implementation Guide (Corrected)

## Implementation Overview

This guide provides the **corrected** roadmap for implementing the Claude Code multi-agent workflow using **enhanced MCP tools with multi-terminal coordination** and database-backed cross-session communication.

## ✅ Phase 1 Status: COMPLETE (January 2025)

**Implemented Components:**
- Virtual user ID parsing: `{user_id}__session__{session_id}__{agent_id}`
- Database session registration in `claude_code_sessions` and `claude_code_agents` tables
- Session-aware Claude profile with multi-agent context detection
- Multi-terminal MCP connections via HTTP v2 transport
- All 5 coordination tools implemented and working

## 🚧 Phase 2 Status: READY FOR ENHANCEMENT (January 2025)

**What We're Building Next:**
- Enhanced codebase analysis in `analyze_task_conflicts`
- Terminal command generation in `create_task_distribution`
- Multi-terminal user experience workflow
- Agent-specific tool filtering

## Implementation Strategy: Multi-Terminal MCP Architecture

### Core Principles
1. **Security First** - Coordination tools ONLY for Claude Code MCP (`x-client-name: 'claude code'`)
2. **Client Isolation** - Never expose coordination tools to Cursor, Chorus, ChatGPT, or other MCP clients
3. **Multi-Terminal Architecture** - Separate Claude Code sessions for each agent (2-5 terminals)
4. **Enhanced MCP Tools** - Add codebase analysis and terminal command generation
5. **User Workflow Focused** - Align with the 5-phase user experience
6. **Database Coordination** - Cross-session communication via proven infrastructure
7. **Process Isolation** - Full context windows and independent monitoring per agent

## 🔒 Security Requirements

### Critical Client Isolation
- **ONLY Claude Code MCP** should receive coordination tools
- **Blocked clients**: Cursor, Chorus, ChatGPT, API users, Default profile
- **Detection mechanism**: `x-client-name: 'claude code'` header verification
- **Implementation**: Client detection in `ClaudeProfile.get_tools_schema()`

### Security Implementation Details
```python
# In claude.py - Security check before exposing coordination tools
client_name = session_info.get("client_name", "") if session_info else ""
is_claude_code = client_name.lower() == "claude code"

# Only add coordination tools for Claude Code
if is_multi_agent and is_claude_code:
    # Add coordination tools
elif is_multi_agent and not is_claude_code:
    logger.warning(f"🚨 SECURITY: Coordination tools blocked for: '{client_name}'")
```

## Phase-by-Phase Implementation

### Phase 1: Enhanced MCP Tools (Day 1 - Morning, 4 hours)

**Goal**: Enhance existing MCP coordination tools with codebase analysis and terminal command generation

#### Enhanced Planning Tools
```python
@mcp.tool(description="[Planning] Analyze task conflicts and generate multi-terminal coordination plan")
async def analyze_task_conflicts(tasks: List[str]) -> Dict:
    """Enhanced with codebase scanning and conflict detection"""
    
    # NEW: Codebase analysis capabilities
    codebase_files = await scan_project_files()
    file_dependencies = await analyze_file_dependencies(codebase_files)
    
    # NEW: Task-to-file mapping
    task_file_mapping = await map_tasks_to_files(tasks, codebase_files)
    
    # NEW: Conflict detection algorithm
    conflicts = detect_file_conflicts(task_file_mapping, file_dependencies)
    
    # NEW: Optimal agent distribution
    optimal_distribution = calculate_agent_distribution(conflicts, len(tasks))
    
    return {
        "conflicts": conflicts,
        "agent_assignments": optimal_distribution,
        "coordination_strategy": "multi_terminal",
        "file_analysis": task_file_mapping,
        "dependencies": file_dependencies,
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

### Phase 2: Multi-Terminal Coordination Tools (Day 1 - Afternoon, 4 hours)

**Goal**: Ensure coordination tools work seamlessly across multiple terminals

**Reference**: Your existing coordination tools in `/app/tools/coordination.py`

#### Cross-Terminal File Locking
```python
@mcp.tool(description="[Execution] Cross-terminal file locking with database coordination")
async def claim_file_lock(file_paths: List[str], duration_minutes: int = 15) -> Dict:
    """Enhanced database-backed file locking across terminals"""
    
    # Use existing database coordination from your implementation
    # Prevent conflicts across separate Claude Code sessions
    return await existing_claim_file_lock_implementation(file_paths, duration_minutes)

@mcp.tool(description="[Execution] Cross-terminal progress synchronization")
async def sync_progress(task_id: str, status: str, affected_files: List[str] = None) -> Dict:
    """Enhanced progress broadcasting across multiple terminals"""
    
    # Use existing database sync from your implementation
    # Share status updates between separate Claude Code processes
    return await existing_sync_progress_implementation(task_id, status, affected_files)

@mcp.tool(description="[Monitoring] Check status of all agents across terminals")
async def check_agent_status(include_inactive: bool = False) -> Dict:
    """Monitor all agents across multiple Claude Code sessions"""
    
    # Use existing agent monitoring from your implementation
    # Provides visibility across all active terminals
    return await existing_check_agent_status_implementation(include_inactive)
```

#### Agent-Specific Tool Access
```python
# app/clients/claude.py - Agent-specific tool filtering
class ClaudeProfile(BaseClientProfile):
    def get_tools_schema(self, include_annotations: bool = False):
        agent_id = self.extract_agent_id_from_session()
        
        # Base tools for all agents
        tools = [jean_memory_tool, store_document_tool]
        
        # Agent-specific coordination tools
        if agent_id == "planner":
            tools.extend([
                analyze_task_conflicts_tool,
                create_task_distribution_tool,
                check_agent_status_tool
            ])
        elif agent_id.startswith("impl_"):
            tools.extend([
                claim_file_lock_tool,
                sync_progress_tool,
                check_agent_status_tool
            ])
        
        return tools
```

## User Experience Implementation

### Multi-Terminal MCP Workflow
```bash
# Multiple dedicated MCP connections for coordinated multi-agent development
# Terminal 1: Planner
claude mcp add jean-memory-planner --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__planner

# Terminals 2-5: Implementers (generated by planner)
claude mcp add jean-memory-impl-a --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_a
claude mcp add jean-memory-impl-b --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__impl_b
```

**Key Advantages**: 
- Full context window per agent (not shared)
- Process-level isolation and monitoring
- Independent debugging per terminal
- Proven database coordination infrastructure

### Workflow Integration (Multi-Terminal + Database Coordination)

**Phase 1: Task Input (30 seconds)**
- User provides multiple tasks in planner terminal
- Planner Claude analyzes complexity and requirements
- Multi-terminal coordination initiated

**Phase 2: Intelligent Planning (2-3 minutes)**  
- Planner uses `@analyze_task_conflicts` with enhanced codebase analysis
- File dependency detection and conflict prediction
- Optimal agent distribution calculation (2-5 agents)
- Generates terminal setup commands and specialized prompts

**Phase 3: Distribution (1 minute)**
- Planner outputs ready-to-use terminal commands
- User copies MCP connection commands to new terminals
- User pastes specialized prompts to start each implementer
- Database coordination automatically established

**Phase 4: Coordinated Execution (Duration varies)**
- Each implementer runs in dedicated terminal with full context
- `@claim_file_lock` prevents conflicts across terminals (database-backed)
- `@sync_progress` shares updates between separate Claude processes
- `@check_agent_status` provides visibility across all terminals
- Real-time collision prevention via cross-session coordination

**Phase 5: Completion & Monitoring (Continuous)**
- Progress tracking across all terminals via database
- Status monitoring from any terminal
- Final coordination and completion verification
- Optional commit coordination across all changes

## Expected User Experience

### What Users Will See

**🎯 Terminal 1 (Planner)**
```
User: "I need to add user authentication, create a dashboard, and implement password reset"

Planner Claude: I'll analyze these tasks for conflicts and create a coordination plan.
[Uses @analyze_task_conflicts and @create_task_distribution tools]

✅ Analysis complete! Here's your coordination plan:

**Terminal 2 Setup - Copy this command:**
claude mcp add jean-memory-impl-a --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/3237d468-429b-4ab6-9380-988f26131ffb__session__my_project__impl_a

**Terminal 2 Initial Prompt - Copy this:**
You are Implementer A in a coordinated multi-agent session.

Your assigned tasks:
1. Add user authentication to login page (files: auth.js, login.component.tsx)
2. Implement logout functionality (files: auth.js, header.component.tsx)

CRITICAL: Before editing any file, use @claim_file_lock to prevent conflicts.
Use @sync_progress to update status.

Other agents are working on: dashboard (Implementer B)
Session ID: my_project

**Terminal 3 Setup - Copy this command:**
claude mcp add jean-memory-impl-b --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/3237d468-429b-4ab6-9380-988f26131ffb__session__my_project__impl_b

**Terminal 3 Initial Prompt - Copy this:**
You are Implementer B in a coordinated multi-agent session.

Your assigned tasks:
1. Create user dashboard with profile data (files: dashboard.component.tsx, user.service.js)
2. Add password reset flow (files: auth.js, reset.component.tsx)

CRITICAL: Before editing any file, use @claim_file_lock to prevent conflicts.
Use @sync_progress to update status.

Other agents are working on: authentication (Implementer A)
Session ID: my_project

Ready for execution! Please copy these commands to set up your implementer terminals.
```

**⚡ Terminal 2 (Implementer A)**
```
User: [Pastes the Implementer A prompt]

Implementer A Claude: Understood! I'm Implementer A working on authentication tasks. 
Let me start by claiming locks on auth.js and login.component.tsx...
[Uses @claim_file_lock tool]
🔒 Files locked successfully. Beginning authentication implementation...
```

**⚡ Terminal 3 (Implementer B)**
```
User: [Pastes the Implementer B prompt]

Implementer B Claude: Understood! I'm Implementer B working on dashboard tasks.
Let me claim locks on dashboard.component.tsx and user.service.js...
[Uses @claim_file_lock tool]
🔒 Files locked successfully. Beginning dashboard implementation...
```

**🔄 Cross-Terminal Coordination**
```bash
# Terminal 2 (Implementer A)
Implementer A: Authentication complete! 
[Uses @sync_progress to broadcast completion]

# Terminal 3 (Implementer B) - Sees the update
Implementer B: I can see Implementer A completed authentication. 
[Uses @check_agent_status to verify]
Now I can safely integrate with the auth system in the dashboard...
```

## Testing Strategy

### Multi-Terminal Setup Testing
```bash
# Test terminal connection and coordination
def test_multi_terminal_setup():
    # Verify planner terminal connects with correct tools
    # Test implementer terminals connect with coordination tools
    # Validate agent-specific tool filtering works
    # Confirm database session registration across terminals
```

### Enhanced MCP Tools Testing
```python
def test_enhanced_coordination_tools():
    # Test analyze_task_conflicts with codebase analysis
    # Test create_task_distribution terminal command generation
    # Verify file conflict detection algorithms
    # Test optimal agent distribution calculations
```

### Cross-Terminal Coordination Testing
```python
def test_cross_terminal_coordination():
    # Test claim_file_lock prevents conflicts across terminals
    # Test sync_progress broadcasts between separate processes
    # Test check_agent_status monitors all terminals
    # Verify database coordination works reliably
```

### End-to-End Workflow Testing
```bash
# Test complete multi-terminal workflow:
# 1. Planner analyzes tasks and generates terminal commands
# 2. User sets up implementer terminals with generated commands
# 3. Implementers coordinate via database-backed tools
# 4. Cross-terminal monitoring and completion tracking
```

## Rollout Plan (1 Day Total)

### Day 1 Morning: Enhanced MCP Tools (4 hours)
- [ ] Add codebase analysis to analyze_task_conflicts
- [ ] Add terminal command generation to create_task_distribution
- [ ] Enhance file dependency detection algorithms
- [ ] Test enhanced tools with planner terminal

### Day 1 Afternoon: Multi-Terminal Integration (4 hours)  
- [ ] Verify agent-specific tool filtering works
- [ ] Test cross-terminal coordination tools
- [ ] End-to-end multi-terminal workflow testing
- [ ] Production deployment and monitoring

### Success Criteria
- [ ] Planner generates working terminal setup commands
- [ ] Implementers coordinate successfully across terminals
- [ ] File conflicts prevented via database coordination
- [ ] User workflow: input → analysis → terminal setup → execution

## Success Metrics

### Performance Targets (Multi-Terminal + Database)
- **Terminal setup**: < 30 seconds (user copy/paste commands)
- **File conflict prevention**: < 50ms (database-backed coordination)
- **Cross-terminal coordination**: < 100ms (database sync)
- **Context isolation**: Full context window per terminal (process-level)

### User Experience Goals
- **Zero conflicts**: Database-backed file locking across terminals
- **Process isolation**: Full debugging and monitoring per agent
- **Familiar interface**: Standard Claude Code in each terminal
- **Seamless workflow**: Task input → terminal setup → coordinated execution
- **Scalable architecture**: 2-5 agents with proven coordination infrastructure

### Quality Gates
- All existing MCP clients unaffected
- Standard Claude Code mode unchanged  
- Multi-terminal coordination works with existing database schema
- Agent-specific tool filtering prevents unauthorized access
- Cross-terminal file locking prevents conflicts reliably

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