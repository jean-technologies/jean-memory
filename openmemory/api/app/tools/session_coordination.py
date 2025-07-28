"""
Session coordination tools for Claude Code multi-agent support.
Uses existing memory system for lightweight coordination.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid
from app.mcp_instance import mcp
from app.context import user_id_var, client_name_var
from .memory import add_memories, search_memory

logger = logging.getLogger(__name__)


def _validate_session_context() -> tuple[bool, Optional[str], Optional[Dict]]:
    """Validate that we're in a Claude Code session context."""
    client_name = client_name_var.get()
    if client_name != "claude code":
        return False, "This tool is only available for Claude Code", None
    
    user_id = user_id_var.get()
    if not user_id or "__session__" not in user_id:
        return False, "This tool is only available in multi-agent session mode", None
    
    # Parse session info
    parts = user_id.split("__")
    if len(parts) >= 4:
        session_info = {
            "base_user_id": parts[0],
            "session_name": parts[2],
            "agent_id": parts[3],
            "virtual_user_id": user_id
        }
        return True, None, session_info
    
    return False, "Invalid session format", None


@mcp.tool(description="🔒 [Claude Code Sessions] Claim exclusive access to files to prevent conflicts with other agents")
async def session_claim_files(
    file_paths: List[str],
    operation: str = "write",
    duration_minutes: int = 30
) -> Dict:
    """
    Claim files to prevent conflicts between agents in the same session.
    Uses memory system for lightweight distributed locking.
    """
    valid, error, session_info = _validate_session_context()
    if not valid:
        return {"error": error}
    
    user_id = session_info["virtual_user_id"]
    agent_id = session_info["agent_id"]
    
    # Check for existing locks
    conflicts = []
    for file_path in file_paths:
        search_results = await search_memory(
            query=f"SESSION_LOCK:{file_path}",
            user_id=user_id,
            limit=5
        )
        
        # Check if any locks are still active
        for result in search_results:
            content = result.get("content", "")
            if f"SESSION_LOCK:{file_path}:" in content:
                try:
                    # Extract lock data
                    lock_json = content.split(":", 2)[2]
                    lock_data = json.loads(lock_json)
                    
                    # Check if lock is still valid
                    expires_at = datetime.fromisoformat(lock_data.get("expires_at", ""))
                    if expires_at > datetime.utcnow():
                        if lock_data.get("agent_id") != agent_id:
                            conflicts.append({
                                "file": file_path,
                                "locked_by": lock_data.get("agent_id"),
                                "operation": lock_data.get("operation"),
                                "expires_in": int((expires_at - datetime.utcnow()).total_seconds() / 60)
                            })
                except Exception as e:
                    logger.warning(f"Failed to parse lock data: {e}")
                    continue
    
    if conflicts:
        return {
            "success": False,
            "conflicts": conflicts,
            "message": "Some files are locked by other agents. Coordinate with them or wait for locks to expire."
        }
    
    # Create locks for all requested files
    lock_id = uuid.uuid4().hex[:8]
    lock_data = {
        "lock_id": lock_id,
        "agent_id": agent_id,
        "operation": operation,
        "locked_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat()
    }
    
    # Store locks in memory
    memories = []
    for file_path in file_paths:
        memories.append(f"SESSION_LOCK:{file_path}:{json.dumps(lock_data)}")
    
    await add_memories(memories=memories, user_id=user_id)
    
    logger.info(f"Agent {agent_id} claimed {len(file_paths)} files for {operation} operation")
    
    return {
        "success": True,
        "lock_id": lock_id,
        "locked_files": file_paths,
        "operation": operation,
        "expires_in_minutes": duration_minutes,
        "agent_id": agent_id
    }


