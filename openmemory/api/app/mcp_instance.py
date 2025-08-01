from mcp.server.fastmcp import FastMCP
import logging

# Centralized MCP instance to be imported by tool definitions and the server.
# This avoids circular dependencies.
mcp = FastMCP("Jean Memory")

# Add logging for MCP initialization
logger = logging.getLogger(__name__)
logger.info(f"Initialized MCP server with name: Jean Memory")
logger.info(f"MCP server object: {mcp}")
logger.info(f"MCP internal server: {mcp._mcp_server}")

# Import all tool modules to register MCP decorators
# This must happen after mcp instance creation but before server usage
def register_all_tools():
    """Import all tool modules to register their MCP decorators"""
    try:
        # Import tool modules to register @mcp.tool decorators
        import app.tools.memory
        import app.tools.documents
        import app.tools.orchestration
        import app.tools.debug
        import app.tools.coordination  # Import coordination tools
        logger.info("✅ All MCP tool modules imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import tool modules: {e}")

# Register tools immediately
register_all_tools() 