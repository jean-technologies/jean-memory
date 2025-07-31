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

from app.clients import get_client_profile
from app.context import user_id_var, client_name_var, background_tasks_var
from app.oauth_simple_new import get_current_user

logger = logging.getLogger(__name__)

oauth_mcp_router = APIRouter(tags=["oauth-mcp"])


async def handle_mcp_request(
    message: dict,
    user: dict,
    background_tasks: BackgroundTasks,
):
    """
    Handles a single JSON-RPC message directly.
    """
    method_name = message.get("method")
    params = message.get("params", {})
    request_id = message.get("id")
    client_name = user["client"]

    logger.info(f"Handling MCP method '{method_name}' for client '{client_name}'")

    client_profile = get_client_profile(client_name)

    if method_name == "initialize":
        # Use client's exact protocol version to avoid version mismatch issues
        client_protocol_version = params.get("protocolVersion", "2024-11-05")
        protocol_version = client_protocol_version
        logger.warning(f"🔥 CLIENT REQUESTED PROTOCOL: {client_protocol_version}")
        
        # For newer protocols, include tools directly in initialize response
        if client_protocol_version in ["2025-06-18", "2025-03-26"]:
            tools_schema = client_profile.get_tools_schema(include_annotations=True)
            capabilities = {
                "tools": {"list": tools_schema, "listChanged": False},
                "logging": {},
                "sampling": {}
            }
            logger.warning(f"🔥 SENDING {len(tools_schema)} TOOLS IN INITIALIZE RESPONSE")
        else:
            # Older protocols use separate tools/list call
            capabilities = {
                "tools": {"listChanged": True},
                "logging": {},
                "sampling": {}
            }
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": capabilities,
                "serverInfo": {"name": "Jean Memory", "version": "1.0.0"}
            },
            "id": request_id
        }

    elif method_name == "tools/list":
        tools_schema = client_profile.get_tools_schema(include_annotations=True)
        return {"jsonrpc": "2.0", "result": {"tools": tools_schema}, "id": request_id}

    elif method_name == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        try:
            result = await client_profile.handle_tool_call(tool_name, tool_args, user["user_id"])
            return client_profile.format_tool_response(result, request_id)
        except Exception as e:
            logger.error(f"Error calling tool '{tool_name}': {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": request_id
            }

    elif method_name in ["notifications/initialized", "notifications/cancelled"]:
        logger.info(f"Received notification '{method_name}'")
        # For notifications, a response isn't strictly required, but we can acknowledge.
        # However, the proxy was returning None, so we do that here as well for single messages.
        # For batch, it was skipped. Let's return a special value to indicate no response.
        return None


    elif method_name in ["resources/list", "prompts/list"]:
        return {"jsonrpc": "2.0", "result": {method_name.split('/')[0]: []}, "id": request_id}

    elif method_name == "resources/templates/list":
        return {"jsonrpc": "2.0", "result": {"templates": []}, "id": request_id}

    else:
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32601, "message": f"Method not found: {method_name}"},
            "id": request_id
        }


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
    
    # Set context variables for the duration of this request
    user_token = user_id_var.set(user["user_id"])
    client_token = client_name_var.set(user["client"])
    tasks_token = background_tasks_var.set(background_tasks)

    try:
        # Parse request body (single message or batch)
        body = await request.json()
        
        # Log all incoming methods to debug what Claude is calling
        if isinstance(body, list):
            methods = [msg.get('method', 'unknown') for msg in body]
            logger.warning(f"🔍 BATCH REQUEST: Methods: {methods}")
            # Check for tools/list in batch
            if any('tools/list' in method for method in methods):
                logger.warning(f"🔥🔥🔥 CLAUDE CALLED TOOLS/LIST IN BATCH! Methods: {methods} 🔥🔥🔥")
        else:
            method = body.get('method', 'unknown')
            logger.warning(f"🔍 SINGLE REQUEST: Method: {method}")
            if method == 'tools/list':
                logger.warning(f"🔥🔥🔥 CLAUDE IS CALLING TOOLS/LIST ON OAUTH PROXY! 🔥🔥🔥")
            elif method == 'initialize':
                logger.warning(f"🔥 INITIALIZE REQUEST: params={body.get('params', {})}")
        
        # Handle batch requests
        if isinstance(body, list):
            logger.info(f"Processing batch request with {len(body)} messages")
            responses = []
            
            for message in body:
                response = await handle_mcp_request(message, user, background_tasks)
                if response:  # Only add non-None responses
                    responses.append(response)
            
            return JSONResponse(content=responses)
        
        # Handle single message
        else:
            response = await handle_mcp_request(body, user, background_tasks)
            if response is None:
                # For notifications, no response is sent back to the client.
                return Response(status_code=204)
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
    finally:
        # Ensure context variables are reset
        user_id_var.reset(user_token)
        client_name_var.reset(client_token)
        background_tasks_var.reset(tasks_token)


@oauth_mcp_router.get("/mcp")
async def mcp_streaming_endpoint(user: dict = Depends(get_current_user)):
    """
    Handle GET requests to /mcp endpoint for Server-Sent Events streaming
    
    Claude Web may require SSE streaming for proper connection persistence.
    This provides a streaming endpoint to maintain connection state.
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json
    import datetime
    
    logger.warning(f"🔥 SSE STREAM REQUESTED by {user['email']} - Claude may need streaming connection")
    
    async def event_generator():
        try:
            # Send initial connection event
            yield f"event: connection\ndata: {json.dumps({'status': 'connected', 'user': user['email']})}\n\n"
            
            # Send capabilities immediately to signal tools are available
            capabilities_event = {
                "event": "capabilities",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {},
                    "prompts": {}
                },
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "Jean Memory", "version": "1.0.0"}
            }
            yield f"event: capabilities\ndata: {json.dumps(capabilities_event)}\n\n"
            
            # Keep connection alive with periodic heartbeats
            while True:
                try:
                    await asyncio.sleep(30)  # 30 second heartbeat
                    heartbeat = {
                        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                        "status": "alive",
                        "user": user["email"]
                    }
                    yield f"event: heartbeat\ndata: {json.dumps(heartbeat)}\n\n"
                except asyncio.CancelledError:
                    logger.info(f"SSE connection closed for {user['email']}")
                    break
                    
        except Exception as e:
            logger.error(f"SSE stream error for {user['email']}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
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