# Claude Code Multi-Agent MCP Implementation

## Overview

This document outlines the implementation of multi-agent coordination features specifically for Claude Code MCP connections. The design ensures complete isolation from other MCP clients (ChatGPT, Cursor, VS Code, etc.) while maintaining backward compatibility for existing Claude Code users.

## Core Requirements

1. **Claude Code Exclusive**: Multi-agent features only available for `claude code` client
2. **Backward Compatible**: Existing Claude Code connections work unchanged
3. **Zero Impact**: No effect on other MCP clients (ChatGPT, Cursor, etc.)
4. **Session Isolation**: Multi-agent sessions use isolated memory spaces
5. **Minimal Changes**: Leverage existing architecture with minimal modifications

## Architecture Design

### Current Claude Code MCP Flow

```
User connects: npx install-mcp https://api.jeanmemory.com/mcp/claude code/sse/{user_id}
                                                               ^^^^^^^^^^^
                                                               client_name = "claude code"
↓
MCP Router: /mcp/claude code/sse/{user_id}
↓ 
ClaudeProfile.get_tools_schema() → Standard tools
↓
Available tools: @jean_memory, @search_memory, @ask_memory, @store_document
```

### Enhanced Multi-Agent Flow

```
Agent connects: npx install-mcp https://api.jeanmemory.com/mcp/claude%20code/sse/{user_id}/session/{session_name}/{agent_id}
                                                               ^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                               client_name    session path parameters
↓
MCP Router: New session endpoints → Detect session mode (Claude Code only)
↓
ClaudeProfile.get_tools_schema() → Standard tools + Session tools (if Claude Code + session mode)
↓
Available tools: Standard tools + @claim_files, @release_files, @sync_codebase, @broadcast_message, @get_agent_messages
```

## Implementation Details

### 1. New Session-Aware MCP Endpoints

```python
# app/routing/mcp.py - Add new session endpoints for Claude Code

# ===============================================
# SESSION ENDPOINTS - CLAUDE CODE ONLY
# ===============================================

@mcp_router.get("/{client_name}/sse/{user_id}/session/{session_name}/{agent_id}")
async def handle_session_sse_connection(
    client_name: str, 
    user_id: str, 
    session_name: str, 
    agent_id: str, 
    request: Request
):
    """
    Session-aware SSE endpoint - CLAUDE CODE ONLY
    URL: /mcp/claude%20code/sse/{user_id}/session/{session_name}/{agent_id}
    """
    from fastapi.responses import StreamingResponse
    
    # Session features are EXCLUSIVELY for Claude Code
    if client_name != "claude code":
        return JSONResponse(
            status_code=404, 
            content={"error": f"Session endpoints not available for client '{client_name}'"}
        )
    
    logger.info(f"Session SSE connection: {client_name}/{user_id}/session/{session_name}/{agent_id}")
    
    # Create virtual user_id for session isolation
    virtual_user_id = f"{user_id}__session__{session_name}__{agent_id}"
    
    # Create a message queue for this session connection
    connection_id = f"{client_name}_{virtual_user_id}"
    if connection_id not in sse_message_queues:
        sse_message_queues[connection_id] = asyncio.Queue()
    
    async def event_generator():
        try:
            # Send the endpoint event that supergateway expects
            session_endpoint = f"/mcp/{client_name}/messages/{user_id}/session/{session_name}/{agent_id}"
            yield f"event: endpoint\ndata: {session_endpoint}\n\n"
            
            # Send immediate heartbeat
            yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()})}\n\n"

            # Main event loop
            while True:
                try:
                    message = await asyncio.wait_for(
                        sse_message_queues[connection_id].get(), 
                        timeout=1.0
                    )
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"Session SSE connection closed for {connection_id}")
            if connection_id in sse_message_queues:
                del sse_message_queues[connection_id]
            return
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

@mcp_router.post("/{client_name}/messages/{user_id}/session/{session_name}/{agent_id}")
async def handle_session_messages(
    client_name: str,
    user_id: str, 
    session_name: str,
    agent_id: str,
    request: Request, 
    background_tasks: BackgroundTasks
):
    """
    Session-aware messages endpoint - CLAUDE CODE ONLY
    URL: /mcp/claude%20code/messages/{user_id}/session/{session_name}/{agent_id}
    """
    
    # Session features are EXCLUSIVELY for Claude Code
    if client_name != "claude code":
        return JSONResponse(
            status_code=404,
            content={"error": f"Session endpoints not available for client '{client_name}'"}
        )
    
    try:
        body = await request.json()
        
        # Create virtual user_id and set session context
        virtual_user_id = f"{user_id}__session__{session_name}__{agent_id}"
        
        # Set headers for session context
        request.headers.__dict__['_list'].append((b'x-user-id', virtual_user_id.encode()))
        request.headers.__dict__['_list'].append((b'x-client-name', client_name.encode()))
        
        # Store session metadata in context
        session_context = {
            "base_user_id": user_id,
            "session_name": session_name,
            "agent_id": agent_id,
            "is_session": True,
            "virtual_user_id": virtual_user_id,
            "client_supports_sessions": True
        }
        
        # Use existing request logic with session context
        response = await handle_request_logic(request, body, background_tasks)
        response_payload = json.loads(response.body)

        # Handle SSE messaging
        connection_id = f"{client_name}_{virtual_user_id}"
        if connection_id in sse_message_queues:
            await sse_message_queues[connection_id].put(response_payload)
            await sse_message_queues[connection_id].put({
                'event': 'heartbeat', 
                'data': {'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()}
            })
            return Response(status_code=204)
        else:
            return response
    
    except Exception as e:
        logger.error(f"Error in session messages handler: {e}", exc_info=True)
        request_id = None
        try:
            body = await request.json()
            request_id = body.get("id")
        except:
            pass
        
        response_payload = {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": request_id,
        }
        
        connection_id = f"{client_name}_{user_id}__session__{session_name}__{agent_id}"
        if connection_id in sse_message_queues:
            await sse_message_queues[connection_id].put(response_payload)
            return Response(status_code=204)
        else:
            return JSONResponse(content=response_payload, status_code=500)

# Enhanced request handler to detect session mode from context
async def handle_request_logic(request: Request, body: dict, background_tasks: BackgroundTasks):
    # ... existing authentication logic ...
    
    # Detect session mode from user_id format
    user_context = parse_user_context(user_id_from_header, client_name_from_header)
    
    # Set enhanced context
    user_token = user_id_var.set(user_context["virtual_user_id"])
    client_token = client_name_var.set(client_name_from_header)
    tasks_token = background_tasks_var.set(background_tasks)
    
    # Store session context for tools to access
    session_context_var.set(user_context)
    
    # ... rest of existing logic remains unchanged ...

def parse_user_context(user_id: str, client_name: str) -> Dict[str, str]:
    """Parse user context from user_id and client"""
    
    # Session features are EXCLUSIVELY for Claude Code
    if client_name != "claude code":
        return {
            "base_user_id": user_id,
            "session_name": None,
            "agent_id": None,
            "is_session": False,
            "virtual_user_id": user_id,
            "client_supports_sessions": False
        }
    
    # Check if this is a session-formatted user_id
    if "__session__" in user_id:
        parts = user_id.split("__")
        return {
            "base_user_id": parts[0],
            "session_name": parts[2] if len(parts) >= 3 else "default",
            "agent_id": parts[3] if len(parts) >= 4 else "agent",
            "is_session": True,
            "virtual_user_id": user_id,
            "client_supports_sessions": True
        }
    else:
        return {
            "base_user_id": user_id,
            "session_name": None,
            "agent_id": None,
            "is_session": False,
            "virtual_user_id": user_id,
            "client_supports_sessions": True  # Claude Code supports sessions, just not using them
        }
```

