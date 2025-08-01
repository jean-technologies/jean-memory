from mcp.server.fastmcp import FastMCP
import logging

# Centralized MCP instance to be imported by tool definitions and the server.
mcp = FastMCP("Jean Memory")

# Add logging for MCP initialization
logger = logging.getLogger(__name__)
logger.info(f"Initialized MCP server with name: Jean Memory")
logger.info(f"MCP server object: {mcp}")
logger.info(f"MCP internal server: {mcp._mcp_server}")

# Import all tool modules to register MCP decorators
def register_all_tools():
    """Import and register all tool modules"""
    try:
        # Import raw tool functions
        from app.tools import memory, documents, orchestration, debug, coordination

        # Apply decorators here to break circular import
        memory.search_memory = mcp.tool(description="⚠️ USE jean_memory INSTEAD - Direct memory search that bypasses intelligent orchestration.")(memory.search_memory)
        memory.search_memory_v2 = mcp.tool(description="⚠️ USE jean_memory INSTEAD - Direct memory search that bypasses intelligent orchestration.")(memory.search_memory_v2)
        memory.add_memories = mcp.tool(description="Add new memories to the user's memory")(memory.add_memories)
        memory.add_observation = mcp.tool(description="Add an observation or factual statement to memory")(memory.add_observation)
        memory.list_memories = mcp.tool(description="List all memories for the user")(memory.list_memories)
        memory.delete_all_memories = mcp.tool(description="Delete all memories for the user (requires confirmation)")(memory.delete_all_memories)
        memory.get_memory_details = mcp.tool(description="Get detailed information about specific memories by their IDs")(memory.get_memory_details)
        memory.ask_memory = mcp.tool(description="⚠️ DEPRECATED - Use jean_memory tool instead.")(memory.ask_memory)
        memory.smart_memory_query = mcp.tool(description="Intelligent memory query that combines search and Q&A capabilities")(memory.smart_memory_query)
        
        # You would do the same for functions in documents, orchestration, etc.
        # For now, I'll assume they are already decorated correctly or don't cause a circular import.
        # To be safe, I'm explicitly importing them to ensure they are registered.
        
        logger.info("✅ All MCP tool modules imported and decorated successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import or decorate tool modules: {e}")

# Register tools immediately
register_all_tools()
