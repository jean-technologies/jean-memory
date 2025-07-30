import logging
import json
import asyncio
import datetime
import os
from typing import Dict, Optional, Tuple
import uuid

from fastapi import APIRouter, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse

from app.clients import get_client_profile, get_client_name
from app.context import user_id_var, client_name_var, background_tasks_var
from app.database import get_db

logger = logging.getLogger(__name__)

# Log service info on startup to help with debugging
SERVICE_NAME = os.getenv('RENDER_SERVICE_NAME', 'unknown-service')
RENDER_REGION = os.getenv('RENDER_REGION', 'unknown-region')
logger.warning(f"🔧 MCP Router initialized on service: {SERVICE_NAME} in region: {RENDER_REGION}")

# Log route registration for debugging
logger.warning(f"🛣️ MCP Router registering routes with prefix: {mcp_router.prefix}")
logger.warning(f"🛣️ Available routes will be:")
logger.warning(f"   - POST /mcp/v2/{{client_name}}/{{user_id}}")
logger.warning(f"   - POST /mcp/messages/")
logger.warning(f"   - GET /mcp/{{client_name}}/sse/{{user_id}}")
logger.warning(f"   - POST /mcp/{{client_name}}/messages/{{user_id}}")
logger.warning(f"🛣️ Multi-agent virtual user ID pattern: user__session__session_id__agent_id")

mcp_router = APIRouter(prefix="/mcp")

# Global dictionary to manage SSE connections
sse_message_queues: Dict[str, asyncio.Queue] = {}

# Session-based ID mapping for ChatGPT
chatgpt_session_mappings: Dict[str, Dict[str, str]] = {}

# ===============================================
# MULTI-AGENT SESSION MANAGEMENT
# ===============================================

def parse_virtual_user_id(user_id: str) -> Dict[str, Any]:
    """
    Parse virtual user ID for multi-terminal session detection.
    
    Pattern: {user_id}__session__{session_id}__{agent_id}
    Returns: Dict with session info or single-user info
    """
    if "__session__" in user_id:
        try:
            parts = user_id.split("__session__")
            if len(parts) != 2:
                logger.warning(f"Invalid virtual user ID format: {user_id}")
                return {"is_multi_agent": False, "real_user_id": user_id}
            
            real_user_id = parts[0]
            session_agent = parts[1].split("__")
            
            if len(session_agent) != 2:
                logger.warning(f"Invalid session/agent format in user ID: {user_id}")
                return {"is_multi_agent": False, "real_user_id": user_id}
            
            session_id = session_agent[0]
            agent_id = session_agent[1]
            
            logger.info(f"🔄 Multi-agent session detected - User: {real_user_id}, Session: {session_id}, Agent: {agent_id}")
            
            return {
                "is_multi_agent": True,
                "real_user_id": real_user_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "virtual_user_id": user_id
            }
        except Exception as e:
            logger.error(f"Error parsing virtual user ID {user_id}: {e}")
            return {"is_multi_agent": False, "real_user_id": user_id}
    
    return {"is_multi_agent": False, "real_user_id": user_id}

async def register_agent_connection(session_id: str, agent_id: str, real_user_id: str, connection_url: str) -> bool:
    """
    Register agent connection in database for multi-terminal coordination.
    Auto-creates session if it doesn't exist.
    Gracefully handles database errors to avoid breaking standard functionality.
    """
    try:
        from sqlalchemy import text
        db = next(get_db())
        
        # Check if session exists, create if not
        session_result = db.execute(
            text("SELECT id FROM claude_code_sessions WHERE id = :session_id"),
            {"session_id": session_id}
        ).fetchone()
        
        if not session_result:
            # Create new session
            db.execute(
                text("""
                    INSERT INTO claude_code_sessions (id, name, description, user_id, status, created_at)
                    VALUES (:session_id, :name, :description, :user_id, :status, :created_at)
                """),
                {
                    "session_id": session_id,
                    "name": f"Multi-Agent Session {session_id[:8]}",
                    "description": f"Multi-terminal coordination session for {real_user_id}",
                    "user_id": real_user_id,
                    "status": "active",
                    "created_at": datetime.datetime.now(datetime.timezone.utc)
                }
            )
            logger.info(f"📋 Created new session: {session_id} for user {real_user_id}")
        
        # Register or update agent (use last_activity instead of updated_at)
        unique_agent_id = f"{session_id}__{agent_id}"
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Try to update existing agent first
        update_result = db.execute(
            text("""
                UPDATE claude_code_agents 
                SET status = :status, connection_url = :connection_url, last_activity = :last_activity
                WHERE id = :agent_id
            """),
            {
                "agent_id": unique_agent_id,
                "status": "connected",
                "connection_url": connection_url,
                "last_activity": now
            }
        )
        
        # If no rows were updated, insert new agent
        if update_result.rowcount == 0:
            db.execute(
                text("""
                    INSERT INTO claude_code_agents (id, session_id, name, connection_url, status, last_activity, created_at)
                    VALUES (:agent_id, :session_id, :name, :connection_url, :status, :last_activity, :created_at)
                """),
                {
                    "agent_id": unique_agent_id,
                    "session_id": session_id,
                    "name": agent_id,
                    "connection_url": connection_url,
                    "status": "connected",
                    "last_activity": now,
                    "created_at": now
                }
            )
        
        db.commit()
        logger.info(f"🤖 Registered agent connection: {agent_id} in session {session_id}")
        return True
        
    except Exception as e:
        logger.warning(f"Could not register agent connection (non-critical): {e}")
        # Don't re-raise the exception - this is optional functionality
        return False
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass

