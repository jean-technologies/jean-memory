# Claude Code Multi-Agent Kickoff Prompt

## Context

You are working on implementing the Claude Code multi-agent workflow system for Jean Memory. This is a multi-terminal coordination system that enables multiple Claude Code sessions to work together on complex development tasks using cross-session coordination.

## Current Status: Phase 1 Complete + Phase 2 Progress

**✅ Phase 1 Achievements (COMPLETED):**
- Virtual user ID parsing implemented (`{user_id}__session__{session_id}__{agent_id}`)
- Database session registration working with `last_activity` field
- Session-aware Claude profile created and tested
- Multi-terminal MCP connections tested successfully
- Enhanced tool descriptions working correctly in multi-agent sessions
- Scalable 2-5 agent architecture specified and documented

**✅ Phase 2 Progress Made:**
1. **Minor Issues Resolved**: Database schema using `last_activity` consistently, enhanced tool descriptions working
2. **Architecture Clarified**: Scalable 2-5 agent system (minimum 2, optimal 3, maximum 5 agents)
3. **Documentation Updated**: All markdown files updated with scalable architecture and correct API URLs
4. **API Endpoints**: Updated to use `https://jean-memory-api-dev.onrender.com`

**🚧 Phase 2 Remaining Tasks:**
1. **Implement Coordination Tools**: Planning tools (`analyze_task_conflicts`, `create_task_distribution`) and execution tools (`claim_file_lock`, `sync_progress`, `check_agent_status`)
2. **End-to-End Testing**: Test multi-terminal coordination workflow with 2-5 agents
3. **Production Readiness**: Final testing and deployment preparation

## Phase 2 Goals: Cross-Session Coordination Tools (Scalable 2-5 Agents)

The next phase involves implementing the coordination tools that enable multiple Claude Code terminals to work together safely across 2-5 agents:

1. **File Conflict Prevention**: `claim_file_lock` tool for cross-terminal file locking across all agents
2. **Progress Synchronization**: `sync_progress` tool for status updates across 2-5 sessions
3. **Agent Status Monitoring**: `check_agent_status` tool for cross-session visibility of all agents
4. **Task Distribution**: `analyze_task_conflicts` and `create_task_distribution` tools for planning phase with scalable agent assignment

## Instructions

### Step 1: Implement Phase 2 Coordination Tools (Primary Focus)

Add the following MCP tools to enable cross-session coordination:

1. **Planning Tools** (for planner agent):
   ```python
   @tool(description="Analyze task conflicts and create cross-session distribution plan for 2-5 agents")
   async def analyze_task_conflicts(tasks: List[str]) -> Dict:
       # Analyze file dependencies and collision potential
       # Generate scalable agent assignments (2-5 agents)
       # Consider project complexity and optimal agent count
       
   @tool(description="Generate terminal-specific prompts and coordination setup for scalable architecture") 
   async def create_task_distribution(analysis: Dict) -> Dict:
       # Create prompts for 1-4 implementation terminals based on analysis
       # Set up coordination strategy for chosen agent count
       # Generate connection commands for each terminal
   ```

2. **Execution Coordination Tools** (for implementation agents):
   ```python
   @tool(description="Create cross-session file locks via database for scalable multi-agent coordination")
   async def claim_file_lock(file_paths: List[str]) -> Dict:
       # Create database-backed locks visible across all terminals (2-5 agents)
       # Parse session info from virtual user ID
       # Coordinate with other agents in same session
       
   @tool(description="Broadcast progress updates across all terminals in session")
   async def sync_progress(task_id: str, status: str) -> Dict:
       # Update database with progress visible to all session agents (2-5)
       # Notify other terminals of status changes
       
   @tool(description="Check status of all other agents in the same session")
   async def check_agent_status() -> Dict:
       # Query database for all agents in same session
       # Return real-time status across all terminals (planner + implementers)
   ```

### Step 2: Test Multi-Terminal Coordination (Scalable 2-5 Agents)

1. **Test Multi-Terminal Setup** (Choose based on project complexity):
   ```bash
   # Terminal 1: Planner (Always Required)
   claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__test_project__planner
   
   # Minimum Configuration (2 Agents)
   # Terminal 2: Implementer A  
   claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__test_project__impl_a
   
   # Optimal Configuration (3 Agents)
   # Terminal 3: Implementer B
   claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__test_project__impl_b
   
   # Maximum Configuration (4-5 Agents)
   # Terminal 4: Implementer C
   claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__test_project__impl_c
   
   # Terminal 5: Implementer D  
   claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__test_project__impl_d
   ```

