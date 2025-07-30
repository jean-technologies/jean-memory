"""MCP server endpoint for Claude with OAuth Bearer token authentication"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTasks

from app.oauth import get_current_user, OAuthUser
from app.routing.mcp import handle_request_logic

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp-claude"])


@router.post("/mcp")
async def mcp_server_post(
    request: Request,
    background_tasks: BackgroundTasks,
    user: OAuthUser = Depends(get_current_user)
):
    """
    MCP server endpoint for Claude - POST with Bearer token
    
    This is the main endpoint that Claude connects to:
    - URL: https://jean-memory-api-dev.onrender.com/mcp
    - Authentication: Bearer token (JWT)
    - Protocol: JSON-RPC 2.0 (MCP)
    """
    
    logger.info(f"MCP POST request from {user.client} for user {user.user_id}")
    
    # Get request body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON body: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32700, "message": "Parse error"},
            "id": None
        }
    
    # Add user context to request headers for downstream processing
    from starlette.datastructures import MutableHeaders
    
    headers = MutableHeaders(request.headers)
    headers["x-user-id"] = user.user_id
    headers["x-user-email"] = user.email
    headers["x-client-name"] = user.client
    
    # Create new request with auth headers
    request._headers = headers
    
    # Route to existing MCP handler (reuses all existing logic)
    response = await handle_request_logic(request, body, background_tasks)
    
    # Log the interaction
    method = body.get("method", "unknown")
    logger.info(f"MCP {method} from {user.client} for user {user.email} completed")
    
    return response


@router.get("/mcp")
async def mcp_server_sse(
    request: Request,
    user: OAuthUser = Depends(get_current_user)
):
    """
    MCP server endpoint for Claude - SSE (Server-Sent Events)
    
    This endpoint supports SSE transport for real-time communication
    - URL: https://jean-memory-api-dev.onrender.com/mcp
    - Authentication: Bearer token (JWT)
    - Transport: Server-Sent Events
    """
    
    logger.info(f"MCP SSE connection from {user.client} for user {user.user_id}")
    
    async def sse_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for MCP communication"""
        
        # Send initial connection event
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'user': user.email})}\n\n"
        
        try:
            # Keep connection alive and handle incoming messages
            # For now, we'll implement a simple ping/pong mechanism
            ping_count = 0
            while True:
                await asyncio.sleep(30)  # Send keepalive every 30 seconds
                ping_count += 1
                
                keepalive_data = {
                    "type": "keepalive",
                    "ping": ping_count,
                    "user": user.email,
                    "client": user.client
                }
                
                yield f"data: {json.dumps(keepalive_data)}\n\n"
                
                # Break after reasonable time to prevent infinite connections
                if ping_count > 120:  # 1 hour max
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for {user.email}")
            yield f"data: {json.dumps({'type': 'disconnection', 'status': 'cancelled'})}\n\n"
        except Exception as e:
            logger.error(f"SSE error for {user.email}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
        }
    )


@router.get("/mcp/health")
async def mcp_health_check(user: OAuthUser = Depends(get_current_user)):
    """Health check for authenticated MCP server"""
    
    return {
        "status": "healthy",
        "protocol": "MCP",
        "version": "2024-11-05",
        "authentication": "OAuth Bearer",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "client": user.client,
            "scopes": user.scope
        },
        "capabilities": {
            "tools": True,
            "resources": False,
            "prompts": False,
            "sampling": False
        }
    }


@router.options("/mcp")
async def mcp_options():
    """Handle CORS preflight for MCP endpoint"""
    
    return {
        "Allow": "GET, POST, OPTIONS",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With",
    }