### 2. Claude Code Specific Profile Enhancement

```python
# app/clients/claude.py - Enhanced with session detection
from app.context import user_id_var, client_name_var

class ClaudeProfile(BaseClientProfile):
    def get_tools_schema(self, include_annotations: bool = False) -> List[Dict[str, Any]]:
        """
        Returns tools schema with session tools ONLY for Claude Code in session mode
        """
        # Get standard tools (unchanged)
        tools = [
            {
                "name": "jean_memory",
                "description": "🌟 PRIMARY TOOL for all conversational interactions...",
                # ... existing tool definition ...
            },
            {
                "name": "add_memories", 
                "description": "💾 MANUAL memory saving...",
                # ... existing tool definition ...
            },
            {
                "name": "store_document",
                "description": "⚡ FAST document upload...",
                # ... existing tool definition ...
            },
            {
                "name": "ask_memory",
                "description": "FAST memory search...",
                # ... existing tool definition ...
            },
            {
                "name": "search_memory",
                "description": "Quick keyword-based search...",
                # ... existing tool definition ...
            },
            {
                "name": "list_memories",
                "description": "Browse through the user's stored memories...",
                # ... existing tool definition ...
            },
            {
                "name": "deep_memory_query",
                "description": "COMPREHENSIVE search...",
                # ... existing tool definition ...
            }
        ]
        
        # Check if this is Claude Code in session mode
        from app.context import session_context_var
        session_context = session_context_var.get({})
        client_name = client_name_var.get()
        
        # Session tools ONLY for Claude Code AND session mode
        if client_name == "claude code" and session_context.get("is_session", False):
            session_tools = [
                {
                    "name": "claim_files",
                    "description": "🔒 Claim exclusive access to files to prevent conflicts with other agents in this session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array", 
                                "items": {"type": "string"}, 
                                "description": "List of file paths to claim (relative to project root)"
                            },
                            "operation": {
                                "type": "string", 
                                "enum": ["read", "write", "create", "delete"], 
                                "description": "Type of operation you plan to perform"
                            },
                            "duration_minutes": {
                                "type": "integer", 
                                "default": 30, 
                                "description": "How long to hold the claim (auto-expires)"
                            }
                        },
                        "required": ["file_paths", "operation"]
                    }
                },
                {
                    "name": "release_files", 
                    "description": "🔓 Release file claims and notify other agents about changes made",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array", 
                                "items": {"type": "string"}, 
                                "description": "Files to release (must match claimed files)"
                            },
                            "changes_summary": {
                                "type": "string", 
                                "description": "Brief summary of what changes were made"
                            },
                            "structural_changes": {
                                "type": "array", 
                                "items": {"type": "string"}, 
                                "description": "List any major structural changes (new functions, classes, dependencies, etc.)"
                            }
                        },
                        "required": ["file_paths", "changes_summary"]
                    }
                },
                {
                    "name": "sync_codebase",
                    "description": "🔄 Get recent changes made by other agents to stay synchronized and avoid conflicts",
                    "inputSchema": {
                        "type": "object", 
                        "properties": {
                            "since_minutes": {
                                "type": "integer", 
                                "default": 60, 
                                "description": "How far back to check for changes (in minutes)"
                            }
                        }
                    }
                },
                {
                    "name": "broadcast_message",
                    "description": "📢 Send coordination message to other agents in this session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string", 
                                "description": "Message to broadcast to other agents"
                            },
                            "message_type": {
                                "type": "string", 
                                "enum": ["info", "warning", "question", "coordination"], 
                                "default": "info",
                                "description": "Type of message for prioritization"
                            }
                        },
                        "required": ["message"]
                    }
                },
                {
                    "name": "get_agent_messages",
                    "description": "📬 Check for messages from other agents in this session",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer", 
                                "default": 10, 
                                "description": "Maximum number of messages to retrieve"
                            }
                        }
                    }
                }
            ]
            
            # Add session tools to the schema
            tools.extend(session_tools)
            
            # Add session info to the first tool's description
            tools[0]["description"] += f"\n\n🤖 MULTI-AGENT MODE: You are in a shared session with other Claude Code agents. Use @sync_codebase regularly and @claim_files before making changes."
        
        # Add annotations for newer protocol versions (unchanged)
        if include_annotations:
            annotations_map = {
                "jean_memory": {"readOnly": False, "sensitive": True, "destructive": False, "intelligent": True},
                "ask_memory": {"readOnly": True, "sensitive": False, "destructive": False},
                "add_memories": {"readOnly": False, "sensitive": True, "destructive": False},
                "store_document": {"readOnly": False, "sensitive": True, "destructive": False},
                "search_memory": {"readOnly": True, "sensitive": False, "destructive": False},
                "list_memories": {"readOnly": True, "sensitive": True, "destructive": False},
                "deep_memory_query": {"readOnly": True, "sensitive": False, "destructive": False, "expensive": True},
                # Session tool annotations
                "claim_files": {"readOnly": False, "sensitive": False, "destructive": False},
                "release_files": {"readOnly": False, "sensitive": False, "destructive": False},
                "sync_codebase": {"readOnly": True, "sensitive": False, "destructive": False},
                "broadcast_message": {"readOnly": False, "sensitive": False, "destructive": False},
                "get_agent_messages": {"readOnly": True, "sensitive": False, "destructive": False}
            }
            for tool in tools:
                if tool["name"] in annotations_map:
                    tool["annotations"] = annotations_map[tool["name"]]
        
        return tools

    async def handle_tool_call(self, tool_name: str, tool_args: dict, user_id: str) -> Any:
        """Enhanced tool handler with session tool routing"""
        
        # Session tools - only handle if this is Claude Code
        session_tools = ["claim_files", "release_files", "sync_codebase", "broadcast_message", "get_agent_messages"]
        
        if tool_name in session_tools:
            client_name = client_name_var.get()
            
            # Double-check: session tools only for Claude Code
            if client_name != "claude code":
                return {"error": f"Tool '{tool_name}' is not available for client '{client_name}'"}
            
            # Route to session coordination tools
            from app.tools.session_coordination import (
                claim_files, release_files, sync_codebase, 
                broadcast_message, get_agent_messages
            )
            
            if tool_name == "claim_files":
                return await claim_files(**tool_args)
            elif tool_name == "release_files":
                return await release_files(**tool_args)
            elif tool_name == "sync_codebase":
                return await sync_codebase(**tool_args)
            elif tool_name == "broadcast_message":
                return await broadcast_message(**tool_args)
            elif tool_name == "get_agent_messages":
                return await get_agent_messages(**tool_args)
        
        # Standard tools - filter parameters for backward compatibility
        if tool_name == "search_memory":
            tool_args.pop("tags_filter", None)
        elif tool_name == "add_memories":
            tool_args.pop("tags", None)

        # Call the base handler for standard tools
        return await super().handle_tool_call(tool_name, tool_args, user_id)
```

