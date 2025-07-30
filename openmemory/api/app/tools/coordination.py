import json
import logging
import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import text
from app.database import get_db
from app.context import user_id_var
from app.mcp_instance import mcp

logger = logging.getLogger(__name__)

# ===============================================
# PLANNING TOOLS (PLANNER AGENT ONLY)
# ===============================================

@mcp.tool(description="📊 PLANNING: Analyze task conflicts and file dependencies for optimal 2-5 agent distribution. Determines file collision risks and creates scalable agent assignment strategy.")
async def analyze_task_conflicts(
    tasks: List[str], 
    project_files: List[str] = [], 
    complexity_level: str = "moderate"
) -> Dict[str, Any]:
    """
    Analyze task conflicts and file dependencies for optimal 2-5 agent distribution.
    Determines file collision risks and creates scalable agent assignment strategy.
    """
    logger.info(f"🎯 Analyzing task conflicts: {len(tasks)} tasks, {len(project_files)} files, complexity: {complexity_level}")
    
    try:
        # Analyze file dependencies and potential conflicts
        file_dependencies = {}
        conflict_matrix = {}
        
        # Group files by directory/module to identify related work
        file_groups = {}
        for file_path in project_files:
            parts = file_path.split('/')
            if len(parts) > 1:
                group = '/'.join(parts[:-1])  # Directory path
                if group not in file_groups:
                    file_groups[group] = []
                file_groups[group].append(file_path)
        
        # Analyze task-file relationships
        task_file_map = {}
        for i, task in enumerate(tasks):
            task_file_map[f"task_{i}"] = {
                "description": task,
                "estimated_files": [f for f in project_files if any(keyword in f.lower() for keyword in task.lower().split()[:3])],
                "priority": "high" if any(word in task.lower() for word in ["critical", "urgent", "fix", "bug"]) else "medium"
            }
        
        # Determine optimal agent count based on complexity and task count
        if complexity_level == "simple" or len(tasks) <= 3:
            optimal_agents = 2
        elif complexity_level == "complex" or len(tasks) >= 8:
            optimal_agents = min(5, max(2, len(tasks) // 2))
        else:
            # Moderate complexity: scale with task count but ensure minimum 3 for "moderate"
            if complexity_level == "moderate":
                optimal_agents = max(3, min(5, len(tasks) // 2 + 1))
            else:
                optimal_agents = min(3, max(2, len(tasks) // 2))
        
        # Identify potential conflicts
        conflicts = []
        for i, (task_a, data_a) in enumerate(task_file_map.items()):
            for j, (task_b, data_b) in enumerate(task_file_map.items()):
                if i < j:  # Avoid duplicate comparisons
                    shared_files = set(data_a["estimated_files"]) & set(data_b["estimated_files"])
                    if shared_files:
                        conflicts.append({
                            "task_a": task_a,
                            "task_b": task_b,
                            "shared_files": list(shared_files),
                            "conflict_level": "high" if len(shared_files) > 1 else "medium"
                        })
        
        analysis_result = {
            "optimal_agent_count": optimal_agents,
            "task_count": len(tasks),
            "file_count": len(project_files),
            "complexity_level": complexity_level,
            "task_file_mapping": task_file_map,
            "file_groups": file_groups,
            "potential_conflicts": conflicts,
            "conflict_count": len(conflicts),
            "recommendations": [
                f"Recommended agent count: {optimal_agents} (2 minimum, 5 maximum)",
                f"High-priority tasks: {len([t for t in task_file_map.values() if t['priority'] == 'high'])}",
                f"File conflicts detected: {len(conflicts)}",
                "Assign conflicting tasks to same agent or sequence them",
                "Use file locking for shared resources"
            ],
            "scalability_notes": {
                "2_agents": "Minimal setup - good for simple projects with few conflicts",
                "3_agents": "Optimal balance - recommended for most projects", 
                "4_agents": "High parallelism - good for complex projects with independent modules",
                "5_agents": "Maximum parallelism - use only for very large, modular projects"
            },
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        logger.info(f"🎯 Analysis complete: {optimal_agents} agents recommended, {len(conflicts)} conflicts detected")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error analyzing task conflicts: {e}")
        return {
            "error": str(e),
            "optimal_agent_count": 2,  # Safe fallback
            "recommendations": ["Use 2 agents due to analysis error", "Manual coordination required"]
        }


@mcp.tool(description="📋 PLANNING: Generate terminal-specific prompts and coordination setup for 2-5 implementer agents. Creates MCP connection commands and implementation prompts.")
async def create_task_distribution(
    analysis_result: Dict[str, Any], 
    preferred_agent_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate terminal-specific prompts and coordination setup for 2-5 implementer agents 
    based on conflict analysis.
    """
    logger.info(f"🎯 Creating task distribution for {analysis_result.get('task_count', 0)} tasks")
    
    try:
        # Use preferred count or fall back to analysis recommendation
        agent_count = preferred_agent_count or analysis_result.get("optimal_agent_count", 2)
        agent_count = max(2, min(5, agent_count))  # Enforce 2-5 range
        
        task_mapping = analysis_result.get("task_file_mapping", {})
        conflicts = analysis_result.get("potential_conflicts", [])
        file_groups = analysis_result.get("file_groups", {})
        
        # Create agent assignments
        agents = {}
        for i in range(agent_count):
            agent_id = f"impl_{chr(97 + i)}"  # impl_a, impl_b, etc.
            agents[agent_id] = {
                "agent_id": agent_id,
                "assigned_tasks": [],
                "assigned_files": [],
                "priority_level": "medium",
                "coordination_notes": []
            }
        
        # Distribute tasks while avoiding conflicts
        assigned_tasks = set()
        conflict_pairs = set()
        
        # Build conflict pairs for reference
        for conflict in conflicts:
            conflict_pairs.add((conflict["task_a"], conflict["task_b"]))
            conflict_pairs.add((conflict["task_b"], conflict["task_a"]))
        
        # Assign high-priority tasks first
        high_priority_tasks = [task_id for task_id, data in task_mapping.items() if data["priority"] == "high"]
        agent_idx = 0
        
        for task_id in high_priority_tasks:
            if task_id not in assigned_tasks:
                agent_id = f"impl_{chr(97 + agent_idx)}"
                agents[agent_id]["assigned_tasks"].append(task_id)
                agents[agent_id]["assigned_files"].extend(task_mapping[task_id]["estimated_files"])
                agents[agent_id]["priority_level"] = "high"
                assigned_tasks.add(task_id)
                
                # Check for conflicting tasks and assign to same agent
                conflicting_tasks = [conf["task_b"] if conf["task_a"] == task_id else conf["task_a"] 
                                   for conf in conflicts if task_id in [conf["task_a"], conf["task_b"]]]
                
                for conflicting_task in conflicting_tasks:
                    if conflicting_task not in assigned_tasks:
                        agents[agent_id]["assigned_tasks"].append(conflicting_task)
                        agents[agent_id]["assigned_files"].extend(task_mapping[conflicting_task]["estimated_files"])
                        agents[agent_id]["coordination_notes"].append(f"Handles conflicting task {conflicting_task}")
                        assigned_tasks.add(conflicting_task)
                
                agent_idx = (agent_idx + 1) % agent_count
        
        # Assign remaining tasks
        remaining_tasks = [task_id for task_id in task_mapping.keys() if task_id not in assigned_tasks]
        agent_idx = 0
        
        for task_id in remaining_tasks:
            agent_id = f"impl_{chr(97 + agent_idx)}"
            agents[agent_id]["assigned_tasks"].append(task_id)
            agents[agent_id]["assigned_files"].extend(task_mapping[task_id]["estimated_files"])
            assigned_tasks.add(task_id)
            agent_idx = (agent_idx + 1) % agent_count
        
        # Remove duplicate files and add coordination notes
        for agent_data in agents.values():
            agent_data["assigned_files"] = list(set(agent_data["assigned_files"]))
            agent_data["file_count"] = len(agent_data["assigned_files"])
            agent_data["task_count"] = len(agent_data["assigned_tasks"])
        
        # Generate terminal setup commands
        session_id = f"multi_project_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            user_id = user_id_var.get()
        except LookupError:
            # Fallback for testing without proper context
            user_id = "test_user"
        
        terminal_commands = {
            "planner": f"claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__planner"
        }
        
        for agent_id in agents.keys():
            terminal_commands[agent_id] = f"claude mcp add --transport http jean-memory https://jean-memory-api-dev.onrender.com/mcp/v2/claude/{user_id}__session__{session_id}__{agent_id}"
        
        # Generate agent-specific prompts
        agent_prompts = {}
        for agent_id, agent_data in agents.items():
            task_descriptions = [task_mapping[task_id]["description"] for task_id in agent_data["assigned_tasks"]]
            
            agent_prompts[agent_id] = f"""# Multi-Agent Development Session - {agent_id.upper()}

## Your Role
You are implementation agent `{agent_id}` in a {agent_count}-agent development team.

## Session Info
- Session ID: {session_id}
- Your Agent ID: {agent_id}
- Total Agents: {agent_count} (1 planner + {agent_count-1} implementers)

## Your Assigned Tasks ({agent_data['task_count']} tasks):
{chr(10).join([f"- {desc}" for desc in task_descriptions])}

## Your File Scope ({agent_data['file_count']} files):
{chr(10).join([f"- {file}" for file in agent_data['assigned_files']])}

## Coordination Tools Available:
- `claim_file_lock`: Lock files before editing to prevent conflicts
- `sync_progress`: Update other agents on your progress
- `check_agent_status`: See what other agents are doing

## Important Rules:
1. ALWAYS use `claim_file_lock` before editing files
2. Update progress with `sync_progress` at key milestones
3. Check other agents' status if you need files they might be using
4. Focus only on your assigned tasks unless coordination is needed

## Priority Level: {agent_data['priority_level'].upper()}
"""
            
            if agent_data["coordination_notes"]:
                agent_prompts[agent_id] += f"\n## Coordination Notes:\n" + "\n".join([f"- {note}" for note in agent_data["coordination_notes"]])
        
        distribution_result = {
            "session_id": session_id,
            "agent_count": agent_count,
            "agents": agents,
            "terminal_commands": terminal_commands,
            "agent_prompts": agent_prompts,
            "coordination_strategy": {
                "conflict_resolution": "Assign conflicting tasks to same agent",
                "file_locking": "Required for all file modifications",
                "progress_sync": "Report at task start, 50%, and completion",
                "communication": "Use coordination tools for status updates"
            },
            "setup_instructions": [
                "1. Copy and run terminal commands in separate terminals",
                "2. Paste agent-specific prompts in each terminal",
                "3. Planner coordinates and monitors progress",
                "4. Implementers focus on assigned tasks",
                "5. Use coordination tools to prevent conflicts"
            ],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        logger.info(f"🎯 Task distribution created: {agent_count} agents, session {session_id}")
        return distribution_result
        
    except Exception as e:
        logger.error(f"Error creating task distribution: {e}")
        return {
            "error": str(e),
            "agent_count": 2,
            "setup_instructions": ["Use manual coordination due to distribution error"]
        }


# ===============================================
# EXECUTION COORDINATION TOOLS (ALL AGENTS)
# ===============================================

@mcp.tool(description="🔒 COORDINATION: Create cross-session file locks via database for scalable multi-agent coordination. Prevents file conflicts across 2-5 terminals.")
async def claim_file_lock(
    file_paths: List[str], 
    operation: str = "write", 
    duration_minutes: int = 15
) -> Dict[str, Any]:
    """
    Create cross-session file locks via database for scalable multi-agent coordination.
    Prevents file conflicts across 2-5 terminals.
    """
    logger.info(f"🔒 Claiming locks for {len(file_paths)} files, operation: {operation}")
    
    try:
        user_id = user_id_var.get()
        db = next(get_db())
        
        # Parse current agent context from user_id (should be virtual user ID)
        if "__session__" in user_id:
            parts = user_id.split("__session__")
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            session_id = session_agent[0]
            agent_id = session_agent[1]
        else:
            # Fallback for non-multi-agent sessions
            real_user_id = user_id
            session_id = "single_user"
            agent_id = "default"
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        expiry_time = current_time + datetime.timedelta(minutes=duration_minutes)
        
        # Check for existing locks
        existing_locks = {}
        conflicts = []
        
        for file_path in file_paths:
            result = db.execute(
                text("""
                    SELECT agent_id, operation, expires_at, created_at
                    FROM file_locks 
                    WHERE file_path = :file_path 
                      AND expires_at > :current_time
                      AND session_id = :session_id
                """),
                {
                    "file_path": file_path,
                    "current_time": current_time,
                    "session_id": session_id
                }
            ).fetchone()
            
            if result:
                lock_agent_id, lock_operation, expires_at, created_at = result
                if lock_agent_id != agent_id:  # Lock held by different agent
                    conflicts.append({
                        "file_path": file_path,
                        "locked_by": lock_agent_id,
                        "operation": lock_operation,
                        "expires_at": expires_at.isoformat(),
                        "time_remaining_minutes": int((expires_at - current_time).total_seconds() / 60)
                    })
                else:
                    existing_locks[file_path] = {
                        "operation": lock_operation,
                        "expires_at": expires_at.isoformat(),
                        "status": "already_owned"
                    }
        
        # If there are conflicts, return them without claiming locks
        if conflicts:
            logger.warning(f"🔒 Lock conflicts detected for agent {agent_id}: {len(conflicts)} files")
            return {
                "success": False,
                "conflicts": conflicts,
                "message": f"Cannot claim locks due to {len(conflicts)} conflicts",
                "recommendations": [
                    "Wait for existing locks to expire",
                    "Coordinate with lock-holding agents", 
                    "Use check_agent_status to see what other agents are doing"
                ]
            }
        
        # Claim locks for files without conflicts
        successfully_locked = []
        failed_locks = []
        
        for file_path in file_paths:
            if file_path in existing_locks:
                # Extend existing lock
                db.execute(
                    text("""
                        UPDATE file_locks 
                        SET expires_at = :expiry_time, operation = :operation
                        WHERE file_path = :file_path 
                          AND agent_id = :agent_id 
                          AND session_id = :session_id
                    """),
                    {
                        "file_path": file_path,
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "expiry_time": expiry_time,
                        "operation": operation
                    }
                )
                successfully_locked.append({
                    "file_path": file_path,
                    "status": "extended",
                    "expires_at": expiry_time.isoformat(),
                    "operation": operation
                })
            else:
                # Create new lock
                try:
                    db.execute(
                        text("""
                            INSERT INTO file_locks (session_id, agent_id, file_path, operation, expires_at, created_at)
                            VALUES (:session_id, :agent_id, :file_path, :operation, :expires_at, :created_at)
                        """),
                        {
                            "session_id": session_id,
                            "agent_id": agent_id,
                            "file_path": file_path,
                            "operation": operation,
                            "expires_at": expiry_time,
                            "created_at": current_time
                        }
                    )
                    successfully_locked.append({
                        "file_path": file_path,
                        "status": "locked",
                        "expires_at": expiry_time.isoformat(),
                        "operation": operation
                    })
                except Exception as e:
                    failed_locks.append({
                        "file_path": file_path,
                        "error": str(e)
                    })
        
        db.commit()
        
        result = {
            "success": len(successfully_locked) > 0,
            "agent_id": agent_id,
            "session_id": session_id,
            "locked_files": successfully_locked,
            "failed_locks": failed_locks,
            "duration_minutes": duration_minutes,
            "expires_at": expiry_time.isoformat(),
            "message": f"Successfully locked {len(successfully_locked)} files for agent {agent_id}"
        }
        
        logger.info(f"🔒 File locks claimed: {len(successfully_locked)} successful, {len(failed_locks)} failed")
        return result
        
    except Exception as e:
        logger.error(f"Error claiming file locks: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to claim file locks due to database error"
        }
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass


@mcp.tool(description="📢 COORDINATION: Broadcast progress updates across all terminals in session. Enables real-time coordination for 2-5 agents.")
async def sync_progress(
    task_id: str, 
    status: str, 
    progress_percentage: Optional[int] = None,
    message: Optional[str] = None,
    affected_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Broadcast progress updates across all terminals in session.
    Enables real-time status sync for 2-5 agent coordination.
    """
    logger.info(f"📡 Syncing progress: task {task_id}, status {status}")
    
    try:
        user_id = user_id_var.get()
        db = next(get_db())
        
        # Parse current agent context from user_id
        if "__session__" in user_id:
            parts = user_id.split("__session__")
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            session_id = session_agent[0]
            agent_id = session_agent[1]
        else:
            real_user_id = user_id
            session_id = "single_user"
            agent_id = "default"
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Store progress update in database
        try:
            # Try to update existing progress record
            update_result = db.execute(
                text("""
                    UPDATE task_progress 
                    SET status = :status, 
                        progress_percentage = :progress_percentage,
                        message = :message,
                        affected_files = :affected_files,
                        updated_at = :updated_at
                    WHERE session_id = :session_id 
                      AND agent_id = :agent_id 
                      AND task_id = :task_id
                """),
                {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "task_id": task_id,
                    "status": status,
                    "progress_percentage": progress_percentage,
                    "message": message,
                    "affected_files": json.dumps(affected_files) if affected_files else None,
                    "updated_at": current_time
                }
            )
            
            # If no existing record, create new one
            if update_result.rowcount == 0:
                db.execute(
                    text("""
                        INSERT INTO task_progress (session_id, agent_id, task_id, status, progress_percentage, message, affected_files, created_at, updated_at)
                        VALUES (:session_id, :agent_id, :task_id, :status, :progress_percentage, :message, :affected_files, :created_at, :updated_at)
                    """),
                    {
                        "session_id": session_id,
                        "agent_id": agent_id,
                        "task_id": task_id,
                        "status": status,
                        "progress_percentage": progress_percentage,
                        "message": message,
                        "affected_files": json.dumps(affected_files) if affected_files else None,
                        "created_at": current_time,
                        "updated_at": current_time
                    }
                )
            
            db.commit()
            
            # Get current session progress for context
            session_progress = db.execute(
                text("""
                    SELECT agent_id, task_id, status, progress_percentage, message, updated_at
                    FROM task_progress 
                    WHERE session_id = :session_id
                    ORDER BY updated_at DESC
                    LIMIT 10
                """),
                {"session_id": session_id}
            ).fetchall()
            
            progress_summary = []
            for row in session_progress:
                progress_summary.append({
                    "agent_id": row[0],
                    "task_id": row[1],
                    "status": row[2],
                    "progress_percentage": row[3],
                    "message": row[4],
                    "updated_at": row[5].isoformat() if row[5] else None
                })
            
            result = {
                "success": True,
                "agent_id": agent_id,
                "session_id": session_id,
                "task_id": task_id,
                "status": status,
                "progress_percentage": progress_percentage,
                "message": message,
                "affected_files": affected_files or [],
                "timestamp": current_time.isoformat(),
                "session_progress": progress_summary,
                "sync_message": f"Progress synced: {agent_id} - {task_id} - {status}"
            }
            
            logger.info(f"📡 Progress synced successfully: {agent_id} - {task_id} - {status}")
            return result
            
        except Exception as e:
            logger.error(f"Error storing progress update: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to sync progress due to database error"
            }
        
    except Exception as e:
        logger.error(f"Error syncing progress: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to sync progress"
        }
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass


@mcp.tool(description="👥 COORDINATION: Check status of all other agents in the same session. Provides real-time visibility across 2-5 terminals.")
async def check_agent_status(include_inactive: bool = False) -> Dict[str, Any]:
    """
    Check status of all other agents in the same session.
    Provides real-time visibility across 2-5 terminals.
    """
    logger.info(f"👥 Checking agent status, include_inactive: {include_inactive}")
    
    try:
        user_id = user_id_var.get()
        db = next(get_db())
        
        # Parse current agent context from user_id
        if "__session__" in user_id:
            parts = user_id.split("__session__")
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            session_id = session_agent[0]
            current_agent_id = session_agent[1]
        else:
            real_user_id = user_id
            session_id = "single_user"
            current_agent_id = "default"
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        activity_threshold = current_time - datetime.timedelta(minutes=10)  # Last 10 minutes
        
        # Get all agents in the session
        agent_query = """
            SELECT id, name, connection_url, status, last_activity, created_at
            FROM claude_code_agents 
            WHERE session_id = :session_id
        """
        
        if not include_inactive:
            agent_query += " AND last_activity >= :activity_threshold"
        
        agent_query += " ORDER BY last_activity DESC"
        
        query_params = {"session_id": session_id}
        if not include_inactive:
            query_params["activity_threshold"] = activity_threshold
        
        agent_results = db.execute(text(agent_query), query_params).fetchall()
        
        # Get recent progress updates for context
        progress_results = db.execute(
            text("""
                SELECT agent_id, task_id, status, progress_percentage, message, updated_at
                FROM task_progress 
                WHERE session_id = :session_id
                  AND updated_at >= :activity_threshold
                ORDER BY updated_at DESC
            """),
            {"session_id": session_id, "activity_threshold": activity_threshold}
        ).fetchall()
        
        # Get active file locks
        lock_results = db.execute(
            text("""
                SELECT agent_id, file_path, operation, expires_at
                FROM file_locks 
                WHERE session_id = :session_id
                  AND expires_at > :current_time
                ORDER BY expires_at ASC
            """),
            {"session_id": session_id, "current_time": current_time}
        ).fetchall()
        
        # Process agent information
        agents = []
        for row in agent_results:
            agent_db_id, name, connection_url, status, last_activity, created_at = row
            is_current = (name == current_agent_id)
            
            # Calculate activity status
            if last_activity:
                minutes_since_activity = int((current_time - last_activity).total_seconds() / 60)
                if minutes_since_activity <= 2:
                    activity_status = "active"
                elif minutes_since_activity <= 10:
                    activity_status = "recent"
                else:
                    activity_status = "inactive"
            else:
                activity_status = "unknown"
            
            # Get agent's recent progress
            agent_progress = [
                {
                    "task_id": p[1],
                    "status": p[2],
                    "progress_percentage": p[3],
                    "message": p[4],
                    "updated_at": p[5].isoformat() if p[5] else None
                }
                for p in progress_results if p[0] == name
            ]
            
            # Get agent's active locks
            agent_locks = [
                {
                    "file_path": l[1],
                    "operation": l[2],
                    "expires_at": l[3].isoformat() if l[3] else None,
                    "minutes_remaining": int((l[3] - current_time).total_seconds() / 60) if l[3] else 0
                }
                for l in lock_results if l[0] == name
            ]
            
            agents.append({
                "agent_id": name,
                "is_current_agent": is_current,
                "connection_status": status,
                "activity_status": activity_status,
                "last_activity": last_activity.isoformat() if last_activity else None,
                "minutes_since_activity": minutes_since_activity if last_activity else None,
                "recent_progress": agent_progress,
                "active_locks": agent_locks,
                "connection_url": connection_url
            })
        
        # Generate summary
        total_agents = len(agents)
        active_agents = len([a for a in agents if a["activity_status"] == "active"])
        agents_with_locks = len([a for a in agents if a["active_locks"]])
        
        result = {
            "session_id": session_id,
            "current_agent_id": current_agent_id,
            "timestamp": current_time.isoformat(),
            "agents": agents,
            "summary": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "agents_with_locks": agents_with_locks,
                "session_activity": "high" if active_agents >= 2 else "low"
            },
            "coordination_status": {
                "file_conflicts": len(lock_results) > 0,
                "active_tasks": len(progress_results),
                "last_activity": max([a["last_activity"] for a in agents if a["last_activity"]], default=None)
            }
        }
        
        logger.info(f"👥 Agent status checked: {total_agents} agents, {active_agents} active")
        return result
        
    except Exception as e:
        logger.error(f"Error checking agent status: {e}")
        return {
            "error": str(e),
            "message": "Failed to check agent status due to database error",
            "agents": []
        }
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass