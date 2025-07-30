from typing import Dict, Any, List
from .base import BaseClientProfile


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
        # Determine if this is a multi-agent session
        is_multi_agent = session_info and session_info.get("is_multi_agent", False)
        
        # Base tool description
        jean_memory_description = "🌟 PRIMARY TOOL for all conversational interactions. Intelligently engineers context for the user's message, saves new information, and provides relevant background. For the very first message in a conversation, set 'is_new_conversation' to true. Set needs_context=false for generic knowledge questions that don't require personal context about the specific user (e.g., 'what is the relationship between introversion and conformity', 'explain quantum physics'). Set needs_context=true only for questions that would benefit from the user's personal context, memories, or previous conversations."
        
        # Add multi-agent session context if applicable
        if is_multi_agent:
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

        # Add annotations only for newer protocol versions
        if include_annotations:
            annotations_map = {
                "jean_memory": {"readOnly": False, "sensitive": True, "destructive": False, "intelligent": True},
                "store_document": {"readOnly": False, "sensitive": True, "destructive": False},
            }
            for tool in tools:
                if tool["name"] in annotations_map:
                    tool["annotations"] = annotations_map[tool["name"]]
        
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