@mcp.tool(description="🔓 [Claude Code Sessions] Release file locks and notify other agents about changes")
async def session_release_files(
    file_paths: List[str],
    changes_summary: str,
    structural_changes: Optional[List[str]] = None
) -> Dict:
    """
    Release file locks and broadcast changes to other agents.
    """
    valid, error, session_info = _validate_session_context()
    if not valid:
        return {"error": error}
    
    user_id = session_info["virtual_user_id"]
    agent_id = session_info["agent_id"]
    
    # Create release records and change notification
    change_id = uuid.uuid4().hex[:8]
    change_data = {
        "change_id": change_id,
        "agent_id": agent_id,
        "file_paths": file_paths,
        "changes_summary": changes_summary,
        "structural_changes": structural_changes or [],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store release and change records
    memories = []
    
    # Release records for each file
    for file_path in file_paths:
        release_data = {
            "agent_id": agent_id,
            "released_at": datetime.utcnow().isoformat()
        }
        memories.append(f"SESSION_RELEASE:{file_path}:{json.dumps(release_data)}")
    
    # Single change notification
    memories.append(f"SESSION_CHANGE:{json.dumps(change_data)}")
    
    await add_memories(memories=memories, user_id=user_id)
    
    logger.info(f"Agent {agent_id} released {len(file_paths)} files and broadcasted changes")
    
    return {
        "success": True,
        "change_id": change_id,
        "released_files": file_paths,
        "message": "Files released and changes broadcasted to other agents"
    }


@mcp.tool(description="🔄 [Claude Code Sessions] Get recent changes made by other agents in this session")
async def session_sync_changes(
    minutes: int = 30,
    include_own_changes: bool = False
) -> Dict:
    """
    Check for recent changes by other agents to stay synchronized.
    """
    valid, error, session_info = _validate_session_context()
    if not valid:
        return {"error": error}
    
    user_id = session_info["virtual_user_id"]
    current_agent = session_info["agent_id"]
    session_name = session_info["session_name"]
    
    # Search for recent changes
    search_results = await search_memory(
        query="SESSION_CHANGE:",
        user_id=user_id,
        limit=100
    )
    
    changes = []
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    for result in search_results:
        content = result.get("content", "")
        if "SESSION_CHANGE:" in content:
            try:
                change_json = content.split(":", 1)[1]
                change_data = json.loads(change_json)
                
                # Filter by time
                change_time = datetime.fromisoformat(change_data.get("timestamp", ""))
                if change_time < cutoff_time:
                    continue
                
                # Filter own changes unless requested
                if not include_own_changes and change_data.get("agent_id") == current_agent:
                    continue
                
                # Add time ago for readability
                time_ago = datetime.utcnow() - change_time
                change_data["time_ago_minutes"] = int(time_ago.total_seconds() / 60)
                
                changes.append(change_data)
                
            except Exception as e:
                logger.warning(f"Failed to parse change data: {e}")
                continue
    
    # Sort by timestamp (most recent first)
    changes.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Limit results
    changes = changes[:20]
    
    # Get current file locks
    lock_search = await search_memory(
        query="SESSION_LOCK:",
        user_id=user_id,
        limit=50
    )
    
    active_locks = []
    for result in lock_search:
        content = result.get("content", "")
        if "SESSION_LOCK:" in content:
            try:
                parts = content.split(":", 2)
                if len(parts) >= 3:
                    file_path = parts[1]
                    lock_data = json.loads(parts[2])
                    
                    expires_at = datetime.fromisoformat(lock_data.get("expires_at", ""))
                    if expires_at > datetime.utcnow():
                        active_locks.append({
                            "file": file_path,
                            "locked_by": lock_data.get("agent_id"),
                            "operation": lock_data.get("operation"),
                            "expires_in_minutes": int((expires_at - datetime.utcnow()).total_seconds() / 60)
                        })
            except:
                continue
    
    return {
        "session_name": session_name,
        "current_agent": current_agent,
        "recent_changes": changes,
        "total_changes": len(changes),
        "time_window_minutes": minutes,
        "active_file_locks": active_locks,
        "recommendation": "Review changes before modifying files" if changes else "No recent changes detected"
    }


@mcp.tool(description="📢 [Claude Code Sessions] Send a coordination message to other agents")
async def session_message(
    message: str,
    message_type: str = "info"
) -> Dict:
    """
    Send a message to other agents for coordination.
    Message types: info, warning, question, request
    """
    valid, error, session_info = _validate_session_context()
    if not valid:
        return {"error": error}
    
    user_id = session_info["virtual_user_id"]
    agent_id = session_info["agent_id"]
    
    message_data = {
        "message_id": uuid.uuid4().hex[:8],
        "from_agent": agent_id,
        "message": message,
        "message_type": message_type,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await add_memories(
        memories=[f"SESSION_MESSAGE:{json.dumps(message_data)}"],
        user_id=user_id
    )
    
    return {
        "success": True,
        "message_id": message_data["message_id"],
        "message": "Message sent to other agents"
    }


@mcp.tool(description="📬 [Claude Code Sessions] Check messages from other agents")
async def session_check_messages(
    minutes: int = 60,
    message_types: Optional[List[str]] = None
) -> Dict:
    """
    Check for messages from other agents.
    """
    valid, error, session_info = _validate_session_context()
    if not valid:
        return {"error": error}
    
    user_id = session_info["virtual_user_id"]
    current_agent = session_info["agent_id"]
    
    search_results = await search_memory(
        query="SESSION_MESSAGE:",
        user_id=user_id,
        limit=50
    )
    
    messages = []
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    for result in search_results:
        content = result.get("content", "")
        if "SESSION_MESSAGE:" in content:
            try:
                message_json = content.split(":", 1)[1]
                message_data = json.loads(message_json)
                
                # Filter by time
                message_time = datetime.fromisoformat(message_data.get("timestamp", ""))
                if message_time < cutoff_time:
                    continue
                
                # Filter by message type if specified
                if message_types and message_data.get("message_type") not in message_types:
                    continue
                
                # Skip own messages
                if message_data.get("from_agent") == current_agent:
                    continue
                
                # Add time ago
                time_ago = datetime.utcnow() - message_time
                message_data["time_ago_minutes"] = int(time_ago.total_seconds() / 60)
                
                messages.append(message_data)
                
            except Exception as e:
                logger.warning(f"Failed to parse message data: {e}")
                continue
    
    # Sort by timestamp (most recent first)
    messages.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "messages": messages[:20],
        "total_messages": len(messages),
        "time_window_minutes": minutes,
        "current_agent": current_agent
    }