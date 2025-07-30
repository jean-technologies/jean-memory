"""
Simple MCP server endpoint for Claude Web

This endpoint:
1. Accepts OAuth Bearer tokens
2. Extracts user context from JWT
3. Routes to existing MCP logic
4. Returns proper JSON-RPC responses
"""

import logging
from fastapi import APIRouter, Request, Depends, BackgroundTasks
from app.oauth_simple_new import get_current_user
from app.routing.mcp import handle_request_logic
from starlette.datastructures import MutableHeaders

logger = logging.getLogger(__name__)

mcp_router = APIRouter(tags=["mcp"])


@mcp_router.post("/mcp")
async def mcp_server(
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    MCP server endpoint for Claude Web
    
    URL: https://jean-memory-api-dev.onrender.com/mcp
    Authentication: Bearer token (JWT)
    Protocol: JSON-RPC 2.0 (MCP)
    """
    
    logger.info(f"MCP request from {user['client']} for user {user['user_id']}")
    
    # Get request body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        }
    
    # Add user context to headers (same as existing v2 endpoints)
    headers = MutableHeaders(request.headers)
    headers["x-user-id"] = user["user_id"]
    headers["x-user-email"] = user["email"]  
    headers["x-client-name"] = user["client"]
    
    # Modify request with user context
    request._headers = headers
    
    # Route to existing MCP logic (identical to v2 endpoints)
    response = await handle_request_logic(request, body, background_tasks)
    
    # Log completion
    method = body.get("method", "unknown")
    logger.info(f"MCP {method} completed for {user['email']}")
    
    return response


@mcp_router.get("/mcp/health")  
async def mcp_health(user: dict = Depends(get_current_user)):
    """Health check for MCP server with auth"""
    
    return {
        "status": "healthy",
        "user": user["email"],
        "client": user["client"],
        "protocol": "MCP"
    }