async def get_session_agents(session_id: str) -> list:
    """
    Get all agents in a session for coordination.
    Returns empty list if database is unavailable.
    """
    try:
        from sqlalchemy import text
        db = next(get_db())
        
        results = db.execute(
            text("""
                SELECT id, name, connection_url, status, last_activity
                FROM claude_code_agents 
                WHERE session_id = :session_id
                ORDER BY last_activity DESC
            """),
            {"session_id": session_id}
        ).fetchall()
        
        agents = []
        for row in results:
            agents.append({
                "id": row[0],
                "name": row[1], 
                "connection_url": row[2],
                "status": row[3],
                "last_activity": row[4].isoformat() if row[4] else None
            })
        
        return agents
        
    except Exception as e:
        logger.warning(f"Could not get session agents (non-critical): {e}")
        return []
    finally:
        if 'db' in locals():
            try:
                db.close()
            except:
                pass

async def handle_request_logic(request: Request, body: dict, background_tasks: BackgroundTasks):
    """Unified logic to handle an MCP request, abstracted from the transport."""
    from app.auth import get_user_from_api_key_header

    # 1. Determine Authentication and Client Identity
    api_key_auth_success = await get_user_from_api_key_header(request)
    if api_key_auth_success and hasattr(request.state, 'user') and request.state.user:
        is_api_key_path = True
        user_id_from_header = str(request.state.user.user_id)
        client_name_from_header = request.headers.get("x-client-name", "default_agent_app")
    else:
        is_api_key_path = False
        user_id_from_header = request.headers.get("x-user-id")
        client_name_from_header = request.headers.get("x-client-name")

    if not user_id_from_header or not client_name_from_header:
        return JSONResponse(status_code=400, content={"error": "Missing user authentication details"})

    # 1.5. Parse session information from user ID
    session_info = parse_virtual_user_id(user_id_from_header)
    real_user_id = session_info["real_user_id"]

    # 2. Set Context and Get Client Profile
    logger.info(f"🔧 [MCP Context] Setting context variables for user: {real_user_id}, client: {client_name_from_header}")
    if session_info["is_multi_agent"]:
        logger.info(f"🔧 [MCP Context] Multi-agent session: {session_info['session_id']}, agent: {session_info['agent_id']}")
    
    user_token = user_id_var.set(real_user_id)  # Use real user ID for authentication
    client_token = client_name_var.set(client_name_from_header)
    tasks_token = background_tasks_var.set(background_tasks)
    
    # Store session info in request state for client profile access
    request.state.session_info = session_info
    
    logger.info(f"🔧 [MCP Context] Context variables set - background_tasks: {background_tasks is not None}")
    
    request_id = body.get("id") # Get request_id early for error reporting
    
    try:
        client_key = get_client_name(client_name_from_header, is_api_key_path)
        client_profile = get_client_profile(client_key)

        # 3. Process MCP Method
        method_name = body.get("method")
        params = body.get("params", {})

        logger.info(f"Handling MCP method '{method_name}' for client '{client_key}'")

        if method_name == "initialize":
            client_version = params.get("protocolVersion", "2024-11-05")
            use_annotations = client_version == "2025-03-26"
            protocol_version = "2025-03-26" if use_annotations else "2024-11-05"
            
            # Properly advertise tool capabilities
            if use_annotations:
                capabilities = {
                    "tools": {"listChanged": False}, 
                    "logging": {}, 
                    "sampling": {}
                }
            else:
                capabilities = {
                    "tools": {}  # This tells clients that tools are supported
                }
            
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": protocol_version,
                    "capabilities": capabilities,
                    "serverInfo": {"name": "Jean Memory", "version": "1.0.0"}
                },
                "id": request_id
            })

        elif method_name == "tools/list":
            client_version = params.get("protocolVersion", "2024-11-05")
            # Pass session info to client profile for multi-agent awareness
            tools_schema = client_profile.get_tools_schema(
                include_annotations=(client_version == "2025-03-26"),
                session_info=session_info
            )
            logger.info(f"🔍 TOOLS/LIST DEBUG - Client: {client_key}, Session: {session_info.get('session_id', 'single')}, Schema: {json.dumps(tools_schema, indent=2)}")
            return JSONResponse(content={"jsonrpc": "2.0", "result": {"tools": tools_schema}, "id": request_id})

        elif method_name == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            logger.info(f"🔧 [MCP Tool Call] Tool: {tool_name}, User: {real_user_id}, Client: {client_key}")
            if session_info["is_multi_agent"]:
                logger.info(f"🔧 [MCP Tool Call] Multi-agent context - Session: {session_info['session_id']}, Agent: {session_info['agent_id']}")
            logger.info(f"🔧 [MCP Tool Call] Background tasks context: {background_tasks is not None}")
            try:
                # Use the profile to handle the tool call, which encapsulates client-specific logic
                result = await client_profile.handle_tool_call(tool_name, tool_args, real_user_id)
                # Use the profile to format the response
                logger.info(f"🔧 [MCP Tool Call] Tool {tool_name} completed successfully")
                return JSONResponse(content=client_profile.format_tool_response(result, request_id))
            except Exception as e:
                logger.error(f"Error calling tool '{tool_name}' for client '{client_key}': {e}", exc_info=True)
                return JSONResponse(status_code=500, content={"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": request_id})

        # Handle other standard MCP methods
        elif method_name in ["notifications/initialized", "notifications/cancelled"]:
            logger.info(f"Received notification '{method_name}' from client '{client_key}'")
            return JSONResponse(content={"status": "acknowledged"})
        elif method_name in ["resources/list", "prompts/list"]:
            return JSONResponse(content={"jsonrpc": "2.0", "result": {method_name.split('/')[0]: []}, "id": request_id})
        elif method_name == "resources/templates/list":
            return JSONResponse(content={"jsonrpc": "2.0", "result": {"templates": []}, "id": request_id})
        else:
            return JSONResponse(status_code=404, content={"error": f"Method '{method_name}' not found"})

    except Exception as e:
        logger.error(f"Error executing MCP method: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        user_id_var.reset(user_token)
        client_name_var.reset(client_token)
        background_tasks_var.reset(tasks_token)


@mcp_router.post("/messages/")
async def handle_post_message(request: Request, background_tasks: BackgroundTasks):
    """
    Handles a single, stateless JSON-RPC message.
    The logic is now delegated to a shared handler function.
    """
    body = await request.json()
    return await handle_request_logic(request, body, background_tasks)


# ===============================================
# V2 ENDPOINTS - DIRECT HTTP TRANSPORT
# ===============================================

@mcp_router.post("/v2/{client_name}/{user_id}")
async def handle_http_v2_transport(client_name: str, user_id: str, request: Request, background_tasks: BackgroundTasks):
    """
    V2 HTTP Transport Endpoint - Direct backend routing (no Cloudflare proxy)
    
    This endpoint supports HTTP transport with supergateway --stdio flag.
    URL format: {api_base_url}/mcp/v2/{client_name}/{user_id}
    
    Features:
    - Direct connection to backend (no Cloudflare Worker)
    - 50-75% faster performance
    - Better debugging and logging
    - Simplified infrastructure
    - Transport auto-detection
    - Multi-terminal session coordination via virtual user ID
    """
    logger.warning(f"🎯 MCP v2 ROUTE HIT: client={client_name}, user_id={user_id}")
    try:
        # Parse virtual user ID for multi-terminal session detection
        session_info = parse_virtual_user_id(user_id)
        real_user_id = session_info["real_user_id"]
        
        # Set headers for context (use real user ID for authentication)
        request.headers.__dict__['_list'].append((b'x-user-id', real_user_id.encode()))
        request.headers.__dict__['_list'].append((b'x-client-name', client_name.encode()))
        
        body = await request.json()
        method = body.get('method')
        
        # Enhanced logging with session info
        if session_info["is_multi_agent"]:
            logger.warning(f"🔄 Multi-Terminal Transport: {client_name}/{user_id} - Method: {method} - Session: {session_info['session_id']} - Agent: {session_info['agent_id']} - Service: {SERVICE_NAME} ({RENDER_REGION})")
            
            # Register agent connection on initialize method (non-blocking)
            if method == "initialize":
                try:
                    connection_url = f"{request.url.scheme}://{request.url.netloc}{request.url.path}"
                    await register_agent_connection(
                        session_info["session_id"],
                        session_info["agent_id"], 
                        real_user_id,
                        connection_url
                    )
                except Exception as e:
                    logger.warning(f"Agent registration failed (non-critical): {e}")
        else:
            logger.warning(f"🚀 HTTP v2 Transport: {client_name}/{user_id} - Method: {method} - Service: {SERVICE_NAME} ({RENDER_REGION})")
        
        # Use the same unified logic as SSE transport
        response = await handle_request_logic(request, body, background_tasks)
        
        # For HTTP transport, return JSON-RPC response directly (no SSE queue)
        logger.warning(f"✅ HTTP v2 Response: {client_name}/{user_id} - Status: {response.status_code} - Service: {SERVICE_NAME}")
        return response
        
    except Exception as e:
        logger.error(f"❌ HTTP v2 Transport Error: {client_name}/{user_id} - {e}", exc_info=True)
        request_id = None
        try:
            body = await request.json()
            request_id = body.get("id")
        except:
            pass
        
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_id,
            }
        )


