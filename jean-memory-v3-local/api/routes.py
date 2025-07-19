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
        
        return MemoryResponse(**memory.to_dict())
        
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
            memories=results,
            total=len(results),
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
            memories=results,
            total=len(results),
            query=request.query,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    service = Depends(get_memory_service)
):
    """Get a specific memory by ID"""
    try:
        memory = await service.get_memory(memory_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        return MemoryResponse(**memory.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    service = Depends(get_memory_service)
):
    """Delete a memory"""
    try:
        success = await service.delete_memory(memory_id)
        
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

@router.get("/graph/search", response_model=SearchResponse)
async def search_graph_memories(
    query: str = Query(..., description="Search query"),
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum results"),
    service = Depends(get_memory_service)
):
    """Search memories using graph context"""
    try:
        start_time = datetime.now()
        
        results = await service.graph_service.search_graph_context(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return SearchResponse(
            memories=results,
            total=len(results),
            query=query,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/memories/{user_id}")
async def get_graph_memories(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum results"),
    service = Depends(get_memory_service)
):
    """Get all memories for a user from graph"""
    try:
        memories = await service.graph_service.get_user_memories(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "memories": memories,
            "total": len(memories),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get graph memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph/stats")
async def get_graph_stats(
    user_id: Optional[str] = Query(None, description="User ID for user-specific stats"),
    service = Depends(get_memory_service)
):
    """Get graph service statistics"""
    try:
        stats = await service.graph_service.get_graph_stats(user_id=user_id)
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_to_cloud(
    user_id: str = Query(..., description="User ID"),
    service = Depends(get_memory_service)
):
    """Sync local memories to cloud (placeholder for now)"""
    # This will be implemented in a later phase
    return {
        "message": "Cloud sync not yet implemented",
        "user_id": user_id,
        "status": "pending"
    }

# Function to set the memory service reference
def set_memory_service(service):
    """Set the global memory service reference"""
    global memory_service
    memory_service = service