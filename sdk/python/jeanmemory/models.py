"""
Jean Memory Python SDK Data Models
Pydantic models for type safety and validation
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum

try:
    from pydantic import BaseModel, Field, validator
except ImportError:
    # Fallback for when pydantic is not installed
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(*args, **kwargs):
        return None
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MemoryStatus(str, Enum):
    """Memory processing status"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class Memory(BaseModel):
    """
    Individual memory object
    """
    id: str = Field(..., description="Unique memory identifier")
    content: str = Field(..., description="Memory content")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    status: MemoryStatus = Field(default=MemoryStatus.PROCESSED, description="Processing status")
    embedding_vector: Optional[List[float]] = Field(None, description="Vector embedding")
    relevance_score: Optional[float] = Field(None, description="Relevance score for search results")
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

class MemorySearchResult(BaseModel):
    """
    Search result containing memories and metadata
    """
    memories: List[Memory] = Field(default_factory=list, description="List of matching memories")
    total: int = Field(..., description="Total number of matching memories")
    query: str = Field(..., description="Original search query")
    limit: int = Field(..., description="Maximum results requested")
    offset: int = Field(default=0, description="Results offset")
    search_time_ms: Optional[int] = Field(None, description="Search execution time in milliseconds")

class MemoryCreateRequest(BaseModel):
    """
    Request model for creating a new memory
    """
    content: str = Field(..., description="Memory content")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

class MemoryCreateResponse(BaseModel):
    """
    Response model for memory creation
    """
    id: str = Field(..., description="Created memory ID")
    status: str = Field(..., description="Creation status")
    message: str = Field(..., description="Status message")

class UserInfo(BaseModel):
    """
    User information model
    """
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    created_at: datetime = Field(..., description="Account creation date")
    subscription_tier: Optional[str] = Field(None, description="Subscription level")
    memory_count: Optional[int] = Field(None, description="Total memories stored")
    
    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

class APIResponse(BaseModel):
    """
    Generic API response wrapper
    """
    success: bool = Field(..., description="Request success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class HealthStatus(BaseModel):
    """
    API health check response
    """
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    uptime_seconds: Optional[int] = Field(None, description="Service uptime")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")
    authenticated: bool = Field(..., description="Authentication status")

class PaginationMeta(BaseModel):
    """
    Pagination metadata
    """
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    has_next: bool = Field(..., description="Whether more items exist")
    has_prev: bool = Field(..., description="Whether previous items exist")

class MemoryListResponse(BaseModel):
    """
    Response for paginated memory lists
    """
    memories: List[Memory] = Field(default_factory=list, description="List of memories")
    pagination: PaginationMeta = Field(..., description="Pagination information")

class ContextResponse:
    """Response object for get_context method to match documentation"""
    def __init__(self, text: str, metadata: Optional[Dict] = None):
        self.text = text
        self.metadata = metadata or {}
        self.speed = self.metadata.get('speed', 'balanced')
        self.tool_used = self.metadata.get('tool', 'jean_memory')
        self.format = self.metadata.get('format', 'enhanced')
    
    def __str__(self):
        return self.text
    
    def __repr__(self):
        return f"ContextResponse(text='{self.text[:50]}...', speed='{self.speed}', tool='{self.tool_used}')"

# Type aliases for convenience
MemoryDict = Dict[str, Any]
ContextDict = Dict[str, Any]