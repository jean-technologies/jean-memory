"""
MCP OAuth Proxy for Claude Web

This endpoint implements a lean, stateless proxy that:
1. Authenticates Claude using OAuth Bearer tokens (JWT)
2. Extracts user_id and client from the JWT
3. Proxies requests to the proven V2 HTTP transport logic
4. Returns responses directly without sessions or SSE overhead

This combines OAuth security with V2's superior performance and reliability.
"""

import logging
import json

from fastapi import APIRouter, Request, Response, Depends, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders

from app.oauth_simple_new import get_current_user
from app.routing.mcp import handle_request_logic

logger = logging.getLogger(__name__)

oauth_mcp_router = APIRouter(tags=["oauth-mcp"])


def validate_origin(request: Request) -> bool:
    """Validate Origin header to prevent DNS rebinding attacks"""
    origin = request.headers.get("origin")
    if not origin:
        return True  # Allow requests without Origin header
    
    # Allow our known domains
    allowed_origins = [
        "https://claude.ai",
        "https://app.claude.ai", 
        "https://api.claude.ai",
        "https://jean-memory-api-virginia.onrender.com",
        "http://localhost",
        "https://localhost"
    ]
    
    return any(origin.startswith(allowed) for allowed in allowed_origins)


@oauth_mcp_router.post("/mcp")
async def mcp_oauth_proxy(
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    MCP OAuth Proxy - Stateless HTTP Transport
    
    URL: https://jean-memory-api-virginia.onrender.com/mcp
    Authentication: OAuth Bearer token (JWT) with auto-discovery
    Transport: Direct HTTP (no sessions, no SSE)
    
    This is the main endpoint users copy/paste into Claude Web connectors.
    After OAuth authentication, requests are proxied to the robust V2 logic.
    """
    
    # Validate Origin header (security requirement)
    if not validate_origin(request):
        logger.warning(f"Invalid origin: {request.headers.get('origin')}")
        raise HTTPException(status_code=403, detail="Invalid origin")
    
    logger.info(f"🚀 MCP OAuth Proxy: {user['client']} for user {user['user_id']} ({user['email']})")
    
    try:
        # Parse request body (single message or batch)
        body = await request.json()
        
        # Handle batch requests
        if isinstance(body, list):
            logger.info(f"Processing batch request with {len(body)} messages")
            responses = []
            
            for message in body:
                response = await proxy_to_v2_logic(request, message, background_tasks, user)
                if response:  # Only add non-None responses
                    responses.append(response)
            
            return JSONResponse(content=responses)
        
        # Handle single message
        else:
            response = await proxy_to_v2_logic(request, body, background_tasks, user)
            return JSONResponse(content=response)
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {e}")
        return JSONResponse(
            status_code=400,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None
            }
        )
    except Exception as e:
        logger.error(f"Error in MCP OAuth proxy: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0", 
                "error": {"code": -32603, "message": "Internal error"},
                "id": None
            }
        )


async def proxy_to_v2_logic(
    request: Request,
    message: dict, 
    background_tasks: BackgroundTasks,
    user: dict
) -> dict:
    """
    Proxy a single JSON-RPC message to the V2 HTTP transport logic
    
    This function:
    1. Adds user context to request headers (same as V2 endpoint)
    2. Calls the proven handle_request_logic function
    3. Returns the response directly (no session management)
    """
    
    # Add user context to headers (same format as V2 endpoint)
    headers = MutableHeaders(request.headers)
    headers["x-user-id"] = user["user_id"]
    headers["x-user-email"] = user["email"]
    headers["x-client-name"] = user["client"]
    
    # Modify request with user context
    request._headers = headers
    
    logger.info(f"🔄 Proxying {message.get('method', 'unknown')} to V2 logic for user {user['user_id']}")
    
    # Route to the proven V2 logic (same as handle_http_v2_transport uses)
    response = await handle_request_logic(request, message, background_tasks)
    
    # Extract JSON content from response
    if hasattr(response, 'body'):
        try:
            response_content = json.loads(response.body)
            logger.info(f"✅ V2 logic completed for {message.get('method', 'unknown')}")
            return response_content
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse V2 response: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Response parsing error"},
                "id": message.get("id")
            }
    elif isinstance(response, dict):
        return response
    else:
        logger.error(f"Unexpected response type from V2 logic: {type(response)}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": "Unexpected response format"},
            "id": message.get("id")
        }


@oauth_mcp_router.get("/mcp")
async def mcp_get_not_supported(user: dict = Depends(get_current_user)):
    """
    Handle GET requests to /mcp endpoint
    
    This transport uses direct HTTP POST only (no SSE streams).
    Return a clear message to indicate this is not a streaming transport.
    """
    return JSONResponse(
        status_code=200,
        content={
            "transport": "oauth-proxy",
            "protocol": "MCP",
            "message": "This endpoint uses direct HTTP transport only. Send POST requests for MCP operations.",
            "streaming": False,
            "user": user["email"]
        }
    )


@oauth_mcp_router.get("/mcp/health")  
async def mcp_health(user: dict = Depends(get_current_user)):
    """Health check for MCP server with auth"""
    
    return {
        "status": "healthy",
        "user": user["email"],
        "client": user["client"],
        "transport": "oauth-proxy",
        "protocol": "MCP"
    }


@oauth_mcp_router.get("/mcp/status")
async def mcp_status():
    """Public MCP server status - no auth required for testing"""
    
    return {
        "status": "online",
        "transport": "oauth-proxy",
        "protocol_version": "2024-11-05",
        "protocol": "MCP",
        "oauth": "enabled",
        "serverInfo": {
            "name": "jean-memory",
            "version": "1.0.0"
        }
    }


@oauth_mcp_router.options("/mcp")
async def mcp_options():
    """Handle CORS preflight requests"""
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Origin",
            "Access-Control-Max-Age": "3600"
        }
    )


@oauth_mcp_router.head("/mcp")
async def mcp_head():
    """Handle HEAD requests for MCP endpoint discovery"""
    return Response(
        status_code=200,
        headers={
            "Content-Type": "application/json",
            "X-MCP-Protocol": "2024-11-05",
            "X-MCP-Transport": "http",
            "X-OAuth-Supported": "true",
            "Access-Control-Allow-Origin": "*"
        }
    )