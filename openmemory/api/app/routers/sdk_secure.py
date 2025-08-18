"""
Jean Memory SDK v2.0 - Secure Authentication Router
Implements JWT-in-header authentication for enhanced security
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.auth import get_current_user_secure
from app.models import User
from app.mcp_claude_simple import handle_mcp_request
from app.context import user_id_var, client_name_var, background_tasks_var

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/jean-chat", tags=["SDK v2.0 Secure"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    format: Optional[str] = "enhanced"
    conversation_id: Optional[str] = None

class SecureChatRequest(BaseModel):
    messages: List[ChatMessage]
    system_prompt: Optional[str] = None

@router.post("")
async def secure_jean_chat_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_request: ChatRequest,
    user: User = Depends(get_current_user_secure)
):
    """
    Secure Jean Memory SDK chat endpoint v2.0
    
    Authentication:
    - JWT token in Authorization header (user identity)
    - API key in X-API-Key header (app authentication)
    
    This prevents apps from impersonating users.
    """
    logger.info(f"🔒 SDK v2.0: Secure chat request from user {user.user_id}")
    
    try:
        # Set context variables for MCP tools
        user_id_var.set(user.user_id)
        client_name_var.set("Jean Memory SDK v2.0")
        background_tasks_var.set(background_tasks)
        
        latest_message = chat_request.message
        if not latest_message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        # Create MCP request for jean_memory tool
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "jean_memory",
                "arguments": {
                    "user_message": latest_message,
                    "is_new_conversation": True,
                    "needs_context": True
                }
            },
            "id": "sdk-v2-mcp-request"
        }
        
        logger.info(f"🧠 SDK v2.0: Calling jean_memory tool for message: '{latest_message[:50]}...'")
        
        # Call existing MCP handler
        mcp_response = await handle_mcp_request(mcp_request, user, background_tasks)
        
        # Extract context from MCP response
        context = ""
        if mcp_response and "result" in mcp_response:
            context = mcp_response["result"]
            logger.info(f"✅ SDK v2.0: Retrieved context (length: {len(context)} chars)")
        else:
            logger.info("💭 SDK v2.0: No context retrieved")
        
        # Return simple response format
        response = {
            "content": context or "I don't have any relevant context for your question.",
            "context": context,
            "context_retrieved": bool(context),
            "user_id": user.user_id,
            "message": latest_message,
            "version": "2.0-secure"
        }
        
        logger.info(f"🎉 SDK v2.0: Secure chat completed for user {user.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"💥 SDK v2.0: Error processing secure chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Secure chat processing failed: {str(e)}")

@router.post("/messages")
async def secure_messages_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_request: SecureChatRequest,
    user: User = Depends(get_current_user_secure)
):
    """
    Secure messages endpoint for assistant-ui compatibility
    """
    logger.info(f"🔒 SDK v2.0: Secure messages request from user {user.user_id}")
    
    try:
        # Set context variables
        user_id_var.set(user.user_id)
        client_name_var.set("Jean Memory SDK v2.0")
        background_tasks_var.set(background_tasks)
        
        # Get the latest user message
        user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        latest_message = user_messages[-1].content
        
        # Create MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "jean_memory",
                "arguments": {
                    "user_message": latest_message,
                    "is_new_conversation": len(chat_request.messages) <= 1,
                    "needs_context": True
                }
            },
            "id": "sdk-v2-messages-request"
        }
        
        # Call MCP handler
        mcp_response = await handle_mcp_request(mcp_request, user, background_tasks)
        
        # Extract context
        context = ""
        if mcp_response and "result" in mcp_response:
            context = mcp_response["result"]
        
        # Build enhanced system prompt
        system_content = chat_request.system_prompt or "You are a helpful assistant."
        if context:
            system_content += f"\n\nUser's relevant context from Jean Memory:\n{context}"
        
        # Return assistant-ui compatible response
        response = {
            "messages": [
                {"role": "system", "content": system_content},
                *[{"role": msg.role, "content": msg.content} for msg in chat_request.messages]
            ],
            "context": context,
            "context_retrieved": bool(context),
            "version": "2.0-secure"
        }
        
        logger.info(f"🎉 SDK v2.0: Secure messages completed for user {user.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"💥 SDK v2.0: Error processing secure messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Secure messages processing failed: {str(e)}")

@router.get("/health")
async def sdk_v2_health():
    """Health check for SDK v2.0 secure endpoints"""
    return {
        "status": "healthy",
        "service": "Jean Memory SDK v2.0",
        "security": "JWT-in-header authentication",
        "version": "2.0-secure"
    }