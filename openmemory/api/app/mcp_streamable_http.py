"""
MCP Streamable HTTP Transport Implementation (2025-03-26 specification)

This implements the correct transport protocol required by Claude Web for
persistent MCP connections with OAuth authentication.
"""

import logging
import json
import secrets
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response, Depends, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.datastructures import MutableHeaders

from app.oauth_simple_new import get_current_user
from app.routing.mcp import handle_request_logic

logger = logging.getLogger(__name__)

# Session storage for Streamable HTTP (use Redis in production)
active_sessions: Dict[str, Dict] = {}

# MCP Streamable HTTP router
mcp_streamable_router = APIRouter(tags=["mcp-streamable"])


def generate_session_id() -> str:
    """Generate a cryptographically secure session ID"""
    return f"mcp-session-{secrets.token_urlsafe(32)}"


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


@mcp_streamable_router.post("/mcp-stream")
async def mcp_streamable_post(
    request: Request,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    MCP Streamable HTTP Transport - POST endpoint
    
    Handles JSON-RPC messages with proper session management
    according to MCP 2025-03-26 specification
    """
    
    # Validate Origin header (required by spec)
    if not validate_origin(request):
        logger.warning(f"Invalid origin: {request.headers.get('origin')}")
        raise HTTPException(status_code=403, detail="Invalid origin")
    
    # Check for session ID in headers
    session_id = request.headers.get("mcp-session-id")
    
    try:
        # Parse request body (single message or batch)
        body = await request.json()
        
        # Handle batch requests
        if isinstance(body, list):
            logger.info(f"Processing batch request with {len(body)} messages")
            responses = []
            
            for message in body:
                response = await process_single_message(
                    request, message, background_tasks, user, session_id
                )
                if response:  # Only add non-None responses
                    responses.append(response)
            
            return JSONResponse(content=responses)
        
        # Handle single message
        else:
            response = await process_single_message(
                request, body, background_tasks, user, session_id
            )
            
            # For initialize method, create session and add session header
            if body.get("method") == "initialize" and response:
                new_session_id = generate_session_id()
                
                # Store session info
                active_sessions[new_session_id] = {
                    "user_id": user["user_id"],
                    "client": user["client"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_activity": datetime.now(timezone.utc).isoformat()
                }
                
                logger.info(f"Created MCP session: {new_session_id} for user {user['email']}")
                
                # Create JSON response with session header
                json_response = JSONResponse(content=response)
                json_response.headers["mcp-session-id"] = new_session_id
                return json_response
            
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
        logger.error(f"Error processing MCP streamable request: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0", 
                "error": {"code": -32603, "message": "Internal error"},
                "id": None
            }
        )


@mcp_streamable_router.get("/mcp-stream")
async def mcp_streamable_get(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    MCP Streamable HTTP Transport - GET endpoint
    
    Opens Server-Sent Events stream for server-to-client messages
    according to MCP 2025-03-26 specification
    """
    
    # Validate Origin header
    if not validate_origin(request):
        logger.warning(f"Invalid origin: {request.headers.get('origin')}")
        raise HTTPException(status_code=403, detail="Invalid origin")
    
    # Check for required session ID
    session_id = request.headers.get("mcp-session-id")
    if not session_id or session_id not in active_sessions:
        logger.warning(f"Invalid or missing session ID: {session_id}")
        raise HTTPException(status_code=400, detail="Valid session ID required")
    
    # Update session activity
    active_sessions[session_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"Opening SSE stream for session: {session_id}")
    
    async def event_generator():
        """Generate Server-Sent Events stream"""
        try:
            # Send initial connection event
            yield f"id: {secrets.token_urlsafe(8)}\n"
            yield f"event: connected\n"
            yield f"data: {json.dumps({'type': 'connected', 'session': session_id})}\n\n"
            
            # Keep connection alive with periodic heartbeats
            import asyncio
            while True:
                try:
                    # Check if session is still valid
                    if session_id not in active_sessions:
                        logger.info(f"Session {session_id} no longer active, closing stream")
                        break
                    
                    # Send heartbeat
                    yield f"id: {secrets.token_urlsafe(8)}\n"
                    yield f"event: heartbeat\n"
                    yield f"data: {json.dumps({'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                    
                    # Wait before next heartbeat
                    await asyncio.sleep(30)  # 30 second heartbeat
                    
                except asyncio.CancelledError:
                    logger.info(f"SSE stream cancelled for session: {session_id}")
                    break
                except Exception as e:
                    logger.error(f"Error in SSE stream: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in event generator: {e}")
        finally:
            logger.info(f"SSE stream closed for session: {session_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control, mcp-session-id",
            "mcp-session-id": session_id
        }
    )


@mcp_streamable_router.delete("/mcp-stream")
async def mcp_streamable_delete(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    MCP Streamable HTTP Transport - DELETE endpoint
    
    Terminates session according to MCP 2025-03-26 specification
    """
    
    session_id = request.headers.get("mcp-session-id")
    if session_id and session_id in active_sessions:
        del active_sessions[session_id]
        logger.info(f"Terminated MCP session: {session_id}")
        return JSONResponse(content={"status": "session_terminated"})
    
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid or missing session ID"}
    )


async def process_single_message(
    request: Request,
    message: dict, 
    background_tasks: BackgroundTasks,
    user: dict,
    session_id: Optional[str] = None
) -> Optional[dict]:
    """Process a single JSON-RPC message with proper MCP handling"""
    
    # Validate session for non-initialize requests
    if message.get("method") != "initialize":
        if not session_id or session_id not in active_sessions:
            logger.warning(f"Invalid session for method {message.get('method')}: {session_id}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32602, "message": "Valid session required"},
                "id": message.get("id")
            }
        
        # Update session activity
        active_sessions[session_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
    
    # Add user context to headers (same as existing MCP logic)
    headers = MutableHeaders(request.headers)
    headers["x-user-id"] = user["user_id"]
    headers["x-user-email"] = user["email"]
    headers["x-client-name"] = user["client"]
    
    # Modify request with user context
    request._headers = headers
    
    # Route to existing MCP logic
    response = await handle_request_logic(request, message, background_tasks)
    
    # Extract JSON content from response
    if hasattr(response, 'body'):
        try:
            return json.loads(response.body)
        except (json.JSONDecodeError, AttributeError):
            return None
    elif isinstance(response, dict):
        return response
    else:
        return None


@mcp_streamable_router.options("/mcp-stream")
async def mcp_streamable_options():
    """Handle CORS preflight requests"""
    return JSONResponse(
        content={"status": "ok"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, mcp-session-id, Origin",
            "Access-Control-Max-Age": "3600"
        }
    )


# Status endpoint for debugging
@mcp_streamable_router.get("/mcp-stream/status")
async def mcp_streamable_status():
    """Get current status of MCP Streamable HTTP transport"""
    return {
        "status": "online",
        "transport": "streamable-http",
        "protocol_version": "2025-03-26",
        "active_sessions": len(active_sessions),
        "oauth": "enabled",
        "serverInfo": {
            "name": "jean-memory",
            "version": "1.0.0"
        }
    }