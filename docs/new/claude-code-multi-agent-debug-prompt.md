# Claude Code Multi-Agent: Debug & Deploy Prompt

## Context

You are helping debug and resolve a blocking issue in the Claude Code multi-agent coordination system. The implementation is complete but coordination tools aren't appearing in the MCP interface.

## Current Status

**✅ What's Working:**
- Multi-terminal MCP connections via: `claude mcp add jean-memory-planner --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__{agent_id}`
- Virtual user ID parsing correctly extracts session and agent IDs
- All 5 coordination tools implemented in `/openmemory/api/app/tools/coordination.py`
- Database tables created in Supabase
- Tool registry contains all coordination functions

**❌ The Blocker:**
- Coordination tools not appearing in Claude Code's MCP tools list
- Only `jean_memory` and `store_document` tools visible
- Tools are defined in Claude profile schema but not exposed via MCP

## Your Mission

Work with me in a human-in-the-loop debugging cycle to resolve this blocker. Follow this approach:

### 0. Initial Cleanup
First, check and clean up any existing MCP connections:

```bash
# Check existing connections
claude mcp list

# If you see jean-memory-planner, jean-memory-impl-a, jean-memory-impl-b, remove them:
claude mcp remove jean-memory-planner
claude mcp remove jean-memory-impl-a
claude mcp remove jean-memory-impl-b

# Verify they're removed
claude mcp list
```

### 1. Review Current State
First, familiarize yourself with:
- `/Users/rohankatakam/Documents/jm/jean-memory/docs/latest/ccmulti/LESSONS_LEARNED.md` - See "Phase 2: Current Debugging Insights"
- `/Users/rohankatakam/Documents/jm/jean-memory/docs/latest/ccmulti/IMPLEMENTATION_GUIDE.md` - See "Phase 2 Status: IN PROGRESS"
- `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/app/tools/coordination.py` - The implemented tools
- `/Users/rohankatakam/Documents/jm/jean-memory/openmemory/api/app/clients/claude.py` - Tool schema definitions

### 2. Debug Cycle Process

**Step 1: Hypothesis & Fix**
- Form a hypothesis about why tools aren't appearing
- Implement a targeted fix
- Add debug logging if needed
- Commit and push to dev branch

**Step 2: Human Testing**
I will:
- Wait for deployment (~2-3 minutes)
- Restart Claude Code sessions
- Run test commands
- Share screenshots and logs

**Step 3: Analysis & Next Steps**
You will:
- Analyze the evidence I provide
- Determine if the fix worked
- If not, form new hypothesis and repeat
- If yes, proceed to test coordination functionality

### 3. Key Test Commands

**Note**: I currently have these connections active. I'll remove them before we start fresh debugging.

```bash
# Multi-terminal setup (I'll run in 3 terminals)
# Terminal 1: Planner
claude mcp add jean-memory-planner --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/3237d468-429b-4ab6-9380-988f2e131ffb__session__test_project__planner

# Terminal 2: Implementer A  
claude mcp add jean-memory-impl-a --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/3237d468-429b-4ab6-9380-988f2e131ffb__session__test_project__impl_a

# Terminal 3: Implementer B
claude mcp add jean-memory-impl-b --transport http https://jean-memory-api-dev.onrender.com/mcp/v2/claude/3237d468-429b-4ab6-9380-988f2e131ffb__session__test_project__impl_b
```

Test queries:
- `List all available tools`
- `Use the analyze_task_conflicts tool to analyze tasks: ["task1", "task2", "task3"]`

### 4. Debug Information Sources

**Server Logs:**
```bash
curl -s "https://jean-memory-api-dev.onrender.com/health/detailed" | jq
```

**MCP Protocol Test:**
```bash
curl -X POST https://jean-memory-api-dev.onrender.com/mcp/v2/claude/3237d468-429b-4ab6-9380-988f2e131ffb__session__test_project__planner \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | jq
```

### 5. Leading Theories to Investigate

1. **Session Context Issue**: Agent ID not being detected correctly in `get_tools_schema()`
2. **Schema Validation**: Tool schemas may have validation errors
3. **Tool Filtering**: MCP protocol may be filtering large tool schemas
4. **Import/Registration**: Tools not being registered despite decorators

### 6. Success Criteria

We've succeeded when:
1. All 5 coordination tools appear in Claude Code tools list
2. Planner agent can use `analyze_task_conflicts` and `create_task_distribution`
3. All agents can use `claim_file_lock`, `sync_progress`, and `check_agent_status`
4. Multi-agent coordination workflow functions end-to-end

## Important Files

**Implementation:**
- `/openmemory/api/app/tools/coordination.py` - Tool implementations
- `/openmemory/api/app/clients/claude.py` - Tool schema definitions
- `/openmemory/api/app/routing/mcp.py` - MCP routing and session parsing
- `/openmemory/api/app/tool_registry.py` - Tool registration
- `/openmemory/api/app/mcp_instance.py` - MCP server instance

**Documentation:**
- `/jean-memory/docs/latest/ccmulti/LESSONS_LEARNED.md` - Debugging insights
- `/jean-memory/docs/latest/ccmulti/PRODUCTION_DEPLOYMENT.md` - Deployment checklist
- `/jean-memory/docs/latest/ccmulti/CLAUDE_CODE_MULTI_AGENT_USER_WORKFLOW.md` - Target workflow

## Let's Begin!

Start by reviewing the current state and forming your first hypothesis about why the coordination tools aren't appearing in the MCP interface. Remember to:
- Make small, targeted changes
- Add logging to verify assumptions
- Test one hypothesis at a time
- Wait for my test results before proceeding

Ready? Let's debug this together!