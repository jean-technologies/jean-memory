# Remove Multi-Agent Claude Code Infrastructure and Simplify to Single Agent Only

## Task Description

Remove the multi-agent tab functionality from the Claude Code connection modal in the dashboard and eliminate all associated multi-agent infrastructure including database tables, coordination tools, and backend services. The Connect modal should only show the Single Agent tab content with the standard MCP server setup instructions.

---

## Part 1 — Mini-FRD (What & Why)

### 1. What
Remove the tabbed interface (Single Agent/Multi-Agent) from the Claude Code connection modal and eliminate all multi-agent coordination infrastructure, leaving only the simple single-agent MCP server installation.

### 2. Why
Multi-agent functionality adds complexity without clear user adoption. Simplifying to single-agent only reduces maintenance overhead, improves user experience with a cleaner interface, and eliminates unused infrastructure components that consume resources.

### 3. Scope

**In Scope:**
- Remove Multi-Agent tab from Claude Code modal (InstallModal.tsx:628-784)
- Remove multi-agent coordination backend infrastructure 
- Remove database tables: claude_code_sessions, claude_code_agents, claude_code_tasks
- Remove coordination tools and routing logic
- Keep single-agent functionality intact

**Out of Scope:**
- Other app integrations (Cursor, Claude Desktop, etc.)
- Core MCP functionality
- User authentication or memory storage features

### 4. Acceptance Criteria
- Claude Code modal shows only single-agent setup instructions
- No Multi-Agent tab visible in the interface
- Backend coordination infrastructure removed completely
- Single-agent MCP installation still works correctly
- No broken references or dead code remaining

---

## Part 2 — Mini-EDD (How)

### 1. Chosen Approach
Remove the Tabs component from InstallModal.tsx and display only the single-agent content directly. Clean up backend by removing coordination tables, tools, and routing logic. This approach maintains the working single-agent functionality while eliminating complexity.

### 2. Key Components / Code Areas
- `openmemory/ui/components/dashboard/InstallModal.tsx` (lines 628-784)
- `openmemory/api/app/tools/coordination.py`
- `openmemory/api/app/routing/mcp.py` (multi-agent session management)
- `openmemory/api/app/coordination_schema.sql`
- `openmemory/api/create_coordination_tables.py`
- `openmemory/api/app/init_coordination_db.py`

### 3. Implementation Steps
1. Remove Tabs component and Multi-Agent TabsContent from InstallModal.tsx
2. Keep only Single Agent setup instructions in the modal
3. Remove coordination.py tools file entirely
4. Remove multi-agent session parsing from mcp.py routing
5. Drop coordination database tables from schema
6. Remove coordination table creation scripts
7. Test single-agent Claude Code connection still works

### 4. Risks & Mitigation
- **Breaking single-agent functionality** → Test single-agent setup before deploying
- **Database migration issues** → Use proper DROP TABLE IF EXISTS statements
- **Frontend build errors** → Verify all imports and references are removed
- **Dead code references** → Search codebase for coordination-related imports

### 5. Testing Plan
- Verify Claude Code modal shows only single-agent instructions
- Test MCP server installation command works correctly
- Confirm no console errors in frontend
- Validate backend starts without coordination dependencies
- **Human-in-the-loop testing:** Follow single-agent setup instructions and verify connection works with backend logs

---

## Implementation Notes

### Frontend Changes Required
- File: `openmemory/ui/components/dashboard/InstallModal.tsx`
- Remove lines 628-784 (Tabs component and Multi-Agent TabsContent)
- Keep only the Single Agent content (lines 634-686)
- Remove Tabs, TabsList, TabsTrigger imports if no longer used

### Backend Changes Required
- Remove `openmemory/api/app/tools/coordination.py` entirely
- Update `openmemory/api/app/routing/mcp.py` to remove multi-agent session management
- Drop coordination tables from database schema
- Remove coordination initialization scripts

### Database Migration
```sql
DROP TABLE IF EXISTS claude_code_tasks;
DROP TABLE IF EXISTS claude_code_agents;
DROP TABLE IF EXISTS claude_code_sessions;
```

### Verification Commands
```bash
# Frontend build test
cd openmemory/ui && npm run build

# Backend startup test
cd openmemory/api && python -m app.main

# Search for dead references
grep -r "coordination" openmemory/
grep -r "multi.agent" openmemory/
```