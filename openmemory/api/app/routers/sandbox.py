"""Sandbox router for anonymous user trial experience"""

import datetime
import uuid
import jwt
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.models import User, App, Memory, MemoryState
from app.utils.db import get_or_create_user
from app.utils.memory import get_memory_client

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])

# JWT settings for sandbox sessions
SANDBOX_JWT_SECRET = os.getenv("SANDBOX_JWT_SECRET", "sandbox-secret-key-change-in-production")
SANDBOX_JWT_ALGORITHM = "HS256"
SANDBOX_SESSION_DURATION_HOURS = 24

class SandboxSessionResponse(BaseModel):
    session_token: str
    expires_in: int
    user_id: str

class SandboxMemoryRequest(BaseModel):
    text: str

class SandboxMemoryResponse(BaseModel):
    id: str
    content: str
    created_at: str
    success: bool
    message: str

def create_sandbox_user(db: Session) -> User:
    """Create a new anonymous user for sandbox sessions"""
    sandbox_user_id = f"sandbox_{uuid.uuid4().hex[:16]}"
    
    user = User(
        user_id=sandbox_user_id,
        name="Sandbox User",
        email=None,
        is_anonymous=True,
        last_seen_at=datetime.datetime.now(datetime.timezone.utc),
        metadata_={
            "sandbox": True,
            "created_for": "trial_experience",
            "expires_at": (datetime.datetime.now(datetime.timezone.utc) + 
                          datetime.timedelta(hours=SANDBOX_SESSION_DURATION_HOURS)).isoformat()
        }
    )
    
    db.add(user)
    db.flush()
    
    # Create default app for sandbox user
    app = App(
        owner_id=user.id,
        name="sandbox_app",
        description="Sandbox application for trial users",
        is_active=True,
        metadata_={"sandbox": True}
    )
    
    db.add(app)
    db.commit()
    
    return user

def create_sandbox_jwt(user_id: str) -> str:
    """Create JWT token for sandbox session"""
    payload = {
        "user_id": user_id,
        "is_sandbox": True,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=SANDBOX_SESSION_DURATION_HOURS),
        "iat": datetime.datetime.now(datetime.timezone.utc)
    }
    
    return jwt.encode(payload, SANDBOX_JWT_SECRET, algorithm=SANDBOX_JWT_ALGORITHM)

def verify_sandbox_jwt(token: str) -> dict:
    """Verify and decode sandbox JWT token"""
    try:
        payload = jwt.decode(token, SANDBOX_JWT_SECRET, algorithms=[SANDBOX_JWT_ALGORITHM])
        if not payload.get("is_sandbox"):
            raise HTTPException(status_code=401, detail="Invalid sandbox token")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sandbox session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid sandbox token")

