# Initiative 4: REST API Migration from JSON-RPC

## Overview

This initiative migrates Jean Memory's API from JSON-RPC to a clean REST API design similar to Mem0's simple SDK. The new API will support both local and hosted configurations, providing a seamless developer experience with clear endpoints and consistent patterns.

## Current vs. Target API Design

### Current JSON-RPC Approach
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_memory",
    "arguments": {"query": "my hobbies"}
  },
  "id": 1
}
```

### Target REST API (Mem0-style)
```python
from jean_memory import Memory

m = Memory()
results = m.search(query="my hobbies", user_id="alice")
```

## API Architecture Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│                                                                  │
│  ┌────────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │Python SDK      │  │JavaScript SDK│  │Direct HTTP    │  │
│  │from jean_memory│  │import Memory │  │curl/fetch     │  │
│  │import Memory   │  │from 'jean'   │  │requests       │  │
│  └────────────────┘  └───────────────┘  └──────────────────┘  │
└──────────────────────────────┼────────────────────────────────────┘
                              │ HTTP/HTTPS
┌──────────────────────────────┼────────────────────────────────────┐
│                         REST API Layer                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    REST Endpoints                           │ │
│  │                                                              │ │
│  │  POST /memories         GET /memories/{id}                  │ │
│  │  POST /memories/search  DELETE /memories/{id}               │ │
│  │  PUT /memories/{id}     GET /memories                       │ │
│  │  POST /memories/ask     DELETE /memories                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                    │
│  ┌──────────────────────────────┴───────────────────────────────────┐ │
│  │              Configuration Management                       │ │
│  │                                                              │ │
│  │  Local Mode:           Hosted Mode:                        │ │
│  │  - FAISS + Neo4j       - API Key Auth                      │ │
│  │  - Direct access       - Cloud endpoints                   │ │
│  │  - File config         - Remote config                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Prerequisites

**Depends on**: [INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md)

Before implementing the REST API migration, ensure:
- Local development environment is operational
- API testing infrastructure is available
- Database setup supports both JSON-RPC and REST endpoints
- Test suite can validate both old and new endpoints

## Implementation Plan

### Phase 1: REST API Endpoints

Builds on [JEAN_MEMORY_BACKEND_API.md](./JEAN_MEMORY_BACKEND_API.md) architecture.

#### 1.1 Core Memory Endpoints

```python
# app/routers/memory_rest_api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.auth import get_current_user_or_api_key
from app.models import User
from app.utils.memory_layers import get_memory_layer

router = APIRouter(prefix="/api/v2", tags=["memory-rest"])