### 3. Session Coordination Tools (Claude Code Only)

```python
# app/tools/session_coordination.py
from app.mcp_instance import mcp
from app.tools.memory import add_memories, search_memory
from app.context import user_id_var, client_name_var
from typing import List, Dict, Optional
import json
import uuid
from datetime import datetime

def _ensure_claude_code_session():
    """Ensure this is a Claude Code session - used by all session tools"""
    from app.context import session_context_var
    
    client_name = client_name_var.get()
    session_context = session_context_var.get({})
    
    if client_name != "claude code":
        raise ValueError(f"Session tools are exclusive to Claude Code. Current client: {client_name}")
    
    if not session_context.get("is_session", False):
        raise ValueError("Session tools only available in multi-agent session mode")
    
    return session_context

def _parse_session_context() -> Dict[str, str]:
    """Parse session context from context variables"""
    from app.context import session_context_var
    return session_context_var.get({})

@mcp.tool(description="Claim exclusive access to files to prevent conflicts")
async def claim_files(
    file_paths: List[str],
    operation: str,
    duration_minutes: int = 30
) -> Dict:
    """
    Claim files to prevent conflicts - CLAUDE CODE SESSION ONLY
    
    This tool is exclusively available to Claude Code agents in multi-agent sessions.
    Other MCP clients (ChatGPT, Cursor, etc.) will never see this tool.
    """
    try:
        session_context = _ensure_claude_code_session()
        user_id = session_context["virtual_user_id"]
        context = _parse_session_context()
    except ValueError as e:
        return {"error": str(e)}
    
    # Check for conflicts with other agents
    conflicts = []
    for file_path in file_paths:
        search_results = await search_memory(
            query=f"FILE_CLAIM:{file_path}",
            user_id=user_id,
            limit=5
        )
        
        # Check for active claims by other agents
        for result in search_results:
            if result.get("content", "").startswith("FILE_CLAIM:"):
                try:
                    claim_data_str = result["content"].split(":", 2)[2]
                    claim_data = json.loads(claim_data_str)
                    
                    # Check if claim is still active and by different agent
                    if (claim_data.get("status") == "active" and 
                        claim_data.get("agent_id") != context["agent_id"] and
                        claim_data.get("expires_at", 0) > datetime.utcnow().timestamp()):
                        
                        conflicts.append({
                            "file": file_path,
                            "claimed_by": claim_data.get("agent_id"),
                            "operation": claim_data.get("operation"),
                            "expires_in_minutes": max(0, int((claim_data.get("expires_at", 0) - datetime.utcnow().timestamp()) / 60))
                        })
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    
    if conflicts:
        return {
            "success": False,
            "conflicts": conflicts,
            "message": "File access conflicts detected. Wait for claims to expire or coordinate with other agents.",
            "suggestion": "Use @get_agent_messages and @broadcast_message to coordinate with other agents"
        }
    
    # Create claims
    claim_data = {
        "agent_id": context["agent_id"],
        "session_name": context["session_name"],
        "file_paths": file_paths,
        "operation": operation,
        "status": "active",
        "claimed_at": datetime.utcnow().isoformat(),
        "expires_at": datetime.utcnow().timestamp() + (duration_minutes * 60)
    }
    
    for file_path in file_paths:
        await add_memories(
            memories=[f"FILE_CLAIM:{file_path}:{json.dumps(claim_data)}"],
            user_id=user_id,
            metadata={
                "type": "file_claim",
                "agent_id": context["agent_id"],
                "session_name": context["session_name"],
                "file_path": file_path,
                "operation": operation,
                "client": "claude code"  # Mark as Claude Code specific
            }
        )
    
    return {
        "success": True,
        "claimed_files": file_paths,
        "operation": operation,
        "expires_in_minutes": duration_minutes,
        "agent_id": context["agent_id"],
        "message": f"Successfully claimed {len(file_paths)} files for {operation} operation"
    }

@mcp.tool(description="Release file claims and notify changes")
async def release_files(
    file_paths: List[str],
    changes_summary: str,
    structural_changes: Optional[List[str]] = None
) -> Dict:
    """
    Release file claims and broadcast changes - CLAUDE CODE SESSION ONLY
    """
    try:
        session_context = _ensure_claude_code_session()
        user_id = session_context["virtual_user_id"]
        context = _parse_session_context()
    except ValueError as e:
        return {"error": str(e)}
    
    # Create change notification
    change_data = {
        "agent_id": context["agent_id"],
        "session_name": context["session_name"],
        "file_paths": file_paths,
        "changes_summary": changes_summary,
        "structural_changes": structural_changes or [],
        "completed_at": datetime.utcnow().isoformat(),
        "change_id": uuid.uuid4().hex[:8]
    }
    
    # Release claims and add change notifications
    for file_path in file_paths:
        # Mark claim as released
        await add_memories(
            memories=[f"FILE_RELEASE:{file_path}:{context['agent_id']}:{datetime.utcnow().isoformat()}"],
            user_id=user_id,
            metadata={
                "type": "file_release",
                "agent_id": context["agent_id"],
                "session_name": context["session_name"],
                "file_path": file_path,
                "client": "claude code"
            }
        )
        
        # Add change notification
        await add_memories(
            memories=[f"CODEBASE_CHANGE:{file_path}:{json.dumps(change_data)}"],
            user_id=user_id,
            metadata={
                "type": "codebase_change",
                "agent_id": context["agent_id"],
                "session_name": context["session_name"],
                "file_path": file_path,
                "has_structural_changes": len(structural_changes or []) > 0,
                "client": "claude code"
            }
        )
    
    return {
        "success": True,
        "released_files": file_paths,
        "change_id": change_data["change_id"],
        "agent_id": context["agent_id"],
        "message": "Files released and changes broadcasted to other agents"
    }

@mcp.tool(description="Get recent codebase changes from other agents")
async def sync_codebase(since_minutes: int = 60) -> Dict:
    """
    Get recent changes by other agents - CLAUDE CODE SESSION ONLY
    """
    try:
        session_context = _ensure_claude_code_session()
        user_id = session_context["virtual_user_id"]
        context = _parse_session_context()
    except ValueError as e:
        return {"error": str(e)}
    
    # Search for recent changes
    search_results = await search_memory(
        query="CODEBASE_CHANGE",
        user_id=user_id,
        limit=50
    )
    
    changes = []
    structural_changes_summary = []
    
    cutoff_time = datetime.utcnow().timestamp() - (since_minutes * 60)
    
    for result in search_results:
        if result.get("content", "").startswith("CODEBASE_CHANGE:"):
            try:
                change_data_str = result["content"].split(":", 2)[2]
                change_data = json.loads(change_data_str)
                
                # Skip own changes
                if change_data.get("agent_id") == context["agent_id"]:
                    continue
                
                # Check if within time window
                change_time = datetime.fromisoformat(change_data.get("completed_at", "")).timestamp()
                if change_time < cutoff_time:
                    continue
                
                change_info = {
                    "agent": change_data.get("agent_id"),
                    "files": change_data.get("file_paths", []),
                    "summary": change_data.get("changes_summary"),
                    "structural_changes": change_data.get("structural_changes", []),
                    "timestamp": change_data.get("completed_at"),
                    "change_id": change_data.get("change_id")
                }
                
                changes.append(change_info)
                structural_changes_summary.extend(change_data.get("structural_changes", []))
                
            except (json.JSONDecodeError, KeyError, IndexError, ValueError):
                continue
    
    # Sort by timestamp (most recent first)
    changes.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "recent_changes": changes,
        "total_changes": len(changes),
        "structural_changes_summary": list(set(structural_changes_summary)),
        "time_window_minutes": since_minutes,
        "current_agent": context["agent_id"],
        "recommendation": "Review these changes before making modifications to avoid conflicts" if changes else "No recent changes detected"
    }

@mcp.tool(description="Broadcast message to other agents in session")  
async def broadcast_message(message: str, message_type: str = "info") -> Dict:
    """
    Send message to other agents in session - CLAUDE CODE SESSION ONLY
    """
    try:
        session_context = _ensure_claude_code_session()
        user_id = session_context["virtual_user_id"]
        context = _parse_session_context()
    except ValueError as e:
        return {"error": str(e)}
    
    message_data = {
        "from_agent": context["agent_id"],
        "session_name": context["session_name"],
        "message": message,
        "message_type": message_type,
        "timestamp": datetime.utcnow().isoformat(),
        "message_id": uuid.uuid4().hex[:8]
    }
    
    await add_memories(
        memories=[f"AGENT_MESSAGE:{json.dumps(message_data)}"],
        user_id=user_id,
        metadata={
            "type": "agent_message",
            "from_agent": context["agent_id"],
            "session_name": context["session_name"],
            "message_type": message_type,
            "client": "claude code"
        }
    )
    
    return {
        "success": True,
        "message_id": message_data["message_id"],
        "from_agent": context["agent_id"],
        "message_type": message_type,
        "message": "Message broadcasted to all agents in session"
    }

@mcp.tool(description="Get messages from other agents in session")
async def get_agent_messages(limit: int = 10) -> Dict:
    """
    Check messages from other agents - CLAUDE CODE SESSION ONLY
    """
    try:
        session_context = _ensure_claude_code_session()
        user_id = session_context["virtual_user_id"]
        context = _parse_session_context()
    except ValueError as e:
        return {"error": str(e)}
    
    search_results = await search_memory(
        query="AGENT_MESSAGE",
        user_id=user_id,
        limit=limit * 2  # Get more to filter out own messages
    )
    
    messages = []
    for result in search_results:
        if result.get("content", "").startswith("AGENT_MESSAGE:"):
            try:
                message_data_str = result["content"].split(":", 1)[1]
                message_data = json.loads(message_data_str)
                
                # Skip own messages
                if message_data.get("from_agent") != context["agent_id"]:
                    messages.append(message_data)
                    
                # Stop when we have enough messages
                if len(messages) >= limit:
                    break
                    
            except (json.JSONDecodeError, KeyError, IndexError):
                continue
    
    # Sort by timestamp (most recent first)
    messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "messages": messages,
        "count": len(messages),
        "current_agent": context["agent_id"],
        "session_name": context["session_name"]
    }
```

