"""
Centralized configuration for MCP (Model Context Protocol) tools.

This file provides a single source of truth for all available tools and
a simple configuration for controlling which tools are exposed to different clients.
"""

from app.tools.orchestration import jean_memory
from app.tools.documents import store_document, deep_memory_query
from app.tools.memory import add_memories, search_memory, ask_memory, list_memories

# A single dictionary defining all available tools in the system.
# The key is the tool name, and the value is the function object.
ALL_TOOLS = {
    "jean_memory": jean_memory,
    "store_document": store_document,
    "add_memories": add_memories,
    "search_memory": search_memory,
    "ask_memory": ask_memory,
    "list_memories": list_memories,
    "deep_memory_query": deep_memory_query,
}

# A simple configuration to control which clients see which tools.
# The key is the client name (e.g., 'claude', 'chatgpt'), and the value is a list
# of tool names they are allowed to access.
CLIENT_TOOL_CONFIG = {
    "claude": [
        "jean_memory",
        "store_document",
    ],
    "chatgpt": [
        "jean_memory",
        "store_document",
        "add_memories",
        "search_memory",
        "ask_memory",
        "list_memories",
    ],
    # Default client gets the most restricted, safest set of tools.
    "default": [
        "jean_memory",
    ],
    # Chorus client gets a specific set.
    "chorus": [
        "jean_memory",
        "add_memories",
    ]
}

def get_tools_for_client(client_name: str) -> list:
    """
    Returns the tool function objects for a given client name based on the configuration.
    If the client is not found, it falls back to the 'default' configuration.
    """
    tool_names = CLIENT_TOOL_CONFIG.get(client_name, CLIENT_TOOL_CONFIG.get("default", []))
    
    # The mcp.tool decorator attaches the tool definition to the function.
    # We collect these definitions to be sent to the client.
    tool_defs = []
    for name in tool_names:
        func = ALL_TOOLS.get(name)
        if func and hasattr(func, "mcp_tool_def"):
            tool_defs.append(func.mcp_tool_def)
            
    return tool_defs 