# Request/Response Models
class AddMemoryRequest(BaseModel):
    messages: Optional[List[Dict[str, str]]] = None
    memories: Optional[List[str]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    infer: bool = True
    layer: str = Field(default="auto", regex="^(auto|short|long)$")

class MemoryResponse(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    score: Optional[float] = None

class SearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)
    layer: str = Field(default="auto", regex="^(auto|short|long)$")
    filters: Optional[Dict[str, Any]] = None

class UpdateMemoryRequest(BaseModel):
    data: str
    metadata: Optional[Dict[str, Any]] = None

# Core Endpoints
@router.post("/memories", response_model=List[MemoryResponse])
async def add_memories(
    request: AddMemoryRequest,
    user: User = Depends(get_current_user_or_api_key)
):
    """
    Add new memories to the user's memory store.
    
    Supports both message-based inference and direct memory addition.
    """
    user_id = request.user_id or str(user.user_id)
    memory_layer = get_memory_layer(request.layer)
    
    if request.messages:
        # Infer memories from conversation
        if request.infer:
            memories = await memory_layer.infer_memories_from_messages(
                messages=request.messages,
                user_id=user_id,
                metadata=request.metadata
            )
        else:
            # Store raw messages
            memories = await memory_layer.add_raw_messages(
                messages=request.messages,
                user_id=user_id,
                metadata=request.metadata
            )
    elif request.memories:
        # Direct memory addition
        memories = await memory_layer.add_memories(
            memories=request.memories,
            user_id=user_id,
            metadata=request.metadata
        )
    else:
        raise HTTPException(400, "Either 'messages' or 'memories' must be provided")
    
    return [
        MemoryResponse(
            id=memory.id,
            content=memory.content,
            metadata=memory.metadata,
            created_at=memory.created_at.isoformat()
        )
        for memory in memories
    ]

@router.get("/memories", response_model=List[MemoryResponse])
async def get_all_memories(
    user_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    layer: str = Query("auto", regex="^(auto|short|long)$"),
    user: User = Depends(get_current_user_or_api_key)
):
    """Get all memories for a user."""
    user_id = user_id or str(user.user_id)
    memory_layer = get_memory_layer(layer)
    
    memories = await memory_layer.get_all_memories(
        user_id=user_id,
        limit=limit
    )
    
    return [
        MemoryResponse(
            id=memory.id,
            content=memory.content,
            metadata=memory.metadata,
            created_at=memory.created_at.isoformat()
        )
        for memory in memories
    ]

@router.get("/memories/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    user: User = Depends(get_current_user_or_api_key)
):
    """Get a specific memory by ID."""
    memory_layer = get_memory_layer("auto")
    
    memory = await memory_layer.get_memory(
        memory_id=memory_id,
        user_id=str(user.user_id)
    )
    
    if not memory:
        raise HTTPException(404, "Memory not found")
    
    return MemoryResponse(
        id=memory.id,
        content=memory.content,
        metadata=memory.metadata,
        created_at=memory.created_at.isoformat()
    )

@router.post("/memories/search", response_model=List[MemoryResponse])
async def search_memories(
    request: SearchRequest,
    user: User = Depends(get_current_user_or_api_key)
):
    """Search memories using semantic similarity."""
    user_id = request.user_id or str(user.user_id)
    memory_layer = get_memory_layer(request.layer)
    
    results = await memory_layer.search_memories(
        query=request.query,
        user_id=user_id,
        limit=request.limit,
        filters=request.filters
    )
    
    return [
        MemoryResponse(
            id=result.id,
            content=result.content,
            metadata=result.metadata,
            created_at=result.created_at.isoformat(),
            score=result.score
        )
        for result in results
    ]

@router.put("/memories/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: str,
    request: UpdateMemoryRequest,
    user: User = Depends(get_current_user_or_api_key)
):
    """Update a specific memory."""
    memory_layer = get_memory_layer("auto")
    
    updated_memory = await memory_layer.update_memory(
        memory_id=memory_id,
        user_id=str(user.user_id),
        content=request.data,
        metadata=request.metadata
    )
    
    if not updated_memory:
        raise HTTPException(404, "Memory not found")
    
    return MemoryResponse(
        id=updated_memory.id,
        content=updated_memory.content,
        metadata=updated_memory.metadata,
        created_at=updated_memory.created_at.isoformat()
    )

@router.delete("/memories/{memory_id}")
async def delete_memory(
    memory_id: str,
    user: User = Depends(get_current_user_or_api_key)
):
    """Delete a specific memory."""
    memory_layer = get_memory_layer("auto")
    
    success = await memory_layer.delete_memory(
        memory_id=memory_id,
        user_id=str(user.user_id)
    )
    
    if not success:
        raise HTTPException(404, "Memory not found")
    
    return {"message": "Memory deleted successfully"}

@router.delete("/memories")
async def delete_all_memories(
    user_id: Optional[str] = Query(None),
    user: User = Depends(get_current_user_or_api_key)
):
    """Delete all memories for a user."""
    user_id = user_id or str(user.user_id)
    memory_layer = get_memory_layer("auto")
    
    count = await memory_layer.delete_all_memories(user_id=user_id)
    
    return {"message": f"Deleted {count} memories"}

@router.get("/memories/{memory_id}/history")
async def get_memory_history(
    memory_id: str,
    user: User = Depends(get_current_user_or_api_key)
):
    """Get the history of changes for a specific memory."""
    memory_layer = get_memory_layer("auto")
    
    history = await memory_layer.get_memory_history(
        memory_id=memory_id,
        user_id=str(user.user_id)
    )
    
    return {
        "memory_id": memory_id,
        "history": history
    }

# AI-powered endpoints
class AskRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    layer: str = Field(default="auto", regex="^(auto|short|long)$")
    context_limit: int = Field(default=5, ge=1, le=20)

@router.post("/memories/ask")
async def ask_memory(
    request: AskRequest,
    user: User = Depends(get_current_user_or_api_key)
):
    """Ask a question about memories and get an AI-generated response."""
    user_id = request.user_id or str(user.user_id)
    memory_layer = get_memory_layer(request.layer)
    
    response = await memory_layer.ask_memory(
        question=request.question,
        user_id=user_id,
        context_limit=request.context_limit
    )
    
    return {
        "question": request.question,
        "answer": response.answer,
        "context": response.context,
        "sources": response.sources
    }
```

#### 1.2 Enhanced Authentication

Builds on [JEAN_MEMORY_BACKEND_API.md](./JEAN_MEMORY_BACKEND_API.md) auth system.

```python
# app/auth.py (Enhanced)
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import User, ApiKey
from app.database import get_db
from sqlalchemy.orm import Session
import hashlib

security = HTTPBearer(auto_error=False)

async def get_current_user_or_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Enhanced authentication supporting both Supabase JWT and API keys.
    Designed for REST API compatibility.
    """
    
    if not credentials:
        raise HTTPException(401, "Authentication required")
    
    token = credentials.credentials
    
    # Try API Key authentication first (for SDK usage)
    if token.startswith("jean_sk_"):
        return await authenticate_api_key(token, db)
    
    # Fall back to Supabase JWT
    return await authenticate_supabase_jwt(token, db)

async def authenticate_api_key(api_key: str, db: Session) -> User:
    """Authenticate using Jean Memory API key."""
    
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    db_api_key = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()
    
    if not db_api_key:
        raise HTTPException(401, "Invalid API key")
    
    # Update last used timestamp
    db_api_key.last_used_at = datetime.datetime.now(datetime.UTC)
    db.commit()
    
    return db_api_key.user

async def authenticate_supabase_jwt(token: str, db: Session) -> User:
    """Authenticate using Supabase JWT token."""
    
    try:
        from app.auth import supabase_service_client
        
        supa_user = supabase_service_client.auth.get_user(token)
        if not supa_user:
            raise HTTPException(401, "Invalid token")
        
        # Get internal user
        db_user = db.query(User).filter(
            User.user_id == str(supa_user.user.id)
        ).first()
        
        if not db_user:
            raise HTTPException(401, "User not found")
        
        return db_user
        
    except Exception:
        raise HTTPException(401, "Invalid token")
```

### Phase 2: Python SDK

#### 2.1 Core SDK Design

```python
# jean_memory_sdk/memory.py
import os
import requests
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

class MemoryLayer(Enum):
    AUTO = "auto"
    SHORT = "short"
    LONG = "long"

@dataclass
class MemoryResult:
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: str
    score: Optional[float] = None

@dataclass
class SearchResponse:
    results: List[MemoryResult]
    query: str
    total: int
    layer_used: str

class Memory:
    """
    Jean Memory SDK - Simple interface for memory operations.
    
    Usage:
        # Local mode
        m = Memory(config={
            "vector_store": {"provider": "faiss"},
            "graph_store": {"provider": "neo4j"}
        })
        
        # Hosted mode
        m = Memory(api_key="jean_sk_...")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("JEAN_MEMORY_API_KEY")
        self.config = config
        self.base_url = base_url or os.getenv("JEAN_MEMORY_BASE_URL", "https://jean-memory-api-virginia.onrender.com")
        
        # Determine mode
        if self.api_key:
            self.mode = "hosted"
            self._setup_hosted_client()
        elif self.config:
            self.mode = "local"
            self._setup_local_client()
        else:
            raise ValueError("Either api_key or config must be provided")
    
    def _setup_hosted_client(self):
        """Setup HTTP client for hosted mode."""
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def _setup_local_client(self):
        """Setup local Jean Memory instance."""
        from .local_memory import LocalMemory
        self.local_client = LocalMemory(self.config)
    
    def add(
        self,
        messages: Optional[List[Dict[str, str]]] = None,
        memories: Optional[List[str]] = None,
        user_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
        infer: bool = True,
        layer: Union[str, MemoryLayer] = MemoryLayer.AUTO
    ) -> List[MemoryResult]:
        """
        Add memories to the store.
        
        Args:
            messages: Conversation messages to infer memories from
            memories: Direct memory strings to add
            user_id: User identifier
            metadata: Additional metadata to attach
            infer: Whether to infer memories from messages
            layer: Which memory layer to use
            
        Returns:
            List of created memory objects
        """
        if isinstance(layer, MemoryLayer):
            layer = layer.value
            
        if self.mode == "hosted":
            return self._add_hosted(messages, memories, user_id, metadata, infer, layer)
        else:
            return self._add_local(messages, memories, user_id, metadata, infer, layer)
    
    def _add_hosted(
        self, 
        messages: Optional[List[Dict[str, str]]],
        memories: Optional[List[str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]],
        infer: bool,
        layer: str
    ) -> List[MemoryResult]:
        """Add memories via hosted API."""
        
        payload = {
            "user_id": user_id,
            "metadata": metadata,
            "infer": infer,
            "layer": layer
        }
        
        if messages:
            payload["messages"] = messages
        elif memories:
            payload["memories"] = memories
        else:
            raise ValueError("Either messages or memories must be provided")
        
        response = self.session.post(
            f"{self.base_url}/api/v2/memories",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return [MemoryResult(**item) for item in data]
    
    def _add_local(
        self,
        messages: Optional[List[Dict[str, str]]],
        memories: Optional[List[str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]],
        infer: bool,
        layer: str
    ) -> List[MemoryResult]:
        """Add memories via local client."""
        
        if messages:
            if infer:
                return self.local_client.infer_and_add(messages, user_id, metadata, layer)
            else:
                return self.local_client.add_messages(messages, user_id, metadata, layer)
        elif memories:
            return self.local_client.add_memories(memories, user_id, metadata, layer)
    
    def search(
        self,
        query: str,
        user_id: str = "default",
        limit: int = 10,
        layer: Union[str, MemoryLayer] = MemoryLayer.AUTO,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryResult]:
        """
        Search memories using semantic similarity.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results
            layer: Which memory layer to search
            filters: Additional filters to apply
            
        Returns:
            List of matching memories with relevance scores
        """
        if isinstance(layer, MemoryLayer):
            layer = layer.value
            
        if self.mode == "hosted":
            return self._search_hosted(query, user_id, limit, layer, filters)
        else:
            return self._search_local(query, user_id, limit, layer, filters)
    
    def _search_hosted(
        self,
        query: str,
        user_id: str,
        limit: int,
        layer: str,
        filters: Optional[Dict[str, Any]]
    ) -> List[MemoryResult]:
        """Search memories via hosted API."""
        
        payload = {
            "query": query,
            "user_id": user_id,
            "limit": limit,
            "layer": layer,
            "filters": filters
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v2/memories/search",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        return [MemoryResult(**item) for item in data]
    
    def get_all(self, user_id: str = "default", limit: int = 100) -> List[MemoryResult]:
        """Get all memories for a user."""
        
        if self.mode == "hosted":
            response = self.session.get(
                f"{self.base_url}/api/v2/memories",
                params={"user_id": user_id, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()
            return [MemoryResult(**item) for item in data]
        else:
            return self.local_client.get_all_memories(user_id, limit)
    
    def get(self, memory_id: str) -> Optional[MemoryResult]:
        """Get a specific memory by ID."""
        
        if self.mode == "hosted":
            response = self.session.get(f"{self.base_url}/api/v2/memories/{memory_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return MemoryResult(**response.json())
        else:
            return self.local_client.get_memory(memory_id)
    
    def update(self, memory_id: str, data: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryResult:
        """Update a memory."""
        
        if self.mode == "hosted":
            payload = {"data": data, "metadata": metadata}
            response = self.session.put(
                f"{self.base_url}/api/v2/memories/{memory_id}",
                json=payload
            )
            response.raise_for_status()
            return MemoryResult(**response.json())
        else:
            return self.local_client.update_memory(memory_id, data, metadata)
    
    def delete(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        
        if self.mode == "hosted":
            response = self.session.delete(f"{self.base_url}/api/v2/memories/{memory_id}")
            return response.status_code == 200
        else:
            return self.local_client.delete_memory(memory_id)
    
    def delete_all(self, user_id: str = "default") -> int:
        """Delete all memories for a user."""
        
        if self.mode == "hosted":
            response = self.session.delete(
                f"{self.base_url}/api/v2/memories",
                params={"user_id": user_id}
            )
            response.raise_for_status()
            return response.json()["count"]
        else:
            return self.local_client.delete_all_memories(user_id)
    
    def history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Get the history of changes for a memory."""
        
        if self.mode == "hosted":
            response = self.session.get(f"{self.base_url}/api/v2/memories/{memory_id}/history")
            response.raise_for_status()
            return response.json()["history"]
        else:
            return self.local_client.get_memory_history(memory_id)
    
    def ask(
        self,
        question: str,
        user_id: str = "default",
        layer: Union[str, MemoryLayer] = MemoryLayer.AUTO,
        context_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Ask a question about memories and get an AI-generated response.
        
        Args:
            question: Question to ask
            user_id: User identifier
            layer: Which memory layer to query
            context_limit: Maximum number of memories to use as context
            
        Returns:
            Dictionary with answer, context, and sources
        """
        if isinstance(layer, MemoryLayer):
            layer = layer.value
            
        if self.mode == "hosted":
            payload = {
                "question": question,
                "user_id": user_id,
                "layer": layer,
                "context_limit": context_limit
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v2/memories/ask",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        else:
            return self.local_client.ask_memory(question, user_id, layer, context_limit)
    
    def reset(self, user_id: str = "default") -> bool:
        """Reset all memories for a user (alias for delete_all)."""
        count = self.delete_all(user_id)
        return count >= 0
```

#### 2.2 Local Memory Implementation

Builds on [INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md).

```python
# jean_memory_sdk/local_memory.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid
import datetime

class LocalMemory:
    """
    Local implementation of Jean Memory using configured providers.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._setup_providers()
    
    def _setup_providers(self):
        """Initialize local providers based on config."""
        
        # Vector store setup
        vector_config = self.config.get("vector_store", {})
        if vector_config.get("provider") == "faiss":
            from .providers.faiss_provider import FAISSProvider
            self.vector_store = FAISSProvider(vector_config.get("config", {}))
        elif vector_config.get("provider") == "qdrant":
            from .providers.qdrant_provider import QdrantProvider
            self.vector_store = QdrantProvider(vector_config.get("config", {}))
        else:
            raise ValueError(f"Unsupported vector store: {vector_config.get('provider')}")
        
        # Graph store setup
        graph_config = self.config.get("graph_store", {})
        if graph_config.get("provider") == "neo4j":
            from .providers.neo4j_provider import Neo4jProvider
            self.graph_store = Neo4jProvider(graph_config.get("config", {}))
        
        # LLM setup
        llm_config = self.config.get("llm", {"provider": "openai"})
        if llm_config.get("provider") == "openai":
            from .providers.openai_provider import OpenAIProvider
            self.llm = OpenAIProvider(llm_config.get("config", {}))
        
        # Embedder setup
        embedder_config = self.config.get("embedder", {"provider": "openai"})
        if embedder_config.get("provider") == "openai":
            from .providers.openai_provider import OpenAIEmbedder
            self.embedder = OpenAIEmbedder(embedder_config.get("config", {}))
    
    def add_memories(
        self,
        memories: List[str],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        layer: str = "auto"
    ) -> List[MemoryResult]:
        """Add memories to local storage."""
        
        results = []
        
        for memory_text in memories:
            # Generate embedding
            embedding = self.embedder.embed(memory_text)
            
            # Create memory object
            memory_id = str(uuid.uuid4())
            memory_obj = {
                "id": memory_id,
                "content": memory_text,
                "user_id": user_id,
                "metadata": metadata or {},
                "embedding": embedding,
                "created_at": datetime.datetime.utcnow().isoformat()
            }
            
            # Store in vector database
            self.vector_store.add(memory_id, embedding, memory_obj)
            
            # Store in graph database if available
            if hasattr(self, 'graph_store'):
                self.graph_store.add_memory_node(memory_obj)
            
            results.append(MemoryResult(
                id=memory_id,
                content=memory_text,
                metadata=memory_obj["metadata"],
                created_at=memory_obj["created_at"]
            ))
        
        return results
    
    def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        layer: str = "auto",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryResult]:
        """Search memories using semantic similarity."""
        
        # Generate query embedding
        query_embedding = self.embedder.embed(query)
        
        # Search vector store
        search_results = self.vector_store.search(
            query_embedding,
            limit=limit,
            filters={"user_id": user_id, **(filters or {})}
        )
        
        # Convert to MemoryResult objects
        results = []
        for result in search_results:
            results.append(MemoryResult(
                id=result["id"],
                content=result["content"],
                metadata=result["metadata"],
                created_at=result["created_at"],
                score=result["score"]
            ))
        
        return results
```

### Phase 3: Configuration Management

#### 3.1 Configuration Schema

```python
# jean_memory_sdk/config.py
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import os
from pathlib import Path
import yaml

class VectorStoreConfig(BaseModel):
    provider: str = Field(..., description="Vector store provider (faiss, qdrant, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict)

class GraphStoreConfig(BaseModel):
    provider: str = Field(..., description="Graph store provider (neo4j, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict)

class LLMConfig(BaseModel):
    provider: str = Field(default="openai", description="LLM provider")
    config: Dict[str, Any] = Field(default_factory=dict)

class EmbedderConfig(BaseModel):
    provider: str = Field(default="openai", description="Embedder provider")
    config: Dict[str, Any] = Field(default_factory=dict)

class JeanMemoryConfig(BaseModel):
    vector_store: VectorStoreConfig
    graph_store: Optional[GraphStoreConfig] = None
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedder: EmbedderConfig = Field(default_factory=EmbedderConfig)
    history_db_path: Optional[str] = None
    version: str = Field(default="v2.0")
    custom_fact_extraction_prompt: Optional[str] = None
    custom_update_memory_prompt: Optional[str] = None

# Preset configurations
PRESET_CONFIGS = {
    "local_fast": {
        "vector_store": {
            "provider": "faiss",
            "config": {
                "index_path": "~/.jean_memory/faiss_index",
                "dimension": 1536
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "uri": "bolt://localhost:7687",
                "auth": ["neo4j", "jeanmemory123"]
            }
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini"
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small"
            }
        }
    },
    "local_qdrant": {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": "localhost",
                "port": 6333
            }
        },
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "uri": "bolt://localhost:7687",
                "auth": ["neo4j", "password"]
            }
        }
    }
}

def load_config(config_path: Optional[str] = None, preset: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file or preset."""
    
    if preset:
        if preset not in PRESET_CONFIGS:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(PRESET_CONFIGS.keys())}")
        return PRESET_CONFIGS[preset]
    
    if config_path:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file) as f:
            if config_file.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif config_file.suffix == '.json':
                import json
                return json.load(f)
    
    # Try to load from default locations
    default_paths = [
        Path.home() / ".jean_memory" / "config.yaml",
        Path.cwd() / "jean_memory_config.yaml",
        Path.cwd() / ".jean_memory.yaml"
    ]
    
    for path in default_paths:
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f)
    
    # Return default local config
    return PRESET_CONFIGS["local_fast"]
```

### Phase 4: API Documentation Update

Builds on [JEAN_MEMORY_BACKEND_API.md](./JEAN_MEMORY_BACKEND_API.md).

#### 4.1 OpenAPI Specification

```python
# app/main.py (Updated with new REST routes)
from app.routers.memory_rest_api import router as memory_rest_router

# Include the new REST API router
app.include_router(memory_rest_router)

# Update OpenAPI metadata
app.openapi_info = {
    "title": "Jean Memory REST API",
    "version": "2.0.0",
    "description": """
    Jean Memory REST API provides simple, Mem0-compatible endpoints for memory operations.
    
    ## Authentication
    
    The API supports two authentication methods:
    
    1. **API Key**: Pass your Jean Memory API key in the Authorization header:
       ```
       Authorization: Bearer jean_sk_your_api_key_here
       ```
    
    2. **Supabase JWT**: Use your Supabase JWT token:
       ```
       Authorization: Bearer your_supabase_jwt_token
       ```
    
    ## Usage Examples
    
    ### Python SDK
    ```python
    from jean_memory import Memory
    
    # Hosted mode
    m = Memory(api_key="jean_sk_...")
    
    # Local mode
    m = Memory(config={
        "vector_store": {"provider": "faiss"},
        "graph_store": {"provider": "neo4j"}
    })
    
    # Add memories
    result = m.add(["I love hiking", "My favorite color is blue"], user_id="alice")
    
    # Search memories
    results = m.search("What are my hobbies?", user_id="alice")
    ```
    
    ### Direct HTTP
    ```bash
    # Add memories
    curl -X POST https://jean-memory-api-virginia.onrender.com/api/v2/memories \
      -H "Authorization: Bearer jean_sk_..." \
      -H "Content-Type: application/json" \
      -d '{"memories": ["I love hiking"], "user_id": "alice"}'
    
    # Search memories
    curl -X POST https://jean-memory-api-virginia.onrender.com/api/v2/memories/search \
      -H "Authorization: Bearer jean_sk_..." \
      -H "Content-Type: application/json" \
      -d '{"query": "What are my hobbies?", "user_id": "alice"}'
    ```
    """,
    "contact": {
        "name": "Jean Memory Support",
        "url": "https://jeanmemory.com/support",
        "email": "support@jeanmemory.com"
    },
    "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
}
```

#### 4.2 Frontend API Documentation Page Update

Builds on [JEAN_MEMORY_FRONTEND.md](./JEAN_MEMORY_FRONTEND.md).

```typescript
// app/api-docs/page.tsx (Updated)
"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Copy, ExternalLink } from 'lucide-react';
import { CodeBlock } from '@/components/ui/code-block';

const API_EXAMPLES = {
  python: {
    setup: `# Install the SDK
pip install jean-memory

# Import and initialize
from jean_memory import Memory

# Hosted mode (recommended)
m = Memory(api_key="jean_sk_your_api_key_here")

# Local mode
m = Memory(config={
    "vector_store": {
        "provider": "faiss",
        "config": {
            "index_path": "~/.jean_memory/faiss_index"
        }
    },
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "uri": "bolt://localhost:7687",
            "auth": ["neo4j", "password"]
        }
    }
})`,
    add: `# Add memories from conversation
messages = [
    {"role": "user", "content": "I love hiking in the mountains"},
    {"role": "assistant", "content": "That sounds wonderful! Do you have a favorite trail?"}
]
result = m.add(messages, user_id="alice", metadata={"category": "hobbies"})

# Add direct memories
result = m.add(memories=["I prefer tea over coffee"], user_id="alice")
print(f"Added {len(result)} memories")`,
    search: `# Search memories
results = m.search(query="What do I like to drink?", user_id="alice")
for result in results:
    print(f"Score: {result.score:.2f} - {result.content}")

# Get all memories
all_memories = m.get_all(user_id="alice")
print(f"Total memories: {len(all_memories)}")`,
    ask: `# Ask questions about memories
response = m.ask("What are my hobbies?", user_id="alice")
print(f"Answer: {response['answer']}")
print(f"Sources: {len(response['sources'])} memories used")`
  },
  curl: {
    add: `curl -X POST https://jean-memory-api-virginia.onrender.com/api/v2/memories \
  -H "Authorization: Bearer jean_sk_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "memories": ["I love hiking in the mountains"],
    "user_id": "alice",
    "metadata": {"category": "hobbies"}
  }'`,
    search: `curl -X POST https://jean-memory-api-virginia.onrender.com/api/v2/memories/search \
  -H "Authorization: Bearer jean_sk_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are my hobbies?",
    "user_id": "alice",
    "limit": 5
  }'`,
    get: `curl -X GET "https://jean-memory-api-virginia.onrender.com/api/v2/memories?user_id=alice&limit=10" \
  -H "Authorization: Bearer jean_sk_your_api_key_here"`,
    ask: `curl -X POST https://jean-memory-api-virginia.onrender.com/api/v2/memories/ask \
  -H "Authorization: Bearer jean_sk_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are my main interests?",
    "user_id": "alice"
  }'`
  }
};

export default function APIDocsPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  
  return (
    <div className="container mx-auto py-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4">Jean Memory REST API</h1>
        <p className="text-xl text-muted-foreground">
          Simple, powerful memory operations with Mem0-compatible interface
        </p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="quickstart">Quick Start</TabsTrigger>
          <TabsTrigger value="endpoints">Endpoints</TabsTrigger>
          <TabsTrigger value="examples">Examples</TabsTrigger>
          <TabsTrigger value="migration">Migration</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Jean Memory REST API v2.0</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                The Jean Memory REST API provides a simple, intuitive interface for memory operations,
                compatible with the Mem0 SDK pattern. Choose between hosted cloud service or local deployment.
              </p>
              
              <div className="grid md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      ☁️ Hosted Mode
                      <Badge>Recommended</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• No setup required</li>
                      <li>• Scalable cloud infrastructure</li>
                      <li>• Cross-device synchronization</li>
                      <li>• Enterprise-grade security</li>
                    </ul>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">🏠 Local Mode</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2 text-sm">
                      <li>• Complete data privacy</li>
                      <li>• No network dependency</li>
                      <li>• Customizable providers</li>
                      <li>• Fast local operations</li>
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="quickstart" className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Quick Start Guide</h2>
            <div className="flex gap-2">
              <Button
                variant={selectedLanguage === 'python' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedLanguage('python')}
              >
                Python SDK
              </Button>
              <Button
                variant={selectedLanguage === 'curl' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSelectedLanguage('curl')}
              >
                HTTP/cURL
              </Button>
            </div>
          </div>
          
          {selectedLanguage === 'python' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>1. Installation & Setup</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="python" code={API_EXAMPLES.python.setup} />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>2. Add Memories</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="python" code={API_EXAMPLES.python.add} />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>3. Search Memories</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="python" code={API_EXAMPLES.python.search} />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>4. Ask Questions</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="python" code={API_EXAMPLES.python.ask} />
                </CardContent>
              </Card>
            </div>
          )}
          
          {selectedLanguage === 'curl' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Add Memories</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="bash" code={API_EXAMPLES.curl.add} />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Search Memories</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="bash" code={API_EXAMPLES.curl.search} />
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Get All Memories</CardTitle>
                </CardHeader>
                <CardContent>
                  <CodeBlock language="bash" code={API_EXAMPLES.curl.get} />
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

## Migration Strategy

### Backward Compatibility
1. Keep existing JSON-RPC endpoints for MCP clients
2. Add new REST endpoints alongside existing ones
3. Gradual deprecation timeline (6+ months)
4. Clear migration documentation

### Performance Targets
- **API Response Time**: <200ms for simple operations
- **SDK Initialization**: <1s for hosted mode, <5s for local mode
- **Memory Operations**: Same performance as current system
- **Configuration Loading**: <100ms

## References

- [Local Development Setup](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md) - **Required prerequisite**
- [Backend API Documentation](./JEAN_MEMORY_BACKEND_API.md) - For existing API structure
- [Frontend Architecture](./JEAN_MEMORY_FRONTEND.md) - For documentation UI
- [Short-term Memory System](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md) - For local mode integration