# ===============================================
# LEGACY SSE ENDPOINTS - CLOUDFLARE PROXY
# ===============================================

@mcp_router.get("/{client_name}/sse/{user_id}")
async def handle_sse_connection(client_name: str, user_id: str, request: Request):
    """
    SSE endpoint for supergateway compatibility
    This allows npx supergateway to connect to the local development server
    """
    from fastapi.responses import StreamingResponse
    
    logger.info(f"SSE connection from {client_name} for user {user_id}")
    
    # Create a message queue for this connection
    connection_id = f"{client_name}_{user_id}"
    if connection_id not in sse_message_queues:
        sse_message_queues[connection_id] = asyncio.Queue()
    
    async def event_generator():
        try:
            # Send the endpoint event that supergateway expects
            yield f"event: endpoint\ndata: /mcp/{client_name}/messages/{user_id}\n\n"
            
            # CRITICAL FIX: Send an immediate heartbeat to satisfy impatient clients like ChatGPT
            # and prevent the connection from being dropped before the first message.
            yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.datetime.now(datetime.UTC).isoformat()})}\n\n"

            # Main event loop
            while True:
                try:
                    # Check for messages with timeout
                    message = await asyncio.wait_for(
                        sse_message_queues[connection_id].get(), 
                        timeout=1.0
                    )
                    # Send the message through SSE
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat when no messages
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': datetime.datetime.now(datetime.UTC).isoformat()})}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for {client_name}/{user_id}")
            # Clean up the message queue
            if connection_id in sse_message_queues:
                del sse_message_queues[connection_id]
            return
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

