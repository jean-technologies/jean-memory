"""
Jean Memory HTTP API Router
Provides simple HTTP endpoints for jean_memory functionality
"""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import time

from app.tools.orchestration import jean_memory
from app.context import user_id_var, client_name_var, background_tasks_var

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["jean-memory"])

class JeanMemoryRequest(BaseModel):
    user_message: str
    is_new_conversation: bool
    needs_context: bool
    user_id: str
    client_name: str

class JeanMemoryResponse(BaseModel):
    context: str
    response_time: float
    status: str
    user_id: str
    client_name: str

@router.post("/jean_memory", response_model=JeanMemoryResponse)
async def jean_memory_endpoint(
    request: JeanMemoryRequest,
    background_tasks: BackgroundTasks
) -> JeanMemoryResponse:
    """
    Jean Memory HTTP endpoint for production testing
    
    This endpoint exposes the jean_memory function via HTTP API,
    allowing external clients (like Claude) to interact with Jean Memory
    through standard REST calls.
    """
    start_time = time.time()
    
    try:
        logger.info(f"🌐 Jean Memory API call from {request.client_name} for user {request.user_id}")
        
        # Set up context variables (similar to local mode)
        user_id_var.set(request.user_id)
        client_name_var.set(request.client_name)
        background_tasks_var.set(background_tasks)
        
        # Call the jean_memory function
        context = await jean_memory(
            user_message=request.user_message,
            is_new_conversation=request.is_new_conversation,
            needs_context=request.needs_context
        )
        
        response_time = time.time() - start_time
        
        return JeanMemoryResponse(
            context=context,
            response_time=response_time,
            status="success",
            user_id=request.user_id,
            client_name=request.client_name
        )
        
    except Exception as e:
        logger.error(f"❌ Jean Memory API error: {str(e)}")
        response_time = time.time() - start_time
        
        return JeanMemoryResponse(
            context=f"Error: {str(e)}",
            response_time=response_time,
            status="error",
            user_id=request.user_id,
            client_name=request.client_name
        )