async def get_sandbox_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get sandbox user from JWT token"""
    # Manually extract Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token_value = auth_header[7:]  # Remove "Bearer " prefix
    
    payload = verify_sandbox_jwt(token_value)
    user_id = payload.get("user_id")
    
    user = db.query(User).filter(
        User.user_id == user_id,
        User.is_anonymous == True
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Sandbox user not found")
    
    # Update last seen
    user.last_seen_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    
    return user

@router.post("/session", response_model=SandboxSessionResponse)
async def create_sandbox_session(db: Session = Depends(get_db)):
    """Create a new sandbox session for anonymous users"""
    try:
        # Create anonymous user
        user = create_sandbox_user(db)
        
        # Generate JWT token
        token = create_sandbox_jwt(user.user_id)
        
        return SandboxSessionResponse(
            session_token=token,
            expires_in=SANDBOX_SESSION_DURATION_HOURS * 3600,  # seconds
            user_id=user.user_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sandbox session: {str(e)}")

@router.post("/memories", response_model=SandboxMemoryResponse)
async def create_sandbox_memory(
    memory_request: SandboxMemoryRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new memory in the sandbox environment"""
    try:
        # Get user from token
        user = await get_sandbox_user(request, db)
        
        # Get user's sandbox app
        app = db.query(App).filter(
            App.owner_id == user.id,
            App.name == "sandbox_app"
        ).first()
        
        if not app:
            raise HTTPException(status_code=404, detail="Sandbox app not found")
        
        # Try to use vector database, but fallback to demo mode if unavailable
        try:
            memory_client = get_memory_client()
            response = memory_client.add(
                messages=memory_request.text,
                user_id=user.user_id,
                metadata={
                    "source_app": "sandbox",
                    "app_db_id": str(app.id),
                    "sandbox": True,
                    "ttl": (datetime.datetime.now(datetime.timezone.utc) + 
                           datetime.timedelta(hours=SANDBOX_SESSION_DURATION_HOURS)).isoformat()
                }
            )
        except Exception as e:
            # Vector database unavailable - use demo mode
            response = {
                "results": [{
                    "id": f"demo_{uuid.uuid4().hex[:16]}",
                    "memory": memory_request.text,
                    "event": "ADD",
                    "metadata": {"demo_mode": True}
                }]
            }
        
        # Process response and create SQL record
        if isinstance(response, dict) and 'results' in response:
            for result in response['results']:
                if result.get('event') == 'ADD':
                    mem0_memory_id = result['id']
                    memory_content = result.get('memory', memory_request.text)
                    
                    # Create SQL memory record with TTL
                    sql_memory = Memory(
                        user_id=user.id,
                        app_id=app.id,
                        content=memory_content,
                        state=MemoryState.active,
                        metadata_={
                            **result.get('metadata', {}),
                            "mem0_id": mem0_memory_id,
                            "sandbox": True,
                            "ttl": (datetime.datetime.now(datetime.timezone.utc) + 
                                   datetime.timedelta(hours=SANDBOX_SESSION_DURATION_HOURS)).isoformat()
                        }
                    )
                    
                    db.add(sql_memory)
                    db.commit()
                    
                    return SandboxMemoryResponse(
                        id=str(sql_memory.id),
                        content=memory_content,
                        created_at=sql_memory.created_at.isoformat(),
                        success=True,
                        message="Memory successfully added to sandbox"
                    )
        
        # If no ADD event, still return success
        return SandboxMemoryResponse(
            id="",
            content=memory_request.text,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            success=True,
            message="Memory processed (may have been updated or deduplicated)"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create memory: {str(e)}")

@router.get("/memories")
async def get_sandbox_memories(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all memories for the sandbox user"""
    try:
        # Get user from token
        user = await get_sandbox_user(request, db)
        # Get memories from database
        memories = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.state == MemoryState.active
        ).order_by(Memory.created_at.desc()).limit(50).all()
        
        memory_list = []
        for memory in memories:
            memory_list.append({
                "id": str(memory.id),
                "content": memory.content,
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
                "metadata": memory.metadata_
            })
        
        return {
            "memories": memory_list,
            "total": len(memory_list),
            "user_id": user.user_id,
            "sandbox": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get memories: {str(e)}")

@router.get("/search")
async def search_sandbox_memories(
    query: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Search memories in the sandbox using vector similarity"""
    try:
        # Get user from token
        user = await get_sandbox_user(request, db)
        
        # Try vector search, fallback to SQL search for demo
        try:
            memory_client = get_memory_client()
            search_results = memory_client.search(
                query=query,
                user_id=user.user_id,
                limit=10
            )
        except Exception as e:
            # Vector database unavailable - search SQL records
            memories = db.query(Memory).filter(
                Memory.user_id == user.id,
                Memory.state == MemoryState.active,
                Memory.content.ilike(f"%{query}%")
            ).limit(10).all()
            
            search_results = {
                "results": [
                    {"memory": mem.content, "id": str(mem.id)}
                    for mem in memories
                ]
            }
        
        # Process results
        results = []
        if isinstance(search_results, dict) and 'results' in search_results:
            results = search_results['results']
        elif isinstance(search_results, list):
            results = search_results
        
        return {
            "query": query,
            "results": results,
            "user_id": user.user_id,
            "sandbox": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}") 