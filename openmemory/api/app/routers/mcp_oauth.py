"""Unified MCP endpoint with OAuth authentication"""

from fastapi import APIRouter, Request, Depends, BackgroundTasks
from app.oauth import oauth_required, get_current_user, OAuthUser
from app.routing.mcp import handle_request_logic
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp-oauth"])


@router.post("/mcp")
async def unified_mcp_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    user: OAuthUser = Depends(get_current_user)
):
    """
    Universal MCP endpoint for all AI clients
    
    No user ID in URL! The JWT token tells us:
    - Who the user is (user.user_id)
    - What client is calling (user.client)
    - What permissions they have (user.scope)
    """
    
    logger.info(f"MCP request from {user.client} for user {user.user_id}")
    
    # Get request body
    try:
        body = await request.json()
    except:
        body = {}
    
    # Add user context to request headers for downstream processing
    # This maintains compatibility with existing MCP logic
    from starlette.datastructures import MutableHeaders
    
    headers = MutableHeaders(request.headers)
    headers["x-user-id"] = user.user_id
    headers["x-user-email"] = user.email
    headers["x-client-name"] = user.client
    
    # Create new request with auth headers
    request._headers = headers
    
    # Route to existing MCP handler
    response = await handle_request_logic(request, body, background_tasks)
    
    # Log the interaction
    logger.info(
        f"MCP {body.get('method', 'unknown')} from {user.client} "
        f"for user {user.email} completed"
    )
    
    return response


@router.get("/mcp/health")
async def mcp_health(user: OAuthUser = Depends(get_current_user)):
    """Health check endpoint that requires OAuth"""
    
    return {
        "status": "healthy",
        "user": user.email,
        "client": user.client,
        "scope": user.scope
    } 