@mcp_router.post("/{client_name}/messages/{user_id}")
async def handle_sse_messages(client_name: str, user_id: str, request: Request, background_tasks: BackgroundTasks):
    """
    Messages endpoint for supergateway compatibility
    This handles the actual MCP tool calls from supergateway
    """
    try:
        body = await request.json()
        
        # This function will return a JSONResponse object
        response = await handle_request_logic(request, body, background_tasks)
        response_payload = json.loads(response.body)

        # For Cursor, return JSON-RPC directly instead of SSE
        if client_name == "cursor":
            return response

        connection_id = f"{client_name}_{user_id}"
        if connection_id in sse_message_queues:
            await sse_message_queues[connection_id].put(response_payload)
            # CRITICAL FIX: Immediately send a heartbeat after the message to keep the connection alive.
            # In an async queue, we send the dict and the generator formats it
            await sse_message_queues[connection_id].put({'event': 'heartbeat', 'data': {'timestamp': datetime.datetime.now(datetime.UTC).isoformat()}})
            return Response(status_code=204)
        else:
            # No active SSE connection, so return the full payload directly.
            return response
    
    except Exception as e:
        logger.error(f"Error in SSE messages handler: {e}", exc_info=True)
        request_id = None
        try:
            body = await request.json()
            request_id = body.get("id")
        except:
            pass
        
        response_payload = {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": request_id,
        }
        
        if client_name == "cursor":
            return JSONResponse(content=response_payload, status_code=500)

        connection_id = f"{client_name}_{user_id}"
        if connection_id in sse_message_queues:
            await sse_message_queues[connection_id].put(response_payload)
            return Response(status_code=204)
        else:
            return JSONResponse(content=response_payload, status_code=500)