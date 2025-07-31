import logging
from typing import Dict, Any, List
from .base import BaseClientProfile

logger = logging.getLogger(__name__)


class ClaudeProfile(BaseClientProfile):
    """Client profile for Claude desktop and other standard clients."""

    def _is_multi_agent_session(self) -> bool:
        """Check if current request is from a multi-agent session"""
        try:
            from starlette.concurrency import run_in_threadpool
            from contextvars import copy_context
            import asyncio
            
            # Try to get current request context (this may not always work)
            # For now, return False - we'll enhance this later
            return False
        except:
            return False

    def get_tools_schema(self, include_annotations: bool = False, session_info: dict = None) -> List[Dict[str, Any]]:
        """
        Returns the JSON schema for the original tools, which is the default for Claude.
        Enhanced for multi-agent session awareness.
        """
        logger.info(f"🔧 [CLAUDE PROFILE] get_tools_schema called with session_info: {session_info}")
        
        # Get client name from session info
        client_name = session_info.get("client_name", "") if session_info else ""
        
        # Determine if this is a multi-agent session AND specifically Claude Code
        is_multi_agent = session_info and session_info.get("is_multi_agent", False)
        is_claude_code = client_name.lower() in ["claude code", "claude-code", "claude"]
        
        logger.info(f"🔧 [CLAUDE PROFILE] client_name: '{client_name}', is_claude_code: {is_claude_code}, is_multi_agent: {is_multi_agent}")
        
        # Debug: Check if we can access MCP registered tools
        try:
            from app.mcp_instance import mcp
            mcp_tools = getattr(mcp._mcp_server, 'request_handlers', {}).get('tools/call', {})
            logger.info(f"🔧 [CLAUDE PROFILE] MCP registered tools: {list(mcp_tools.keys()) if isinstance(mcp_tools, dict) else 'Not accessible'}")
        except Exception as e:
            logger.error(f"🔧 [CLAUDE PROFILE] Error accessing MCP tools: {e}")
        
        # Base tool description
        jean_memory_description = "🌟 PRIMARY TOOL for all conversational interactions. Intelligently engineers context for the user's message, saves new information, and provides relevant background. For the very first message in a conversation, set 'is_new_conversation' to true. Set needs_context=false for generic knowledge questions that don't require personal context about the specific user (e.g., 'what is the relationship between introversion and conformity', 'explain quantum physics'). Set needs_context=true only for questions that would benefit from the user's personal context, memories, or previous conversations."
        
        # Add multi-agent session context if applicable (only for Claude Code)
        if is_multi_agent and is_claude_code:
            jean_memory_description += f"\n\n🔄 MULTI-AGENT SESSION ACTIVE:\n• Session: {session_info.get('session_id', 'unknown')}\n• Agent: {session_info.get('agent_id', 'unknown')}\n• Cross-terminal coordination enabled for collision-free development"
        
        tools = [
            {
                "name": "jean_memory",
                "description": jean_memory_description,
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_message": {"type": "string", "description": "The user's complete message or question"},
                        "is_new_conversation": {"type": "boolean", "description": "Set to true only for the very first message in a new chat session, otherwise false."},
                        "needs_context": {"type": "boolean", "description": "Whether personal context retrieval is needed for this query. Set to false for generic knowledge questions (science, definitions, general concepts). Set to true for questions that would benefit from the user's personal context, memories, or previous conversations.", "default": True}
                    },
                    "required": ["user_message", "is_new_conversation"]
                }
            },
            {
                "name": "store_document",
                "description": "⚡ FAST document upload. Store large documents (markdown, code, essays) in background. Returns immediately with job ID for status tracking. Perfect for entire files that would slow down chat.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "A descriptive title for the document"},
                        "content": {"type": "string", "description": "The full text content of the document (markdown, code, etc.)"},
                        "document_type": {"type": "string", "description": "Type of document (e.g., 'markdown', 'code', 'notes', 'documentation')", "default": "markdown"},
                        "source_url": {"type": "string", "description": "Optional URL where the document came from"}
                    },
                    "required": ["title", "content"]
                }
            }
        ]

        # Add coordination tools for multi-agent sessions (Claude Code only)
        if is_multi_agent and not is_claude_code:
            logger.warning(f"🚨 SECURITY: Multi-agent coordination tools blocked for non-Claude Code client: '{client_name}'. Only Claude Code is authorized for coordination tools.")
        elif is_multi_agent and is_claude_code:
            agent_id = session_info.get('agent_id', 'unknown')
            
            # Planning tools (available to planner agent only)
            logger.info(f"🔧 CLAUDE PROFILE DEBUG - Agent ID: '{agent_id}', Session Info: {session_info}")
            logger.info(f"🔧 CLAUDE PROFILE DEBUG - Agent ID type: {type(agent_id)}, value repr: {repr(agent_id)}")
            logger.info(f"🔧 CLAUDE PROFILE DEBUG - Checking if agent_id == 'planner': {agent_id == 'planner'}")
            if agent_id == 'planner':
                logger.info("🎯 Adding planner-specific coordination tools")
                tools.extend([
                    {
                        "name": "analyze_task_conflicts",
                        "description": "🎯 PLANNER ONLY: Analyze task conflicts and file dependencies for optimal 2-5 agent distribution. Determines file collision risks and creates scalable agent assignment strategy.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "tasks": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of development tasks to analyze for conflicts"
                                },
                                "project_files": {
                                    "type": "array", 
                                    "items": {"type": "string"},
                                    "description": "List of file paths that will be modified"
                                },
                                "complexity_level": {
                                    "type": "string",
                                    "enum": ["simple", "moderate", "complex"],
                                    "description": "Project complexity to determine optimal agent count",
                                    "default": "moderate"
                                }
                            },
                            "required": ["tasks"]
                        }
                    },
                    {
                        "name": "create_task_distribution",
                        "description": "🎯 PLANNER ONLY: Generate terminal-specific prompts and coordination setup for 2-5 implementer agents based on conflict analysis.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "analysis_result": {
                                    "type": "object",
                                    "description": "Result from analyze_task_conflicts tool"
                                },
                                "preferred_agent_count": {
                                    "type": "integer",
                                    "minimum": 2,
                                    "maximum": 5,
                                    "description": "Preferred number of implementation agents (2-5)"
                                }
                            },
                            "required": ["analysis_result"]
                        }
                    }
                ])
            
            # Execution coordination tools (available to all agents including planner)
            logger.info("🛠️ Adding execution coordination tools (available to all agents)")
            tools.extend([
                {
                    "name": "claim_file_lock",
                    "description": "🔒 COORDINATION: Create cross-session file locks via database for scalable multi-agent coordination. Prevents file conflicts across 2-5 terminals.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file paths to lock for exclusive access"
                            },
                            "operation": {
                                "type": "string",
                                "enum": ["read", "write", "delete"],
                                "description": "Type of operation requiring the lock",
                                "default": "write"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 60,
                                "description": "Lock duration in minutes (auto-expires)",
                                "default": 15
                            }
                        },
                        "required": ["file_paths"]
                    }
                },
                {
                    "name": "sync_progress",
                    "description": "📡 COORDINATION: Broadcast progress updates across all terminals in session. Enables real-time status sync for 2-5 agent coordination.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Unique identifier for the task being updated"
                            },
                            "status": {
                                "type": "string",
                                "enum": ["started", "in_progress", "completed", "failed", "blocked"],
                                "description": "Current status of the task"
                            },
                            "progress_percentage": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 100,
                                "description": "Progress percentage (0-100)"
                            },
                            "message": {
                                "type": "string",
                                "description": "Optional status message or details"
                            },
                            "affected_files": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Files modified in this update"
                            }
                        },
                        "required": ["task_id", "status"]
                    }
                },
                {
                    "name": "check_agent_status",
                    "description": "👥 COORDINATION: Check status of all other agents in the same session. Provides real-time visibility across 2-5 terminals.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "include_inactive": {
                                "type": "boolean",
                                "description": "Include agents that haven't been active recently",
                                "default": False
                            }
                        }
                    }
                }
            ])

        # Add annotations only for newer protocol versions
        if include_annotations:
            annotations_map = {
                "jean_memory": {"readOnly": False, "sensitive": True, "destructive": False, "intelligent": True},
                "store_document": {"readOnly": False, "sensitive": True, "destructive": False},
                "analyze_task_conflicts": {"readOnly": True, "sensitive": False, "destructive": False, "intelligent": True},
                "create_task_distribution": {"readOnly": False, "sensitive": False, "destructive": False, "intelligent": True},
                "claim_file_lock": {"readOnly": False, "sensitive": False, "destructive": False},
                "sync_progress": {"readOnly": False, "sensitive": False, "destructive": False},
                "check_agent_status": {"readOnly": True, "sensitive": False, "destructive": False},
            }
            for tool in tools:
                if tool["name"] in annotations_map:
                    tool["annotations"] = annotations_map[tool["name"]]
        
        logger.info(f"🔧 [CLAUDE PROFILE] Returning {len(tools)} tools: {[tool['name'] for tool in tools]}")
        return tools

    async def handle_tool_call(
        self, tool_name: str, tool_args: dict, user_id: str
    ) -> Any:
        """
        For Claude/default clients, we need to filter out parameters that
        are not intended for them to preserve backward compatibility.
        """
        # Filter out complex parameters for Claude Desktop to keep interface simple
        if tool_name == "search_memory":
            tool_args.pop("tags_filter", None)
        elif tool_name == "add_memories":
            tool_args.pop("tags", None)

        # Call the base handler with the sanitized arguments
        return await super().handle_tool_call(tool_name, tool_args, user_id) 