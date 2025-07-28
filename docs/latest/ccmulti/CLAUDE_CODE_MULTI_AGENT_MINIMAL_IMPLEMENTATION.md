# Claude Code Multi-Agent Minimal Implementation Plan

## Overview

This document outlines a minimal implementation approach for Claude Code multi-agent shared memory using the existing Jean Memory infrastructure.

## Core Concept: Virtual User ID for Session Isolation

Instead of implementing complex new systems, we leverage the existing memory system with a simple virtual user ID pattern:

```
Standard Mode: user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
Session Mode:  user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464__session__webscraper__research"
```

All agents in the same session share the same base virtual user ID, giving them shared memory access.

## Implementation Components

### 1. Enhanced MCP Routing (Minimal Changes)

```python
# app/routing/mcp.py - Add session detection to existing endpoints

@mcp_router.post("/v2/{client_name}/{user_id}")
async def handle_http_v2_transport(client_name: str, user_id: str, request: Request, background_tasks: BackgroundTasks):
    # Existing code...
    
    # NEW: Parse session info from user_id if present
    session_info = parse_session_info(user_id)
    if session_info and client_name == "claude code":
        # Store in request state for tools to access
        request.state.session_info = session_info
    
    # Continue with existing logic...

def parse_session_info(user_id: str) -> Optional[Dict]:
    """Parse session info from virtual user_id format"""
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

### 2. Simple Coordination Tools Using Existing Memory

```python
# app/tools/session_coordination.py
from app.tools.memory import add_memories, search_memory
from app.context import user_id_var, client_name_var
import json
from datetime import datetime, timedelta

@mcp.tool(description="[Claude Code Sessions] Claim files to prevent conflicts")
async def session_claim_files(
    file_paths: List[str],
    operation: str = "write",
    duration_minutes: int = 30
) -> Dict:
    """Simple file locking using memory system"""
    client_name = client_name_var.get()
    if client_name != "claude code":
        return {"error": "This tool is only available for Claude Code"}
    
    user_id = user_id_var.get()
    if "__session__" not in user_id:
        return {"error": "This tool is only available in session mode"}
    
    agent_id = user_id.split("__")[-1]
    
    # Check for existing locks
    for file_path in file_paths:
        search_results = await search_memory(
            query=f"SESSION_LOCK:{file_path}",
            user_id=user_id,
            limit=5
        )
        
        # Check active locks
        for result in search_results:
            if "SESSION_LOCK:" in result.get("content", ""):
                try:
                    lock_data = json.loads(result["content"].split(":", 2)[2])
                    expires_at = datetime.fromisoformat(lock_data["expires_at"])
                    if expires_at > datetime.utcnow() and lock_data["agent_id"] != agent_id:
                        return {
                            "success": False,
                            "conflict": f"{file_path} locked by {lock_data['agent_id']}"
                        }
                except:
                    pass
    
    # Create locks
    lock_data = {
        "agent_id": agent_id,
        "operation": operation,
        "locked_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat()
    }
    
    memories = []
    for file_path in file_paths:
        memories.append(f"SESSION_LOCK:{file_path}:{json.dumps(lock_data)}")
    
    await add_memories(memories=memories, user_id=user_id)
    
    return {
        "success": True,
        "locked_files": file_paths,
        "expires_in_minutes": duration_minutes
    }

@mcp.tool(description="[Claude Code Sessions] Broadcast changes to other agents")
async def session_broadcast_change(
    file_paths: List[str],
    changes_summary: str
) -> Dict:
    """Broadcast changes using memory system"""
    client_name = client_name_var.get()
    if client_name != "claude code":
        return {"error": "This tool is only available for Claude Code"}
    
    user_id = user_id_var.get()
    if "__session__" not in user_id:
        return {"error": "This tool is only available in session mode"}
    
    agent_id = user_id.split("__")[-1]
    
    change_data = {
        "agent_id": agent_id,
        "file_paths": file_paths,
        "changes_summary": changes_summary,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await add_memories(
        memories=[f"SESSION_CHANGE:{json.dumps(change_data)}"],
        user_id=user_id
    )
    
    return {"success": True, "broadcasted": True}

@mcp.tool(description="[Claude Code Sessions] Check recent changes by other agents")
async def session_sync_changes(minutes: int = 30) -> Dict:
    """Get recent changes from other agents"""
    client_name = client_name_var.get()
    if client_name != "claude code":
        return {"error": "This tool is only available for Claude Code"}
    
    user_id = user_id_var.get()
    if "__session__" not in user_id:
        return {"error": "This tool is only available in session mode"}
    
    current_agent = user_id.split("__")[-1]
    
    search_results = await search_memory(
        query="SESSION_CHANGE:",
        user_id=user_id,
        limit=50
    )
    
    changes = []
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    for result in search_results:
        if "SESSION_CHANGE:" in result.get("content", ""):
            try:
                change_data = json.loads(result["content"].split(":", 1)[1])
                change_time = datetime.fromisoformat(change_data["timestamp"])
                
                if change_time > cutoff_time and change_data["agent_id"] != current_agent:
                    changes.append(change_data)
            except:
                continue
    
    changes.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "recent_changes": changes[:10],
        "count": len(changes),
        "time_window_minutes": minutes
    }
