"""
Jean Memory SDK MCP Integration Router
Provides MCP-native endpoints for the Jean Memory SDK
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.auth import get_current_supa_user
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

@router.post("")
async def jean_chat_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    chat_request: ChatRequest,
    user: User = Depends(get_current_supa_user)
):
    """
    Jean Memory SDK chat endpoint using existing MCP infrastructure
    This endpoint is designed to work seamlessly with assistant-ui
    """
    logger.info(f"🤖 SDK MCP: Chat request from user {user.user_id}")
    
    try:
        # Set context variables for MCP tools
        user_id_var.set(user.user_id)
        client_name_var.set("Jean Memory SDK")
        background_tasks_var.set(background_tasks)
        
        # Get the latest user message
        user_messages = [msg for msg in chat_request.messages if msg.role == "user"]
        if not user_messages:
            raise HTTPException(status_code=400, detail="No user message found")
        
        latest_message = user_messages[-1].content
        
        # Create MCP request for jean_memory tool
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
            "id": "sdk-mcp-request"
        }
        
        logger.info(f"🧠 SDK MCP: Calling jean_memory tool for message: '{latest_message[:50]}...'")
        
        # Call existing MCP handler
        mcp_response = await handle_mcp_request(mcp_request, user, background_tasks)
        
        # Extract context from MCP response
        context = ""
        if mcp_response and "result" in mcp_response:
            context = mcp_response["result"]
            logger.info(f"✅ SDK MCP: Retrieved context (length: {len(context)} chars)")
        else:
            logger.info("💭 SDK MCP: No context retrieved")
        
        # Build enhanced system prompt
        system_content = chat_request.system_prompt or "You are a helpful assistant."
        if context:
            system_content += f"\n\nUser's relevant context from Jean Memory:\n{context}"
        
        # Return assistant-ui compatible response format
        response = {
            "messages": [
                {"role": "system", "content": system_content},
                *[{"role": msg.role, "content": msg.content} for msg in chat_request.messages]
            ],
            "context": context,
            "context_retrieved": bool(context)
        }
        
        logger.info(f"🎉 SDK MCP: Chat enhancement completed for user {user.user_id}")
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