### 4. Context Variables Enhancement

```python
# app/context.py - Add session context
from contextvars import ContextVar
from typing import Dict, Any

user_id_var: ContextVar[str] = ContextVar('user_id')
client_name_var: ContextVar[str] = ContextVar('client_name')
background_tasks_var: ContextVar = ContextVar('background_tasks')

# New: Session context for multi-agent coordination
session_context_var: ContextVar[Dict[str, Any]] = ContextVar('session_context', default={})
```

## Frontend Session Management

### Dashboard Integration

To provide a seamless user experience, we'll add a Claude Code session management interface to the Jean Memory dashboard. This allows users to create and manage multi-agent sessions directly from the web interface.

#### Session Management Components

```typescript
// components/claude-code/SessionManager.tsx
interface Session {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  agents: Agent[];
  status: 'active' | 'inactive';
}

interface Agent {
  id: string;
  session_id: string;
  name: string;
  role?: string;
  connection_url: string;
  status: 'connected' | 'disconnected';
  last_activity: string;
}

export function SessionManager() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  return (
    <div className="claude-code-sessions">
      <div className="session-header">
        <h2>Claude Code Multi-Agent Sessions</h2>
        <Button onClick={() => setShowCreateDialog(true)}>
          Create New Session
        </Button>
      </div>
      
      <SessionList sessions={sessions} />
      
      {showCreateDialog && (
        <CreateSessionDialog 
          onClose={() => setShowCreateDialog(false)}
          onSessionCreated={(session) => setSessions([...sessions, session])}
        />
      )}
    </div>
  );
}
```