2. **Test Coordination Workflow**:
   - Use planner to analyze tasks and create distribution plan for optimal agent count (2-5)
   - Use implementers to claim file locks and coordinate changes across all terminals
   - Verify cross-session communication works via database across scalable architecture
   - Test with different agent counts (2, 3, 5) to validate scalability

### Step 3: Finalize Documentation and Deployment

**Documentation Status**: ✅ Already updated with:
- Phase 1 completion status and resolved issues
- Scalable 2-5 agent architecture specification
- Updated API endpoints (`https://jean-memory-api-dev.onrender.com`)
- Agent scaling guidelines and use cases
- Latest technical findings and implementation insights

**Remaining**: Update with Phase 2 implementation results and testing outcomes

## Key Files to Work With

**Implementation Files:**
- `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/app/routing/mcp.py` - Main MCP routing with virtual user ID parsing
- `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/app/clients/claude.py` - Claude profile with session awareness
- `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/main.py` - Router registration

**Documentation to Update:**
- `/Users/rohankatakam/Documents/jm/jean-memory/docs/latest/ccmulti/IMPLEMENTATION_GUIDE.md`
- `/Users/rohankatakam/Documents/jm/jean-memory/docs/latest/ccmulti/TECHNICAL_ARCHITECTURE.md`
- `/Users/rohankatakam/Documents/jm/jean-memory/docs/latest/ccmulti/LESSONS_LEARNED.md`

**Test Files:**
- `/Users/rohankatakam/Documents/jm/test_session_awareness.py` - Session awareness testing

## Reference Documentation

For implementation guidance, refer to:
- `jean-memory/docs/latest/ccmulti/CLAUDE_CODE_MULTI_AGENT_USER_WORKFLOW.md` - User workflow specification
- `jean-memory/docs/latest/ccmulti/TECHNICAL_ARCHITECTURE.md` - Multi-terminal architecture
- `jean-memory/docs/latest/ccmulti/IMPLEMENTATION_GUIDE.md` - 3-day implementation plan
- `jean-memory/docs/latest/ccmulti/LESSONS_LEARNED.md` - Previous implementation insights

## Success Criteria

- [x] Minor database schema issue fixed (using `last_activity` consistently)
- [x] Enhanced tool descriptions working correctly in multi-agent sessions  
- [x] Scalable 2-5 agent architecture specified and documented
- [x] Documentation updated with latest progress and findings
- [ ] **All Phase 2 coordination tools implemented and tested** (PRIMARY FOCUS)
- [ ] **Multi-terminal coordination working end-to-end with 2-5 agents** (CRITICAL)
- [ ] Ready for production testing with real development workflows

## Current Database Connection Info

Use the existing database connection and schema that's already working. The system uses:
- Virtual user ID pattern: `{user_id}__session__{session_id}__{agent_id}`
- Tables: `claude_code_sessions` and `claude_code_agents`
- MCP v2 endpoints: `/mcp/v2/{client_name}/{user_id}`

Focus on incremental improvements to the working system rather than major architectural changes.

## Latest Insights & Implementation Notes

### ✅ Key Discoveries from Phase 1 Testing
1. **Session Awareness Works**: Test script `/Users/rohankatakam/Documents/jm/test_session_awareness.py` confirms enhanced tool descriptions display multi-agent context correctly
2. **Database Schema Stable**: Using `last_activity` field consistently instead of `updated_at` - no database changes needed
3. **Virtual User ID Pattern Proven**: `{user_id}__session__{session_id}__{agent_id}` pattern successfully enables cross-session coordination
4. **API Endpoint Working**: `https://jean-memory-api-dev.onrender.com` transport working reliably with Claude Code

### 🎯 Implementation Focus for Phase 2
- **Primary Goal**: Implement the 5 coordination tools in `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/app/clients/claude.py`
- **Architecture**: Add tools to existing `ClaudeProfile.get_tools_schema()` method - no new files needed
- **Database Integration**: Use existing session management in `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/app/routing/mcp.py`
- **Testing Strategy**: Test with 2, 3, and 5 agent configurations to validate scalability

### 🚀 Ready-to-Implement Design
The system architecture is solid and tested. All that remains is:
1. Adding the 5 coordination tool implementations to the Claude profile
2. Testing multi-terminal coordination end-to-end 
3. Validating scalable architecture with different agent counts

**Current system can handle 2-5 agents without architectural changes** - the database schema, virtual user ID parsing, and session management all scale linearly.