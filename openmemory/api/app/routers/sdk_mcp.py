"""
Jean Memory SDK MCP Integration Router
Provides MCP-native endpoints for the Jean Memory SDK
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.auth import get_current_user
from app.models import User
from app.mcp_claude_simple import handle_mcp_request
from app.context import user_id_var, client_name_var, background_tasks_var

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jean-chat", tags=["SDK MCP"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None

class LegacyChatRequest(BaseModel):
    message: str
    user_token: Optional[str] = None
    conversation_id: Optional[str] = None
    system_prompt: Optional[str] = None

@router.post("")
async def jean_chat_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """
    Jean Memory SDK chat endpoint supporting both new ChatRequest and legacy formats
    Supports OAuth JWT user tokens and API key authentication
    """
    try:
        # Parse request body to determine format
        body = await request.json()
        logger.info(f"🤖 SDK MCP: Chat request from user {user.user_id}, format: {type(body)}")
        
        # Determine current user (support user_token override for OAuth)
        current_user = user
        if "user_token" in body and body["user_token"]:
            # Parse OAuth JWT to get user ID
            import jwt
            try:
                payload = jwt.decode(body["user_token"], options={"verify_signature": False})
                oauth_user_id = payload.get("sub")
                if oauth_user_id:
                    # Get or create user from OAuth token
                    from app.auth import get_or_create_user_from_provider
                    from app.database import get_db
                    db = next(get_db())
                    oauth_user = await get_or_create_user_from_provider(
                        provider_id=oauth_user_id,
                        email=payload.get("email", "oauth@example.com"),
                        name=payload.get("name", "OAuth User"),
                        provider="oauth_jwt"
                    )
                    if oauth_user:
                        current_user = oauth_user
                        logger.info(f"🔄 Using OAuth user: {oauth_user_id}")
            except Exception as e:
                logger.warning(f"Failed to parse user_token, using API key user: {e}")
        
        # Set context variables for MCP tools
        user_id_var.set(current_user.user_id)
        client_name_var.set("Jean Memory SDK")
        background_tasks_var.set(background_tasks)
        
        # Handle different request formats
        if "messages" in body:
            # New ChatRequest format
            messages = body["messages"]
            system_prompt = body.get("system_prompt", "You are a helpful assistant.")
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if not user_messages:
                raise HTTPException(status_code=400, detail="No user message found")
            latest_message = user_messages[-1]["content"]
            is_new_conversation = len(messages) <= 1
        else:
            # Legacy format with single message
            latest_message = body.get("message", "")
            if not latest_message:
                raise HTTPException(status_code=400, detail="No message provided")
            system_prompt = body.get("system_prompt", "You are a helpful assistant.")
            is_new_conversation = True
        
        # Create MCP request for jean_memory tool
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "jean_memory",
                "arguments": {
                    "user_message": latest_message,
                    "is_new_conversation": is_new_conversation,
                    "needs_context": True
                }
            },
            "id": "sdk-mcp-request"
        }
        
        logger.info(f"🧠 SDK MCP: Calling jean_memory tool for message: '{latest_message[:50]}...'")
        
        # Call existing MCP handler
        mcp_response = await handle_mcp_request(mcp_request, current_user, background_tasks)
        
        # Extract context from MCP response
        context = ""
        if mcp_response and "result" in mcp_response:
            context = mcp_response["result"]
            logger.info(f"✅ SDK MCP: Retrieved context (length: {len(context)} chars)")
        else:
            logger.info("💭 SDK MCP: No context retrieved")
        
        # Build response based on request format
        if "messages" in body:
            # Assistant-ui compatible response format
            enhanced_system = system_prompt
            if context:
                enhanced_system += f"\n\nUser's relevant context from Jean Memory:\n{context}"
            
            response = {
                "messages": [
                    {"role": "system", "content": enhanced_system},
                    *body["messages"]
                ],
                "context": context,
                "context_retrieved": bool(context)
            }
        else:
            # Legacy response format
            response = {
                "content": context or "I don't have any relevant context for your question.",
                "context": context,
                "context_retrieved": bool(context),
                "user_id": current_user.user_id,
                "message": latest_message
            }
        
        logger.info(f"🎉 SDK MCP: Chat enhancement completed for user {current_user.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"💥 SDK MCP: Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/health")
async def sdk_mcp_health():
    """Health check for SDK MCP integration"""
    return {
        "status": "healthy",
        "service": "Jean Memory SDK MCP",
        "integration": "Native MCP with jean_memory tool"
    }