```typescript
// components/claude-code/SessionList.tsx
export function SessionList({ sessions }: { sessions: Session[] }) {
  return (
    <div className="sessions-grid">
      {sessions.map(session => (
        <SessionCard key={session.id} session={session} />
      ))}
    </div>
  );
}

function SessionCard({ session }: { session: Session }) {
  const navigate = useNavigate();
  
  return (
    <Card className="session-card" onClick={() => navigate(`/sessions/${session.id}`)}>
      <CardHeader>
        <div className="session-status">
          <StatusBadge status={session.status} />
          <span className="agent-count">{session.agents.length}/3 agents</span>
        </div>
        <h3>{session.name}</h3>
        {session.description && <p>{session.description}</p>}
      </CardHeader>
      
      <CardContent>
        <div className="agents-preview">
          {session.agents.slice(0, 3).map(agent => (
            <AgentAvatar key={agent.id} agent={agent} size="sm" />
          ))}
          {session.agents.length > 3 && <span>+{session.agents.length - 3}</span>}
        </div>
        
        <div className="session-meta">
          <span>Created {formatDistanceToNow(new Date(session.created_at))} ago</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

```typescript
// components/claude-code/CreateSessionDialog.tsx
export function CreateSessionDialog({ onClose, onSessionCreated }: {
  onClose: () => void;
  onSessionCreated: (session: Session) => void;
}) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    agents: [{ name: '', role: '' }] // Start with one agent
  });

  const addAgent = () => {
    if (formData.agents.length < 3) {
      setFormData({
        ...formData,
        agents: [...formData.agents, { name: '', role: '' }]
      });
    }
  };

  const removeAgent = (index: number) => {
    if (formData.agents.length > 1) {
      setFormData({
        ...formData,
        agents: formData.agents.filter((_, i) => i !== index)
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const response = await fetch('/api/v1/claude-code/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const session = await response.json();
      onSessionCreated(session);
      onClose();
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  return (
    <Dialog open onClose={onClose}>
      <DialogHeader>
        <h2>Create Multi-Agent Session</h2>
        <p>Set up a collaborative session for multiple Claude Code agents</p>
      </DialogHeader>
      
      <form onSubmit={handleSubmit}>
        <DialogContent>
          <div className="form-group">
            <label>Session Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              placeholder="e.g., WebScraper Development"
              required
            />
          </div>
          
          <div className="form-group">
            <label>Description (Optional)</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              placeholder="Brief description of the project or collaboration"
            />
          </div>
          
          <div className="agents-section">
            <div className="agents-header">
              <h3>Agents ({formData.agents.length}/3)</h3>
              {formData.agents.length < 3 && (
                <Button type="button" variant="outline" onClick={addAgent}>
                  Add Agent
                </Button>
              )}
            </div>
            
            {formData.agents.map((agent, index) => (
              <div key={index} className="agent-form">
                <div className="agent-inputs">
                  <input
                    type="text"
                    placeholder="Agent name (e.g., researcher, implementer)"
                    value={agent.name}
                    onChange={(e) => {
                      const newAgents = [...formData.agents];
                      newAgents[index].name = e.target.value;
                      setFormData({...formData, agents: newAgents});
                    }}
                    required
                  />
                  <input
                    type="text"
                    placeholder="Role (optional)"
                    value={agent.role}
                    onChange={(e) => {
                      const newAgents = [...formData.agents];
                      newAgents[index].role = e.target.value;
                      setFormData({...formData, agents: newAgents});
                    }}
                  />
                </div>
                {formData.agents.length > 1 && (
                  <Button 
                    type="button" 
                    variant="ghost" 
                    onClick={() => removeAgent(index)}
                  >
                    Remove
                  </Button>
                )}
              </div>
            ))}
          </div>
        </DialogContent>
        
        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit">
            Create Session
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
}
```

```typescript
// components/claude-code/SessionDetailView.tsx
export function SessionDetailView({ sessionId }: { sessionId: string }) {
  const [session, setSession] = useState<Session | null>(null);
  const [activeTab, setActiveTab] = useState<'agents' | 'activity' | 'settings'>('agents');

  useEffect(() => {
    fetchSession(sessionId);
  }, [sessionId]);

  return (
    <div className="session-detail">
      <SessionHeader session={session} />
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        
        <TabsContent value="agents">
          <AgentsPanel session={session} />
        </TabsContent>
        
        <TabsContent value="activity">
          <ActivityPanel session={session} />
        </TabsContent>
        
        <TabsContent value="settings">
          <SettingsPanel session={session} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AgentsPanel({ session }: { session: Session | null }) {
  if (!session) return <div>Loading...</div>;

  return (
    <div className="agents-panel">
      <div className="agents-grid">
        {session.agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} session={session} />
        ))}
      </div>
      
      {session.agents.length < 3 && (
        <Button onClick={() => addAgentToSession(session.id)}>
          Add Agent
        </Button>
      )}
    </div>
  );
}

function AgentCard({ agent, session }: { agent: Agent; session: Session }) {
  const [showUrl, setShowUrl] = useState(false);
  
  const copyConnectionUrl = () => {
    navigator.clipboard.writeText(agent.connection_url);
    toast.success('Connection URL copied to clipboard');
  };

  return (
    <Card className="agent-card">
      <CardHeader>
        <div className="agent-status">
          <StatusBadge status={agent.status} />
          <h3>{agent.name}</h3>
        </div>
        {agent.role && <p className="agent-role">{agent.role}</p>}
      </CardHeader>
      
      <CardContent>
        <div className="connection-section">
          <div className="connection-header">
            <span>Connection URL</span>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowUrl(!showUrl)}
            >
              {showUrl ? 'Hide' : 'Show'}
            </Button>
          </div>
          
          {showUrl && (
            <div className="connection-url">
              <code>{agent.connection_url}</code>
              <Button size="sm" onClick={copyConnectionUrl}>
                Copy
              </Button>
            </div>
          )}
        </div>
        
        <div className="connection-instructions">
          <p>To connect this agent:</p>
          <ol>
            <li>Copy the connection URL above</li>
            <li>Run: <code>npx install-mcp [URL] --client claude code</code></li>
            <li>Verify: <code>claude mcp list</code></li>
          </ol>
        </div>
        
        <div className="agent-meta">
          <span>Last activity: {formatDistanceToNow(new Date(agent.last_activity))} ago</span>
        </div>
      </CardContent>
    </Card>
  );
}
```

#### Backend API Endpoints

```python
# api/app/routes/claude_code_sessions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.claude_code import ClaudeCodeSession, ClaudeCodeAgent
from app.auth import get_current_user
from typing import List
import uuid

router = APIRouter(prefix="/api/v1/claude-code", tags=["claude-code-sessions"])

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all Claude Code sessions for the current user"""
    sessions = db.query(ClaudeCodeSession).filter(
        ClaudeCodeSession.user_id == current_user.id
    ).all()
    return sessions

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new multi-agent session"""
    
    # Create session
    session = ClaudeCodeSession(
        id=str(uuid.uuid4()),
        name=session_data.name,
        description=session_data.description,
        user_id=current_user.id,
        status="active"
    )
    db.add(session)
    db.flush()  # Get the session ID
    
    # Create agents
    for i, agent_data in enumerate(session_data.agents):
        agent = ClaudeCodeAgent(
            id=str(uuid.uuid4()),
            session_id=session.id,
            name=agent_data.name,
            role=agent_data.role,
            connection_url=generate_agent_connection_url(
                current_user.id, 
                session.name, 
                agent_data.name
            ),
            status="disconnected"
        )
        db.add(agent)
    
    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get session details"""
    session = db.query(ClaudeCodeSession).filter(
        ClaudeCodeSession.id == session_id,
        ClaudeCodeSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session

def generate_agent_connection_url(user_id: str, session_name: str, agent_name: str) -> str:
    """Generate MCP connection URL for an agent"""
    import urllib.parse
    
    # URL encode the session name and agent name
    encoded_session = urllib.parse.quote(session_name.lower().replace(' ', '_'))
    encoded_agent = urllib.parse.quote(agent_name.lower().replace(' ', '_'))
    
    return f"https://api.jeanmemory.com/mcp/claude%20code/sse/{user_id}/session/{encoded_session}/{encoded_agent}"

# Database Models
class ClaudeCodeSession(Base):
    __tablename__ = "claude_code_sessions"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents = relationship("ClaudeCodeAgent", back_populates="session")
    user = relationship("User", back_populates="claude_code_sessions")

class ClaudeCodeAgent(Base):
    __tablename__ = "claude_code_agents"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("claude_code_sessions.id"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String)
    connection_url = Column(String, nullable=False)
    status = Column(String, default="disconnected")  # connected, disconnected
    last_activity = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("ClaudeCodeSession", back_populates="agents")
```

#### Dashboard Route Integration

```typescript
// app/dashboard/claude-code/page.tsx
export default function ClaudeCodePage() {
  return (
    <div className="claude-code-page">
      <DashboardHeader 
        title="Claude Code Integration"
        description="Manage multi-agent Claude Code sessions and connections"
      />
      
      <div className="claude-code-content">
        <div className="quick-start-section">
          <h3>Quick Start</h3>
          <p>Connect Claude Code to Jean Memory for persistent memory across coding sessions.</p>
          
          <div className="connection-modes">
            <Card className="mode-card">
              <CardHeader>
                <h4>Single Agent Mode</h4>
                <p>Standard Claude Code connection</p>
              </CardHeader>
              <CardContent>
                <code>
                  npx install-mcp https://api.jeanmemory.com/mcp/claude%20code/sse/{currentUser.id} --client claude code
                </code>
                <Button variant="outline" onClick={() => copyToClipboard(singleAgentUrl)}>
                  Copy URL
                </Button>
              </CardContent>
            </Card>
            
            <Card className="mode-card">
              <CardHeader>
                <h4>Multi-Agent Mode</h4>
                <p>Collaborative sessions with multiple agents</p>
              </CardHeader>
              <CardContent>
                <p>Create sessions below to generate agent-specific connection URLs</p>
              </CardContent>
            </Card>
          </div>
        </div>
        
        <SessionManager />
      </div>
    </div>
  );
}
```

## Usage Instructions

### Frontend Session Management

Users can now manage Claude Code multi-agent sessions directly from the Jean Memory dashboard:

1. **Navigate to Claude Code section** in the dashboard
2. **Create New Session** - Click the "Create New Session" button
3. **Configure Session** - Add session name, description, and up to 3 agents
4. **Get Connection URLs** - Each agent gets a unique MCP connection URL
5. **Connect Agents** - Use the provided URLs to connect Claude Code instances

### Single Agent Mode (Existing - No Changes)

```bash
# Standard Claude Code connection (unchanged)
npx install-mcp https://api.jeanmemory.com/mcp/claude code/sse/fa97efb5-410d-4806-b137-8cf13b6cb464 --client claude code

# Verify connection
claude mcp list
```

**Available Tools**: `@jean_memory`, `@search_memory`, `@ask_memory`, `@store_document`, `@add_memories`, `@list_memories`, `@deep_memory_query`

### Multi-Agent Session Mode (New Feature)

```bash
# Research Agent
npx install-mcp https://api.jeanmemory.com/mcp/claude%20code/sse/fa97efb5-410d-4806-b137-8cf13b6cb464/session/webscraper_dev/research --client claude code

# Implementation Agent  
npx install-mcp https://api.jeanmemory.com/mcp/claude%20code/sse/fa97efb5-410d-4806-b137-8cf13b6cb464/session/webscraper_dev/implementation --client claude code

# Verify both connections
claude mcp list
```

**Available Tools**: All standard tools + `@claim_files`, `@release_files`, `@sync_codebase`, `@broadcast_message`, `@get_agent_messages`

## Multi-Agent Workflow Example

### Research Agent Workflow

```python
# Start each session by checking for updates
@sync_codebase(60)

# Claim files before making changes
@claim_files(
    file_paths=["README.md", "requirements.txt", "docs/api.md"], 
    operation="write", 
    duration_minutes=20
)

# Make your changes to the files...

# Release files and notify others
@release_files(
    file_paths=["README.md", "requirements.txt", "docs/api.md"],
    changes_summary="Updated project documentation and added BeautifulSoup dependency",
    structural_changes=["Added dependency: beautifulsoup4==4.12.2", "New API documentation section"]
)

# Coordinate with implementation team
@broadcast_message(
    message="Research phase complete. BeautifulSoup added as dependency. Implementation can begin with basic scraping patterns.",
    message_type="coordination"
)
```

### Implementation Agent Workflow

```python
# Check for recent changes before starting
@sync_codebase(90)
# Output: Shows research agent's recent changes

# Check for coordination messages
@get_agent_messages(5)
# Output: Shows research agent's coordination message

# Claim implementation files
@claim_files(
    file_paths=["src/scraper.py", "src/parser.py", "tests/test_scraper.py"],
    operation="create",
    duration_minutes=45
)

# Implement the features...

# Release and notify
@release_files(
    file_paths=["src/scraper.py", "src/parser.py", "tests/test_scraper.py"],
    changes_summary="Implemented basic web scraper with BeautifulSoup integration and unit tests",
    structural_changes=["New module: scraper.py", "New module: parser.py", "Added test suite"]
)

# Ask question to research agent
@broadcast_message(
    message="Basic scraper implemented. Should I proceed with rate limiting implementation or wait for more research on target sites?",
    message_type="question"
)
```

## Client Isolation Guarantees

### What Other MCP Clients See

**ChatGPT, Cursor, VS Code, etc.** connecting with any user_id format:
- ✅ Standard tools only: `jean_memory`, `search_memory`, `ask_memory`, etc.
- ✅ No session tools visible in schema
- ✅ Session tools return error if somehow called
- ✅ Normal memory isolation (unchanged)
- ✅ Zero impact on existing functionality

### What Claude Code Sees

**Standard connection** (`claude code/sse/{user_id}`):
- ✅ Standard tools only (backward compatible)
- ❌ No session tools visible

**Session connection** (`claude code/sse/{user_id}/session/{session_name}/{agent_id}`):
- ✅ All standard tools (full compatibility)
- ✅ Additional session coordination tools
- ✅ Enhanced tool descriptions mentioning multi-agent mode
- ✅ Isolated memory space per session

## Implementation Safety

1. **Zero Breaking Changes**: All existing connections work unchanged
2. **Client Isolation**: Session features exclusively for Claude Code
3. **Graceful Degradation**: Invalid session formats fall back to standard mode
4. **Memory Isolation**: Each session gets its own virtual user space
5. **Error Handling**: Clear error messages for unsupported operations
6. **Performance**: No overhead for non-session connections

## Technical Implementation Checklist

- [ ] **Update MCP routing** with client-aware session detection
- [ ] **Enhance ClaudeProfile** with conditional session tools
- [ ] **Create session coordination tools** with client validation
- [ ] **Add context variables** for session state
- [ ] **Test backward compatibility** with existing Claude Code connections
- [ ] **Test client isolation** with ChatGPT/Cursor connections
- [ ] **Update documentation** with new URL patterns
- [ ] **Deploy with feature flag** for gradual rollout

## Deployment Strategy

1. **Phase 1**: Deploy with session detection (no visible changes)
2. **Phase 2**: Enable session tools for Claude Code beta users
3. **Phase 3**: Full rollout with documentation update
4. **Phase 4**: Monitor usage and gather feedback

This implementation ensures multi-agent coordination features are exclusively available to Claude Code while maintaining complete compatibility with all existing MCP clients and connections.