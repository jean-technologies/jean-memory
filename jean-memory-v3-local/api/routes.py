"""
API Routes for Jean Memory V3 Local Service
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

# We'll need to get the memory service instance
# For now, we'll create a global reference that gets set in main.py

logger = logging.getLogger(__name__)

# Global memory service reference (set by main.py)
memory_service = None

def get_memory_service():
    """Dependency to get memory service"""
    if memory_service is None or not memory_service.is_ready():
        raise HTTPException(status_code=503, detail="Memory service not ready")
    return memory_service

# Request/Response Models
class CreateMemoryRequest(BaseModel):
    content: str = Field(..., description="Memory content")
    user_id: str = Field(..., description="User ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class MemoryResponse(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str
    source: str

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    user_id: str = Field(..., description="User ID")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results")
    threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Similarity threshold")

class SearchResponse(BaseModel):
    memories: List[Dict[str, Any]]
    total: int
    query: str
    execution_time_ms: int

class StatsResponse(BaseModel):
    total_memories: int
    index_size: int
    embedding_dim: int
    oldest_memory: Optional[str]
    newest_memory: Optional[str]
    model: str

# Create router
router = APIRouter()

@router.post("/memories/", response_model=MemoryResponse)
async def create_memory(
    request: CreateMemoryRequest,
    service = Depends(get_memory_service)
):
    """Create a new memory in local storage"""
    try:
        logger.info(f"Creating memory for user {request.user_id}")
        
        memory = await service.add_memory(
            content=request.content,
            user_id=request.user_id,
            metadata=request.metadata
        )
        
        return MemoryResponse(**memory)
        
    except Exception as e:
        logger.error(f"Failed to create memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/search", response_model=SearchResponse)
async def search_memories(
    query: str = Query(..., description="Search query"),
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
    threshold: float = Query(default=0.3, ge=0.0, le=1.0, description="Similarity threshold"),
    service = Depends(get_memory_service)
):
    """Search memories using semantic similarity"""
    try:
        start_time = datetime.now()
        
        results = await service.search_memories(
            query=query,
            user_id=user_id,
            limit=limit,
            threshold=threshold
        )
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return SearchResponse(
            memories=results.get("memories", []),
            total=results.get("total", 0),
            query=query,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memories/search", response_model=SearchResponse)
async def search_memories_post(
    request: SearchRequest,
    service = Depends(get_memory_service)
):
    """Search memories using semantic similarity (POST version)"""
    try:
        start_time = datetime.now()
        
        results = await service.search_memories(
            query=request.query,
            user_id=request.user_id,
            limit=request.limit,
            threshold=request.threshold
        )
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return SearchResponse(
            memories=results.get("memories", []),
            total=results.get("total", 0),
            query=request.query,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    user_id: str = Query(..., description="User ID"),
    service = Depends(get_memory_service)
):
    """Get a specific memory by ID"""
    try:
        memory = await service.get_memory(memory_id, user_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return MemoryResponse(**memory)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str = Query(..., description="User ID"),
    service = Depends(get_memory_service)
):
    """Delete a memory"""
    try:
        success = await service.delete_memory(memory_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return {"message": "Memory deleted successfully", "id": memory_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    user_id: Optional[str] = Query(None, description="User ID for user-specific stats"),
    service = Depends(get_memory_service)
):
    """Get memory service statistics"""
    try:
        stats = await service.get_stats(user_id=user_id)
        
        return StatsResponse(
            total_memories=stats["total_memories"],
            index_size=stats["index_size"],
            embedding_dim=stats["embedding_dim"],
            oldest_memory=stats["oldest_memory"].isoformat() if stats["oldest_memory"] else None,
            newest_memory=stats["newest_memory"].isoformat() if stats["newest_memory"] else None,
            model=stats["model"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# V3 Session Management Endpoints
@router.post("/sessions/")
async def create_session(
    user_id: str = Query(..., description="User ID"),
    metadata: Optional[Dict[str, Any]] = None,
    service = Depends(get_memory_service)
):
    """Create new session"""
    try:
        session_id = await service.create_session(user_id, metadata)
        return {"session_id": session_id, "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    service = Depends(get_memory_service)
):
    """Get session data"""
    try:
        session = await service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/state")
async def update_session_state(
    session_id: str,
    key: str,
    value: Any,
    service = Depends(get_memory_service)
):
    """Update session state"""
    try:
        success = await service.update_session_state(session_id, key, value)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session state updated", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update session state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# V3 Memory Shuttle Endpoints
@router.post("/shuttle/sync")
async def force_sync_to_ltm(
    user_id: str = Query(..., description="User ID"),
    service = Depends(get_memory_service)
):
    """Force immediate sync of user memories to LTM"""
    try:
        result = await service.force_sync_to_ltm(user_id)
        return result
        
    except Exception as e:
        logger.error(f"Failed to sync to LTM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/shuttle/preload")
async def preload_hot_memories(
    user_id: str = Query(..., description="User ID"),
    service = Depends(get_memory_service)
):
    """Preload hot memories from LTM to STM"""
    try:
        result = await service.preload_hot_memories(user_id)
        return result
        
    except Exception as e:
        logger.error(f"Failed to preload memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shuttle/stats")
async def get_shuttle_stats(
    user_id: Optional[str] = Query(None, description="User ID for user-specific stats"),
    service = Depends(get_memory_service)
):
    """Get Memory Shuttle statistics"""
    try:
        stats = await service.get_shuttle_stats(user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get shuttle stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# V3 Enhanced Memory Endpoints
@router.get("/memories/user/{user_id}")
async def get_user_memories(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
    source: str = Query(default="hybrid", description="Memory source: stm, ltm, or hybrid"),
    service = Depends(get_memory_service)
):
    """Get user memories from specified source(s)"""
    try:
        if hasattr(service.memory_service, 'get_user_memories'):
            result = await service.memory_service.get_user_memories(
                user_id=user_id,
                limit=limit,
                source=source
            )
            return result
        else:
            # Fallback to search for all memories
            result = await service.search_memories("", user_id, limit)
            return result
        
    except Exception as e:
        logger.error(f"Failed to get user memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Function to set the memory service reference
def set_memory_service(service):
    """Set the global memory service reference"""
    global memory_service
    memory_service = service