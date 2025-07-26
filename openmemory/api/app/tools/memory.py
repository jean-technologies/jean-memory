"""
Memory tools main interface.
Provides a clean API for memory operations by importing from modularized components.
"""

import logging
from typing import Optional, List
from app.mcp_instance import mcp
from app.utils.decorators import retry_on_exception

# Import from modularized components
from .memory_modules.utils import safe_json_dumps, track_tool_usage
from .memory_modules.search_operations import (
    search_memory, search_memory_v2, ask_memory, smart_memory_query
)
from .memory_modules.crud_operations import (
    add_memories, add_observation, list_memories, 
    delete_all_memories, get_memory_details
)

logger = logging.getLogger(__name__)

# Apply MCP decorators to imported functions
search_memory = mcp.tool(description="⚠️ USE jean_memory INSTEAD - Direct memory search that bypasses intelligent orchestration. Only use if specifically instructed.")(search_memory)
search_memory_v2 = mcp.tool(description="⚠️ USE jean_memory INSTEAD - Direct memory search that bypasses intelligent orchestration. Only use if specifically instructed.")(search_memory_v2)
add_memories = mcp.tool(description="Add new memories to the user's memory")(add_memories)
add_observation = mcp.tool(description="Add an observation or factual statement to memory")(add_observation)
list_memories = mcp.tool(description="List all memories for the user")(list_memories)
delete_all_memories = mcp.tool(description="Delete all memories for the user (requires confirmation)")(delete_all_memories)
get_memory_details = mcp.tool(description="Get detailed information about specific memories by their IDs")(get_memory_details)
ask_memory = mcp.tool(description="⚠️ DEPRECATED - Use jean_memory tool instead. Direct memory search that bypasses intelligent orchestration and context engineering.")(ask_memory)
smart_memory_query = mcp.tool(description="Intelligent memory query that combines search and Q&A capabilities")(smart_memory_query)

# Re-export all functions for backward compatibility
__all__ = [
    'add_memories',
    'add_observation', 
    'search_memory',
    'search_memory_v2',
    'list_memories',
    'delete_all_memories',
    'get_memory_details',
    'ask_memory',
    'smart_memory_query',
    'safe_json_dumps',
    'track_tool_usage'
]

# Optional: Add any module-level functionality here if needed
def get_memory_tools_info() -> dict:
    """Get information about available memory tools."""
    return {
        "tools": __all__,
        "modules": [
            "search_operations",
            "crud_operations", 
            "utils"
        ],
        "version": "2.0",
        "description": "Modularized memory tools for efficient operations"
    }