```

### 3. Enhanced Claude Profile (Conditional Tools)

```python
# app/clients/claude.py - Add session tools conditionally

class ClaudeProfile(BaseClientProfile):
    def get_tools_schema(self, include_annotations: bool = False) -> List[Dict[str, Any]]:
        # Get standard tools
        tools = [
            # ... existing tools ...
        ]
        
        # Check if this is a session request
        from app.context import user_id_var
        user_id = user_id_var.get()
        
        if user_id and "__session__" in user_id:
            # Add session coordination tools
            session_tools = [
                {
                    "name": "session_claim_files",
                    "description": "🔒 [Session Tool] Claim files to prevent conflicts with other agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files to claim"
                            },
                            "operation": {
                                "type": "string",
                                "enum": ["read", "write", "create", "delete"],
                                "description": "Operation type"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "default": 30,
                                "description": "Lock duration"
                            }
                        },
                        "required": ["file_paths"]
                    }
                },
                {
                    "name": "session_broadcast_change",
                    "description": "📢 [Session Tool] Notify other agents about your changes",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Changed files"
                            },
                            "changes_summary": {
                                "type": "string",
                                "description": "Summary of changes"
                            }
                        },
                        "required": ["file_paths", "changes_summary"]
                    }
                },
                {
                    "name": "session_sync_changes",
                    "description": "🔄 [Session Tool] Check recent changes by other agents",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "minutes": {
                                "type": "integer",
                                "default": 30,
                                "description": "Time window"
                            }
                        }
                    }
                }
            ]
            
            tools.extend(session_tools)
            
            # Add session context to first tool description
            session_name = user_id.split("__")[2]
            agent_id = user_id.split("__")[3]
            tools[0]["description"] += f"\n\n🤖 SESSION MODE: You are agent '{agent_id}' in session '{session_name}'. Use session tools to coordinate with other agents."
        
        return tools
```

## Usage Examples

### Single Agent Mode (No Changes)
```bash
# Standard connection
npx install-mcp https://api.jeanmemory.com/mcp/v2/claude%20code/fa97efb5-410d-4806-b137-8cf13b6cb464
```

### Multi-Agent Session Mode
```bash
# Research Agent
npx install-mcp https://api.jeanmemory.com/mcp/v2/claude%20code/fa97efb5-410d-4806-b137-8cf13b6cb464__session__webscraper__research

# Implementation Agent
npx install-mcp https://api.jeanmemory.com/mcp/v2/claude%20code/fa97efb5-410d-4806-b137-8cf13b6cb464__session__webscraper__implementation
```

### Agent Workflow Example

```python
# Research Agent
@session_sync_changes(30)  # Check for recent changes

@session_claim_files(["README.md", "requirements.txt"], "write", 20)

# Make changes...

@session_broadcast_change(
    ["README.md", "requirements.txt"],
    "Updated documentation and added BeautifulSoup dependency"
)

# Implementation Agent
@session_sync_changes(60)  # See research agent's changes

@session_claim_files(["src/scraper.py"], "create", 45)

# Implement...

@session_broadcast_change(
    ["src/scraper.py"],
    "Implemented web scraper using BeautifulSoup"
)
```

## Implementation Benefits

1. **Minimal Changes**: Uses existing memory system, no new dependencies
2. **Backward Compatible**: Standard connections work unchanged
3. **Simple**: No complex state management or external services
4. **Fast**: Leverages existing optimized memory queries
5. **Flexible**: Easy to extend with more coordination tools

## Database Migrations

Since models are already added, just need to run:

```bash
cd openmemory/api
alembic upgrade head
```

## Testing Strategy

1. **Unit Tests**: Test session parsing and tool functions
2. **Integration Tests**: Test multi-agent memory sharing
3. **Performance Tests**: Ensure minimal overhead
4. **Compatibility Tests**: Verify standard mode unchanged

## Rollout Plan

1. **Phase 1**: Deploy session parsing (invisible change)
2. **Phase 2**: Add coordination tools (feature flag)
3. **Phase 3**: Enable for beta users
4. **Phase 4**: Full rollout with documentation

This minimal approach achieves multi-agent coordination without the complexity of external systems or major architectural changes.