import datetime
import logging
# Python 3.10 compatibility for datetime.UTC
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from typing import List, Optional, Set, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from sqlalchemy import or_, func

from app.database import get_db
from app.auth import get_current_supa_user
from gotrue.types import User as SupabaseUser
# Memory clients are imported in individual functions where needed
from app.utils.db import get_or_create_user, get_user_and_app
from app.models import (
    Memory, MemoryState, MemoryAccessLog, App,
    MemoryStatusHistory, User, Category, AccessControl, UserNarrative, Document
)
from app.schemas import MemoryResponse, PaginatedMemoryResponse
from app.utils.permissions import check_memory_access_permissions
from .memories_modules.utils import (
    get_memory_or_404, update_memory_state, get_accessible_memory_ids,
    group_memories_into_threads
)
from .memories_modules.schemas import (
    CreateMemoryRequestData, DeleteMemoriesRequestData, PauseMemoriesRequestData,
    UpdateMemoryRequestData, FilterMemoriesRequestData
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memories", tags=["memories"])

class JeanMemoryRequest(BaseModel):
    user_message: str
    is_new_conversation: bool = False

@router.post("/context", response_model=str)
async def get_jean_memory_context(
    request: JeanMemoryRequest,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
):
    """
    Get orchestrated context from Jean Memory.
    This is the primary endpoint for all conversational interactions.
    """
    from app.tools.orchestration import jean_memory
    from app.context import user_id_var, client_name_var
    
    supa_uid = str(current_supa_user.id)
    # For API calls, client_name can be a default or passed in headers later
    client_name = "api_client"

    # Set context variables for the tool call
    user_id_var.set(supa_uid)
    client_name_var.set(client_name)
    
    return await jean_memory(
        user_message=request.user_message,
        is_new_conversation=request.is_new_conversation
    )


# List all memories with filtering (no pagination)
@router.get("/", response_model=List[MemoryResponse])
async def list_memories(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    app_id: Optional[UUID] = None,
    from_date: Optional[int] = Query(
        None,
        description="Filter memories created after this date (timestamp)",
        examples=[1718505600]
    ),
    to_date: Optional[int] = Query(
        None,
        description="Filter memories created before this date (timestamp)",
        examples=[1718505600]
    ),
    categories: Optional[str] = None,
    search_query: Optional[str] = None,
    sort_column: Optional[str] = Query(None, description="Column to sort by (memory, categories, app_name, created_at)"),
    sort_direction: Optional[str] = Query(None, description="Sort direction (asc or desc)"),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found or could not be created")

    # Build base query for SQL memories
    query = db.query(Memory).filter(
        Memory.user_id == user.id,
        Memory.state != MemoryState.deleted,
        Memory.state != MemoryState.archived,
        Memory.content.ilike(f"%{search_query}%") if search_query else True
    )

    # Apply filters
    if app_id:
        query = query.filter(Memory.app_id == app_id)

    if from_date:
        from_datetime = datetime.datetime.fromtimestamp(from_date, tz=UTC)
        query = query.filter(Memory.created_at >= from_datetime)

    if to_date:
        to_datetime = datetime.datetime.fromtimestamp(to_date, tz=UTC)
        query = query.filter(Memory.created_at <= to_datetime)

    # Add joins for app and categories after filtering
    query = query.outerjoin(App, Memory.app_id == App.id)
    query = query.outerjoin(Memory.categories)

    # Apply category filter if provided
    if categories:
        category_list = [c.strip() for c in categories.split(",")]
        query = query.filter(Category.name.in_(category_list))
    
    # Apply sorting if specified
    if sort_column:
        sort_field = None
        if sort_column == "memory": sort_field = Memory.content
        elif sort_column == "categories": sort_field = Category.name
        elif sort_column == "app_name": sort_field = App.name
        elif sort_column == "created_at": sort_field = Memory.created_at
        
        if sort_field is not None:
            if sort_column == "categories" and not categories:
                query = query.join(Memory.categories)
            if sort_column == "app_name" and not app_id:
                query = query.outerjoin(App, Memory.app_id == App.id)
                
            if sort_direction == "desc":
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(Memory.created_at.desc())
    else:
        query = query.order_by(Memory.created_at.desc())

    # Get ALL SQL memories (no pagination)
    sql_memories = query.options(joinedload(Memory.app), joinedload(Memory.categories)).all()
    
    # Filter SQL results based on permissions
    permitted_sql_memories = []
    for item in sql_memories:
        if check_memory_access_permissions(db, item, app_id):
            permitted_sql_memories.append(item)

    # Transform SQL memories to response format
    sql_response_items = [
        MemoryResponse(
            id=mem.id,
            content=mem.content,
            created_at=mem.created_at, 
            state=mem.state.value if mem.state else None,
            app_id=mem.app_id,
            app_name=mem.app.name if mem.app else "Unknown App", 
            categories=[cat.name for cat in mem.categories], 
            metadata_=mem.metadata_
        )
        for mem in permitted_sql_memories
    ]
    
    # REMOVED: Jean Memory V2 API call - using SQL database as single source of truth
    # The SQL database already contains all memories with proper app_id references
    jean_response_items = []

    # Use SQL results only
    all_response_items = sql_response_items
    
    # Sort combined results by created_at desc (most recent first)
    all_response_items.sort(key=lambda x: x.created_at, reverse=True)
    
    logger.info(f"✅ Retrieved {len(sql_response_items)} memories from database")
    logger.info(f"📊 Total memories: {len(all_response_items)}")

    # REMOVED: Threading not needed when using single data source
    # All memories come from SQL database with proper app_id references

    return all_response_items


# Get all categories
@router.get("/categories")
async def get_categories(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    memories = db.query(Memory).filter(Memory.user_id == user.id, Memory.state != MemoryState.deleted, Memory.state != MemoryState.archived).all()
    categories_set = set()
    for memory_item in memories:
        for category_item in memory_item.categories:
            categories_set.add(category_item.name)
    
    return {
        "categories": list(categories_set),
        "total": len(categories_set)
    }


# Get or generate user narrative using Jean Memory V2.
@router.get("/narrative")
async def get_user_narrative(
    force_regenerate: bool = False,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """
    Get or generate user narrative using Jean Memory V2.
    Returns cached narrative if fresh, otherwise generates new one using Jean Memory V2.
    """
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    logger.info(f"🔄 NARRATIVE REQUEST: user={supabase_user_id_str}, force_regenerate={force_regenerate}")

    # Check for existing cached narrative (only if not forcing regeneration)
    narrative = db.query(UserNarrative).filter(UserNarrative.user_id == user.id).first()
    
    # Only use cache if not forcing regeneration and narrative is fresh
    if not force_regenerate and narrative:
        now = datetime.datetime.now(narrative.generated_at.tzinfo or UTC)
        age_days = (now - narrative.generated_at).days
        
        if age_days <= 7:  # Narrative is still fresh
            logger.info(f"📋 RETURNING CACHED NARRATIVE: age={age_days} days, version={narrative.version}")
            return {
                "narrative": narrative.narrative_content,
                "generated_at": narrative.generated_at,
                "version": narrative.version,
                "age_days": age_days,
                "source": "cached"
            }
    
    # Generate new narrative using Jean Memory V2
    try:
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
        
        # Get user's full name for personalized narrative (only if both names exist)
        user_full_name = ""
        if user.firstname and user.lastname:
            user_full_name = f"{user.firstname.strip()} {user.lastname.strip()}".strip()
        elif user.firstname:
            user_full_name = user.firstname.strip()
        elif user.lastname:
            user_full_name = user.lastname.strip()
        
        # Get recent memories from Jean Memory V2 focused on life alignment
        logger.info(f"🔍 NARRATIVE DEBUG: Starting memory search for user {supabase_user_id_str}")
        
        memory_results = await memory_client.search(
            query="recent experiences recent memories current projects goals values personality growth life patterns recent reflections recent decisions recent insights recent challenges recent achievements how experiences align with values core beliefs life direction personal development recent learning recent relationships recent work recent thoughts",
            user_id=supabase_user_id_str,
            limit=100
        )
        
        logger.info(f"🔍 NARRATIVE DEBUG: Raw search results type: {type(memory_results)}")
        logger.info(f"🔍 NARRATIVE DEBUG: Raw search results: {memory_results}")
        
        # Process memory results with PROPER FILTERING
        memories_text = []
        if isinstance(memory_results, dict) and 'results' in memory_results:
            memories = memory_results['results']
            logger.info(f"🔍 NARRATIVE DEBUG: Extracted {len(memories)} memories from dict results")
        elif isinstance(memory_results, list):
            memories = memory_results
            logger.info(f"🔍 NARRATIVE DEBUG: Using list of {len(memories)} memories directly")
        else:
            memories = []
            logger.warning(f"🔍 NARRATIVE DEBUG: No memories found - unexpected result type")
        
        # Filter for narrative generation (less aggressive - include all meaningful content)
        for mem in memories[:50]:  # Limit for narrative generation
            content = mem.get('memory', mem.get('content', ''))
            
            if not content or not isinstance(content, str):
                continue
            
            content = content.strip()
            
            # Skip empty content
            if not content.strip():
                continue
            
            # Skip very short content 
            if len(content) < 5:
                logger.info(f"🚫 Narrative: Skipping too short: '{content}'")
                continue
            
            # Include ALL other content (both user memories and graph insights)
            memories_text.append(content)
            logger.info(f"✅ Narrative: Added content: '{content[:50]}...'")
        
        logger.info(f"📊 Narrative: Found {len(memories_text)} pieces of content for narrative generation")
        
        if not memories_text:
            # Return a helpful message instead of raising an error
            return {
                "narrative": "You have no memories! Please add some to see your Life Narrative.",
                "generated_at": datetime.datetime.now(UTC),
                "version": "empty",
                "age_days": 0,
                "source": "generated",
                "memory_count": 0
            }
        
        # Fetch user documents
        documents = db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).limit(20).all()
        documents_text = ""
        if documents:
            logger.info(f"📚 Found {len(documents)} documents for narrative generation.")
            documents_text = "\n\n".join([f"--- Document: {doc.title} ---\n{doc.content}" for doc in documents])
        
        if not memories_text and not documents:
            # Return a helpful message instead of raising an error
            return {
                "narrative": "You have no memories or documents! Please add some to see your Life Narrative.",
                "generated_at": datetime.datetime.now(UTC),
                "version": "empty",
                "age_days": 0,
                "source": "generated",
                "memory_count": 0
            }
        
        # Generate narrative using Gemini (same as MCP orchestration)
        from app.utils.gemini import GeminiService
        
        gemini = GeminiService()
        combined_memories = "\n".join(memories_text)
        
        # Create a new combined context with documents
        combined_context = f"=== USER'S MEMORIES ===\n{combined_memories}"
        if documents_text:
            combined_context += f"\n\n=== USER'S DOCUMENTS ===\n{documents_text}"

        logger.info(f"🧠 NARRATIVE DEBUG: Sending {len(combined_context)} characters to Gemini Pro for user {user_full_name}")
        logger.info(f"🧠 NARRATIVE DEBUG: Combined context preview: '{combined_context[:200]}...'")
        
        narrative_content = await gemini.generate_narrative_pro(combined_context, user_full_name)
        
        logger.info(f"🧠 NARRATIVE DEBUG: Generated narrative length: {len(narrative_content)} characters")
        logger.info(f"🧠 NARRATIVE DEBUG: Narrative preview: '{narrative_content[:200]}...'")
        
        
        # Cache the new narrative
        if narrative:
            # Update existing
            narrative.narrative_content = narrative_content
            narrative.generated_at = datetime.datetime.now(UTC)
            narrative.version += 1
        else:
            # Create new
            narrative = UserNarrative(
                user_id=user.id,
                narrative_content=narrative_content,
                generated_at=datetime.datetime.now(UTC),
                version=1
            )
            db.add(narrative)
        
        db.commit()
        db.refresh(narrative)
        
        logger.info(f"✅ Generated new narrative for user {supabase_user_id_str} using Jean Memory V2 (force_regenerate={force_regenerate})")
        
        return {
            "narrative": narrative.narrative_content,
            "generated_at": narrative.generated_at,
            "version": narrative.version,
            "age_days": 0,
            "source": "jean_memory_v2_generated",
            "memory_count": len(memories_text),
            "user_full_name": user_full_name,
            "force_regenerate": force_regenerate
        }
        
    except Exception as e:
        logger.error(f"Failed to generate narrative using Jean Memory V2: {e}")
        
        # Handle specific "Insufficient memories" error gracefully
        if "Insufficient memories" in str(e) or "204" in str(e):
            memory_count = len(memories_text) if 'memories_text' in locals() else 0
            if memory_count > 0:
                return {
                    "narrative": f"You have {memory_count} memories, but need more for a comprehensive Life Narrative. Keep adding memories to unlock richer insights!",
                    "generated_at": datetime.datetime.now(UTC),
                    "version": "insufficient",
                    "age_days": 0,
                    "source": "generated",
                    "memory_count": memory_count
                }
            else:
                return {
                    "narrative": "You have no memories! Please add some to see your Life Narrative.",
                    "generated_at": datetime.datetime.now(UTC),
                    "version": "empty",
                    "age_days": 0,
                    "source": "generated",
                    "memory_count": 0
                }
        
        # Fallback to cached narrative if available
        if narrative:
            return {
                "narrative": narrative.narrative_content,
                "generated_at": narrative.generated_at,
                "version": narrative.version,
                "age_days": (datetime.datetime.now(UTC) - narrative.generated_at).days,
                "source": "cached_fallback",
                "error": str(e)
            }
        else:
            # Final fallback for any other errors
            return {
                "narrative": "Unable to generate your Life Narrative right now. Please try again later or add more memories.",
                "generated_at": datetime.datetime.now(UTC),
                "version": "error",
                "age_days": 0,
                "source": "error_fallback",
                "error": str(e)
            }




# Create new memory
@router.post("/", response_model=MemoryResponse)
async def create_memory(
    request: CreateMemoryRequestData,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    
    user, app_obj = get_user_and_app(db, supabase_user_id_str, request.app_name, current_supa_user.email)

    if not app_obj.is_active:
        raise HTTPException(status_code=403, detail=f"App {request.app_name} is currently paused. Cannot create new memories.")

    # 1. First save to Jean Memory V2 to get mem0_id
    mem0_id = None
    try:
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
        
        # Prepare metadata for Jean Memory V2 (without sql_memory_id since we don't have it yet)
        jean_metadata = {
            'app_name': request.app_name,
            'app_id': str(app_obj.id),
            'created_via': 'rest_api'
        }
        if request.metadata:
            jean_metadata.update(request.metadata)
        
        # Add to Jean Memory V2 (async) - Concise logging
        content_preview = request.text[:100] + ("..." if len(request.text) > 100 else "")
        logger.info(f"📝 Adding to Jean Memory V2 first - User: {supabase_user_id_str}, Content: '{content_preview}'")
        
        # Format message the same way as MCP tools
        message_to_add = {
            "role": "user", 
            "content": request.text
        }
        
        jean_result = await memory_client.add(
            messages=[message_to_add],
            user_id=supabase_user_id_str,
            metadata=jean_metadata
        )
        
        # Extract mem0_id from Jean Memory V2 response
        if isinstance(jean_result, dict) and 'results' in jean_result:
            if jean_result['results'] and len(jean_result['results']) > 0:
                first_result = jean_result['results'][0]
                mem0_id = first_result.get('id')
                logger.info(f"✅ Jean Memory V2 stored successfully, got mem0_id: {mem0_id}")
            else:
                logger.warning(f"⚠️ Jean Memory V2: No results in response")
        else:
            logger.warning(f"⚠️ Jean Memory V2: Unexpected response format")
        
    except Exception as e:
        logger.error(f"⚠️ Jean Memory V2 storage failed: {str(e)[:200]}...")
        # Continue with SQL storage even if Jean Memory V2 fails
    
    # 2. Create SQL memory with correct metadata from the start
    sql_metadata = {}
    if mem0_id:
        sql_metadata['mem0_id'] = mem0_id
        logger.info(f"🔍 Creating SQL memory with mem0_id: {mem0_id}")
    else:
        logger.warning(f"⚠️ Creating SQL memory without mem0_id")
    
    # Merge with any additional metadata from request
    if request.metadata:
        sql_metadata.update(request.metadata)
    
    sql_memory = Memory(
        user_id=user.id,
        app_id=app_obj.id,
        content=request.text,
        metadata_=sql_metadata
    )
    db.add(sql_memory)
    try:
        db.commit()
        db.refresh(sql_memory)
        logger.info(f"✅ SQL memory created with metadata: {sql_memory.metadata_}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return MemoryResponse(
        id=sql_memory.id,
        content=sql_memory.content,
        created_at=sql_memory.created_at,
        state=sql_memory.state.value if sql_memory.state else None,
        app_id=sql_memory.app_id,
        app_name=app_obj.name,
        categories=[cat.name for cat in sql_memory.categories],
        metadata_=sql_memory.metadata_
    )


# IMPORTANT: Specific routes must come before general routes
# Life Graph Data endpoint - must be before /{memory_id}
@router.get("/life-graph-data")
async def get_life_graph_data(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    limit: int = Query(25, description="Maximum number of core memories to analyze initially"),
    focus_query: Optional[str] = Query(None, description="Optional query to focus the graph on specific topics"),
    progressive: bool = Query(True, description="Use progressive loading for better performance"),
    db: Session = Depends(get_db)
):
    """
    Get optimized life graph data for visualization.
    This endpoint provides pre-computed entities and relationships for fast visualization.
    """
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    try:
        logger.info(f"🚀 Generating life graph data for user {supabase_user_id_str}")
        
        # Base query for user's memories
        query = db.query(Memory).filter(Memory.user_id == user.id, Memory.state == MemoryState.active)

        # Apply focus query if provided
        if focus_query:
            query = query.filter(Memory.content.ilike(f"%{focus_query}%"))
            
        memories = query.order_by(Memory.created_at.desc()).limit(limit).all()
        
        logger.info(f"📊 Retrieved {len(memories)} memories from database")
        
        nodes = []
        edges = []
        entities = {}
        entity_memory_map = {}

        for mem in memories:
            nodes.append({
                'id': str(mem.id),
                'title': mem.content[:80] + '...' if len(mem.content) > 80 else mem.content,
                'content': mem.content,
                'type': 'memory',
                'created_at': mem.created_at.isoformat(),
                'source': mem.app.name if mem.app else 'Jean Memory'
            })
            
            if mem.entities and 'entities' in mem.entities:
                for fact in mem.entities['entities']:
                    parts = fact.split(': ', 1)
                    if len(parts) != 2: continue
                    
                    entity_type, entity_info = parts
                    entity_type = entity_type.strip().lower()

                    if ' - ' in entity_info:
                        entity_name = entity_info.split(' - ')[0].strip()
                    else:
                        entity_name = entity_info.strip()

                    if entity_name and len(entity_name) > 1 and entity_type in ['person', 'place', 'event', 'topic', 'object', 'emotion']:
                        entity_id = f"{entity_type}_{entity_name.lower().replace(' ', '_')}"
                        
                        if entity_id not in entities:
                            entities[entity_id] = {'id': entity_id, 'name': entity_name, 'type': entity_type, 'mentions': 0}
                        
                        entities[entity_id]['mentions'] += 1
                        entity_memory_map.setdefault(entity_id, []).append(str(mem.id))

        # Add entity nodes
        for entity_id, entity in entities.items():
            nodes.append({
                'id': entity_id,
                'title': entity['name'],
                'content': f"{entity['type'].title()}: {entity['name']} (mentioned {entity['mentions']} times)",
                'type': entity['type'],
                'mentions': entity['mentions']
            })

        # Create memory-to-entity edges
        edge_id = 0
        for entity_id, memory_ids in entity_memory_map.items():
            for memory_id in memory_ids:
                edges.append({'id': f"edge_{edge_id}", 'source': memory_id, 'target': entity_id, 'type': 'mentions'})
                edge_id += 1
        
        visualization_data = {
            'nodes': nodes,
            'edges': edges,
            'clusters': [],
            'metadata': {
                'total_memories': len(memories),
                'total_entities': len(entities),
                'focus_query': focus_query
            }
        }
        
        logger.info(f"✅ Life graph data generated successfully: {len(nodes)} nodes, {len(edges)} edges")
        
        return visualization_data
        
    except Exception as e:
        logger.error(f"Life Graph Data failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Life graph data generation failed: {str(e)}"
        )


# ITERATIVE EXPLORER ENDPOINTS FOR /MY-LIFE PAGE

@router.post("/life-graph-expand")
async def expand_graph_node(
    request_data: dict,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """
    Expand a specific node in the life graph using focused search.
    This endpoint enables iterative exploration by performing targeted searches
    around a specific node or topic.
    """
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    # Extract parameters
    focal_node_id = request_data.get('focal_node_id')
    query = request_data.get('query', '')
    depth = request_data.get('depth', 1)
    strategy = request_data.get('strategy', 'NODE_HYBRID_SEARCH_NODE_DISTANCE')
    limit = request_data.get('limit', 20)
    
    logger.info(f"🔍 Graph expansion: node={focal_node_id}, query='{query}', strategy={strategy}")
    
    try:
        # Use the working memory client (same as life-graph-data)
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
        
        # Create focused search query
        if not query.strip():
            query = "related memories connected topics similar experiences"
        
        # Add context for focused search
        focused_query = f"{query} related to {focal_node_id}" if focal_node_id else query
        
        # Search for related memories
        memory_results = await memory_client.search(
            query=focused_query,
            user_id=supabase_user_id_str,
            limit=limit
        )
        
        # Process results into graph structure (same pattern as life-graph-data)
        nodes = []
        edges = []
        clusters = []
        
        # Extract memories from results (same as working life-graph-data endpoint)
        memories = []
        if isinstance(memory_results, dict) and 'results' in memory_results:
            memories = memory_results['results']
        elif isinstance(memory_results, list):
            memories = memory_results
        
        logger.info(f"📊 Retrieved {len(memories)} memories for expansion")
        
        # Process memories for expansion
        for i, memory in enumerate(memories):
            content = memory.get('memory', memory.get('content', ''))
            memory_id = memory.get('id', f"expanded_{i}")
            score = memory.get('score', 0.5)
            
            # Skip empty memories
            if not content or len(content.strip()) < 5:
                continue
            
            node = {
                'id': memory_id,
                'content': content.strip(),
                'type': 'memory',
                'score': score,
                'source': 'expansion',
                'parent_node': focal_node_id,
                'metadata': memory.get('metadata', {})
            }
            nodes.append(node)
            
            # Create edge to parent node if specified
            if focal_node_id:
                edges.append({
                    'source': focal_node_id,
                    'target': memory_id,
                    'type': 'expansion',
                    'weight': score
                })
        
        # If no valid memories found, create a fallback node
        if len(nodes) == 0:
            nodes.append({
                'id': f"no_results_{focal_node_id}",
                'content': "No memories found for this topic. Try exploring a different area or add more memories to your collection.",
                'type': 'message',
                'score': 0.0,
                'source': 'fallback',
                'parent_node': focal_node_id,
                'metadata': {}
            })
        
        expansion_data = {
            'nodes': nodes,
            'edges': edges,
            'clusters': clusters,
            'metadata': {
                'focal_node_id': focal_node_id,
                'query': query,
                'strategy': strategy,
                'depth': depth,
                'total_results': len(nodes),
                'expansion_type': 'focused_search'
            }
        }
        
        logger.info(f"✅ Graph expansion complete: {len(nodes)} new nodes, {len(edges)} edges")
        
        return expansion_data
        
    except Exception as e:
        logger.error(f"Graph expansion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Graph expansion failed: {str(e)}"
        )


@router.post("/life-graph-suggest")
async def suggest_next_exploration(
    request_data: dict,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered suggestions for next exploration areas in the life graph.
    Uses Gemini AI to analyze current exploration path and suggest relevant areas.
    """
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    # Extract parameters
    current_path = request_data.get('current_path', [])
    current_node = request_data.get('current_node', '')
    context = request_data.get('context', '')
    
    logger.info(f"🤖 Generating exploration suggestions for path: {current_path}")
    
    try:
        # Use Gemini for intelligent suggestions
        from app.utils.gemini import GeminiService
        gemini_service = GeminiService()
        
        # Create context prompt
        path_context = " → ".join(current_path) if current_path else "Life Overview"
        
        prompt = f"""Based on the current exploration path: {path_context}
Current focus: {current_node}
Additional context: {context}

Suggest 3-5 meaningful areas for further exploration in this person's life graph. 
Focus on:
1. Related people, places, or topics that would naturally connect
2. Different time periods that might show growth or change
3. Contrasting or complementary experiences
4. Goals, outcomes, or lessons learned

Return suggestions as a JSON array with this format:
[
  {{
    "title": "Short descriptive title",
    "description": "Brief explanation of why this would be interesting",
    "query": "Search query to use for this exploration",
    "type": "people|places|topics|temporal|outcomes"
  }}
]

Keep suggestions concise and actionable."""

        response_text = await gemini_service.generate_response(prompt)
        response_text = response_text.strip()
        
        # Try to parse JSON response
        import json
        try:
            suggestions = json.loads(response_text)
        except json.JSONDecodeError:
            # Fallback to structured suggestions if JSON parsing fails
            suggestions = [
                {
                    "title": "Related People",
                    "description": "Explore connections with people mentioned in this context",
                    "query": f"people relationships connected to {current_node}",
                    "type": "people"
                },
                {
                    "title": "Similar Experiences",
                    "description": "Find related experiences from different time periods",
                    "query": f"similar experiences like {current_node}",
                    "type": "temporal"
                },
                {
                    "title": "Outcomes & Growth",
                    "description": "Discover results and lessons from these experiences",
                    "query": f"outcomes results growth from {current_node}",
                    "type": "outcomes"
                }
            ]
        
        suggestion_data = {
            'suggestions': suggestions,
            'metadata': {
                'current_path': current_path,
                'current_node': current_node,
                'generated_by': 'gemini_ai',
                'context_used': bool(context)
            }
        }
        
        logger.info(f"✅ Generated {len(suggestions)} exploration suggestions")
        
        return suggestion_data
        
    except Exception as e:
        logger.error(f"Suggestion generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion generation failed: {str(e)}"
        )


@router.get("/life-graph-clusters")
async def get_life_graph_clusters(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    level: int = Query(1, description="Cluster level (1=topics, 2=subtopics, 3=memories)"),
    limit: int = Query(30, description="Maximum number of clusters to return"),
    db: Session = Depends(get_db)
):
    """
    Get hierarchical topic clusters for the life graph overview.
    This provides the initial high-level view for iterative exploration.
    """
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    logger.info(f"📊 Getting life graph clusters (level {level}) for user {supabase_user_id_str}")
    
    try:
        # Use the working memory client
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
        
        # Define cluster queries based on level
        if level == 1:
            # High-level life areas
            cluster_queries = [
                "personal relationships family friends",
                "work career professional development",
                "learning education skills knowledge",
                "hobbies interests creative activities", 
                "health fitness wellness lifestyle",
                "travel places locations experiences",
                "goals aspirations future plans",
                "achievements accomplishments milestones"
            ]
        elif level == 2:
            # More specific sub-topics
            cluster_queries = [
                "daily routines habits patterns",
                "challenges problems difficulties",
                "celebrations successes victories",
                "projects work initiatives",
                "conversations discussions meetings",
                "decisions choices important moments",
                "tools technology apps usage",
                "finances money business"
            ]
        else:
            # Memory-level clusters
            cluster_queries = [
                "recent memories current events",
                "significant moments important experiences",
                "repeated themes patterns behaviors",
                "emotional memories feelings experiences"
            ]
        
        clusters = []
        
        # Search for each cluster type
        for i, query in enumerate(cluster_queries):
            try:
                results = await memory_client.search(
                    query=query,
                    user_id=supabase_user_id_str,
                    limit=min(limit // len(cluster_queries) + 3, 10)
                )
                
                memory_count = len(results) if hasattr(results, '__len__') else 0
                
                if memory_count > 0:
                    # Extract cluster title from query
                    cluster_title = " ".join(query.split()[:2]).title()
                    
                    cluster = {
                        'id': f"cluster_{level}_{i}",
                        'title': cluster_title,
                        'query': query,
                        'level': level,
                        'memory_count': memory_count,
                        'type': 'topic_cluster',
                        'can_expand': True,
                        'description': f"Explore {memory_count} memories about {cluster_title.lower()}"
                    }
                    clusters.append(cluster)
                    
            except Exception as e:
                logger.warning(f"Cluster search failed for '{query}': {e}")
                continue
        
        cluster_data = {
            'clusters': clusters,
            'metadata': {
                'level': level,
                'total_clusters': len(clusters),
                'generated_at': datetime.datetime.now(UTC).isoformat(),
                'user_id': supabase_user_id_str
            }
        }
        
        logger.info(f"✅ Generated {len(clusters)} clusters for level {level}")
        
        return cluster_data
        
    except Exception as e:
        logger.error(f"Cluster generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Cluster generation failed: {str(e)}"
        )


# Get memory by ID
@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: UUID,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)

    # First, try to get from SQL database (main memories)
    sql_memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user.id).first()
    
    if sql_memory:
        # Found in SQL database - return it
        return MemoryResponse(
            id=sql_memory.id,
            content=sql_memory.content,
            created_at=sql_memory.created_at,
            state=sql_memory.state.value if sql_memory.state else None,
            app_id=sql_memory.app_id,
            app_name=sql_memory.app.name if sql_memory.app else "Unknown App",
            categories=[category.name for category in sql_memory.categories],
            metadata_=sql_memory.metadata_
        )
    
    # Not found in SQL, try Jean Memory V2 (submemories)
    try:
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
        
        # Search broadly in Jean Memory V2 since ID-based search might not work
        jean_results = await memory_client.search(
            query="memories",  # Broad search to get all memories
            user_id=supabase_user_id_str,
            limit=1000  # Large limit to ensure we get all memories
        )
        
        # Process Jean Memory V2 results to find matching ID
        jean_memories = []
        if isinstance(jean_results, dict) and 'results' in jean_results:
            jean_memories = jean_results['results']
        elif isinstance(jean_results, list):
            jean_memories = jean_results
        
        # Look for memory with matching ID
        for jean_mem in jean_memories:
            jean_memory_id = jean_mem.get('id')
            
            # Check if this is the memory we're looking for (try both string and UUID comparison)
            if (str(jean_memory_id) == str(memory_id) or 
                jean_memory_id == memory_id or
                (isinstance(jean_memory_id, str) and jean_memory_id.replace('-', '') == str(memory_id).replace('-', ''))):
                
                memory_content = jean_mem.get('memory', jean_mem.get('content', ''))
                metadata = jean_mem.get('metadata', {})
                created_at = jean_mem.get('created_at')
                
                # Skip if no content
                if not memory_content or not memory_content.strip():
                    continue
                
                # Parse created_at if it's a string
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = datetime.datetime.now(UTC)
                elif not created_at:
                    created_at = datetime.datetime.now(UTC)
                
                # Get app info from metadata
                app_name = metadata.get('app_name', 'Jean Memory V2')
                
                logger.info(f"✅ Found memory {memory_id} in Jean Memory V2: '{memory_content[:50]}...'")
                
                return MemoryResponse(
                    id=memory_id,
                    content=memory_content,
                    created_at=created_at,
                    state='active',  # Jean Memory V2 memories are active
                    app_id=JEAN_MEMORY_V2_APP_ID,  # Use dummy app ID
                    app_name=app_name,
                    categories=[],  # Submemories have empty categories
                    metadata_=metadata
                )
        
        logger.info(f"Memory {memory_id} not found in Jean Memory V2 either")
        
    except Exception as e:
        logger.warning(f"Failed to search Jean Memory V2 for memory {memory_id}: {e}")
    
    # Memory not found in either system
    raise HTTPException(status_code=404, detail="Memory not found or you do not have permission")




# Delete multiple memories
@router.delete("/", status_code=200)
async def delete_memories(
    request: DeleteMemoriesRequestData,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)

    deleted_count = 0
    not_found_count = 0
    jean_deleted_count = 0

    # Also prepare to delete from Jean Memory V2
    memory_client = None
    try:
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
    except Exception as e:
        logger.error(f"Failed to initialize Jean Memory V2 client for deletion: {e}")

    for memory_id_to_delete in request.memory_ids:
        try:
            # 1. Delete from SQL database (existing behavior)
            update_memory_state(db, memory_id_to_delete, MemoryState.deleted, user.id)
            deleted_count += 1
            
            # 2. Also try to delete from Jean Memory V2 (NEW: dual deletion)
            if memory_client:
                try:
                    jean_result = await memory_client.delete(
                        memory_id=str(memory_id_to_delete),
                        user_id=supabase_user_id_str
                    )
                    if jean_result and jean_result.get('message'):
                        jean_deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete memory {memory_id_to_delete} from Jean Memory V2: {e}")
                    # Don't fail the whole operation if Jean Memory V2 deletion fails
            
        except HTTPException as e:
            if e.status_code == 404:
                not_found_count += 1
            else:
                raise e # Re-raise other exceptions
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error committing deletions: {e}")

    # Enhanced response with dual system info
    message = f"Successfully deleted {deleted_count} memories from SQL database"
    if jean_deleted_count > 0:
        message += f" and {jean_deleted_count} from Jean Memory V2"
    if not_found_count > 0:
        message += f". Not found: {not_found_count}"
    
    logger.info(f"✅ Deleted {deleted_count} SQL + {jean_deleted_count} Jean Memory V2 memories")
    
    return {"message": message}


# Archive memories
@router.post("/actions/archive", status_code=200)
async def archive_memories(
    memory_ids: List[UUID],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    archived_count = 0
    not_found_count = 0

    for memory_id_to_archive in memory_ids:
        try:
            update_memory_state(db, memory_id_to_archive, MemoryState.archived, user.id)
            archived_count += 1
        except HTTPException as e:
            if e.status_code == 404:
                not_found_count += 1
            else:
                raise e
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error committing archival: {e}")
    
    return {"message": f"Successfully archived {archived_count} memories. Not found: {not_found_count}."}




# Pause access to memories
@router.post("/actions/pause", status_code=200)
async def pause_memories(
    request: PauseMemoriesRequestData,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)

    state_to_set = request.state or MemoryState.paused

    count = 0
    if request.global_pause_for_user:
        memories_to_update = db.query(Memory).filter(
            Memory.user_id == user.id,
        ).all()
        for memory_item in memories_to_update:
            update_memory_state(db, memory_item.id, state_to_set, user.id)
            count += 1
        message = f"Successfully set state for all {count} accessible memories for user."

    elif request.app_id:
        memories_to_update = db.query(Memory).filter(
            Memory.app_id == request.app_id,
            Memory.user_id == user.id,
        ).all()
        for memory_item in memories_to_update:
            update_memory_state(db, memory_item.id, state_to_set, user.id)
            count += 1
        message = f"Successfully set state for {count} memories for app {request.app_id}."
    
    elif request.memory_ids:
        for mem_id in request.memory_ids:
            memory_to_update = db.query(Memory).filter(Memory.id == mem_id, Memory.user_id == user.id).first()
            if memory_to_update:
                 update_memory_state(db, mem_id, state_to_set, user.id)
                 count += 1
        message = f"Successfully set state for {count} specified memories."

    elif request.category_ids:
        memories_to_update = db.query(Memory).join(Memory.categories).filter(
            Memory.user_id == user.id,
            Category.id.in_(request.category_ids),
            Memory.state != MemoryState.deleted,
        ).distinct().all()
        for memory_item in memories_to_update:
            update_memory_state(db, memory_item.id, state_to_set, user.id)
            count += 1
        message = f"Successfully set state for {count} memories in {len(request.category_ids)} categories."
    else:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid pause request parameters. Specify memories, app, categories, or global_pause_for_user.")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error committing state changes: {e}")
        
    return {"message": message}


# Get memory access logs
@router.get("/{memory_id}/access-log")
async def get_memory_access_log(
    memory_id: UUID,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)

    memory_owner_check = get_memory_or_404(db, memory_id, user.id)
    if memory_owner_check.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access logs for this memory")

    query = db.query(MemoryAccessLog).filter(MemoryAccessLog.memory_id == memory_id)
    total = query.count()
    logs = query.order_by(MemoryAccessLog.accessed_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    for log_item in logs:
        app = db.query(App).filter(App.id == log_item.app_id).first()
        log_item.app_name = app.name if app else None

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "logs": logs
    }




# Update a memory
@router.put("/{memory_id}", response_model=MemoryResponse)
async def update_memory(
    memory_id: UUID,
    request: UpdateMemoryRequestData,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    memory_to_update = get_memory_or_404(db, memory_id, user.id)

    if memory_to_update.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this memory")

    memory_to_update.content = request.memory_content
    try:
        db.commit()
        db.refresh(memory_to_update)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
        
    return MemoryResponse(
        id=memory_to_update.id,
        content=memory_to_update.content,
        created_at=memory_to_update.created_at,
        state=memory_to_update.state.value if memory_to_update.state else None,
        app_id=memory_to_update.app_id,
        app_name=memory_to_update.app.name if memory_to_update.app else "Unknown App",
        categories=[cat.name for cat in memory_to_update.categories],
        metadata_=memory_to_update.metadata_
    )




@router.post("/filter", response_model=List[MemoryResponse])
async def filter_memories(
    request: FilterMemoriesRequestData,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)

    query = db.query(Memory).filter(
        Memory.user_id == user.id,
        Memory.state != MemoryState.deleted,
    )

    if not request.show_archived:
        query = query.filter(Memory.state != MemoryState.archived)

    if request.search_query:
        query = query.filter(Memory.content.ilike(f"%{request.search_query}%"))

    if request.app_ids:
        query = query.filter(Memory.app_id.in_(request.app_ids))

    query = query.outerjoin(App, Memory.app_id == App.id)

    if request.category_ids:
        query = query.join(Memory.categories).filter(Category.id.in_(request.category_ids))
    else:
        query = query.outerjoin(Memory.categories)

    if request.from_date:
        from_datetime = datetime.fromtimestamp(request.from_date, tz=UTC)
        query = query.filter(Memory.created_at >= from_datetime)

    if request.to_date:
        to_datetime = datetime.fromtimestamp(request.to_date, tz=UTC)
        query = query.filter(Memory.created_at <= to_datetime)

    if request.sort_column and request.sort_direction:
        sort_direction = request.sort_direction.lower()
        if sort_direction not in ['asc', 'desc']:
            raise HTTPException(status_code=400, detail="Invalid sort direction")

        sort_mapping = {
            'memory': Memory.content,
            'app_name': App.name,
            'created_at': Memory.created_at,
        }
        
        if request.sort_column == 'categories':
            query = query.order_by(Memory.created_at.desc())
        elif request.sort_column in sort_mapping:
            sort_field = sort_mapping[request.sort_column]
            if sort_direction == 'desc':
                query = query.order_by(sort_field.desc())
            else:
                query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(Memory.created_at.desc())
    else:
        query = query.order_by(Memory.created_at.desc())

    query = query.options(
        joinedload(Memory.categories),
        joinedload(Memory.app)
    ).distinct(Memory.id)

    # Get ALL filtered memories (no pagination)
    memories = query.all()

    return [
        MemoryResponse(
            id=mem.id,
            content=mem.content,
            created_at=mem.created_at,
            state=mem.state.value if mem.state else None,
            app_id=mem.app_id,
            app_name=mem.app.name if mem.app else "Unknown App",
            categories=[cat.name for cat in mem.categories],
            metadata_=mem.metadata_
        )
        for mem in memories
    ]


@router.get("/{memory_id}/related", response_model=List[MemoryResponse])
async def get_related_memories(
    memory_id: UUID,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    source_memory = get_memory_or_404(db, memory_id, user.id)
    if source_memory.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access related memories for this item.")
        
    category_ids = [category.id for category in source_memory.categories]
    
    if not category_ids:
        return []
    
    # First, get memory IDs with their category counts
    subquery = db.query(
        Memory.id,
        func.count(Category.id).label('category_count')
    ).filter(
        Memory.user_id == user.id,
        Memory.id != memory_id,
        Memory.state != MemoryState.deleted
    ).join(Memory.categories).filter(
        Category.id.in_(category_ids)
    ).group_by(Memory.id).subquery()
    
    # Then join with full memory data and order properly
    query = db.query(Memory).join(
        subquery, Memory.id == subquery.c.id
    ).options(
        joinedload(Memory.categories),
        joinedload(Memory.app)
    ).order_by(
        subquery.c.category_count.desc(),
        Memory.created_at.desc()
    )
    
    # Get ALL related memories (no pagination)
    related_memories = query.all()

    return [
        MemoryResponse(
            id=item.id,
            content=item.content,
            created_at=item.created_at,
            state=item.state.value if item.state else None,
            app_id=item.app_id,
            app_name=item.app.name if item.app else "Unknown App",
            categories=[cat.name for cat in item.categories],
            metadata_=item.metadata_
        )
        for item in related_memories
    ]


@router.post("/deep-life-query")
async def enhanced_deep_life_query(
    request: dict,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """
    Performs a true deep life query using the full orchestration logic.
    """
    supabase_user_id_str = str(current_supa_user.id)
    query = request.get("query", "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        from app.mcp_orchestration import get_smart_orchestrator
        orchestrator = get_smart_orchestrator()
        
        # Use a default client_name for API-initiated deep queries
        client_name = "deep_life_query_client"

        logger.info(f"🧠 [DEEP LIFE QUERY] Initiating full deep analysis for user {supabase_user_id_str}: '{query}'")
        
        # Await the comprehensive analysis from the orchestrator
        analysis_result = await orchestrator._full_deep_analysis(
            search_query=query,
            user_id=supabase_user_id_str,
            client_name=client_name
        )
        
        logger.info(f"✅ [DEEP LIFE QUERY] Full deep analysis completed for user {supabase_user_id_str}")
        
        return {
            "response": analysis_result,
            "metadata": {
                "analysis_type": "full_deep_analysis",
                "timestamp": datetime.datetime.now(UTC).isoformat()
            },
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ [DEEP LIFE QUERY] Failed for user {supabase_user_id_str}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Deep life query failed: {str(e)}"
        )


# Old entity extraction and layout functions removed
# These are now handled by the specialized function in Jean Memory V2
# Life graph data endpoint has been moved to appear before /{memory_id} route



async def select_most_important_memories(memories: list, target_count: int) -> list:
    """
    Intelligently select the most important memories based on:
    1. Entity density (memories with more extractable entities)
    2. Content richness (longer, more detailed memories)
    3. Temporal distribution (spread across time periods)
    4. Source diversity (different apps/contexts)
    """
    if len(memories) <= target_count:
        return memories
    
    # Score each memory based on multiple factors
    scored_memories = []
    
    for memory in memories:
        content = memory.get('memory', memory.get('content', ''))
        metadata = memory.get('metadata', {})
        
        score = 0
        
        # Factor 1: Content richness (longer content = more potential connections)
        content_score = min(len(content) / 500, 2.0)  # Cap at 500 chars = 2.0 score
        score += content_score
        
        # Factor 2: Entity potential (count capitalized words as proxy for entities)
        import re
        entities = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', content)
        entity_score = min(len(set(entities)) / 5, 2.0)  # Cap at 5 unique entities = 2.0 score
        score += entity_score
        
        # Factor 3: Temporal diversity bonus (prefer memories from different time periods)
        # This will be handled in the final selection to ensure time spread
        
        # Factor 4: Source diversity (different apps are more interesting)
        source = metadata.get('app_name', '')
        if source and source.lower() not in ['unknown', '']:
            score += 0.5
        
        # Factor 5: Recency bonus (slight preference for newer memories)
        created_at = memory.get('created_at')
        if created_at:
            try:
                from datetime import datetime, timezone
                if isinstance(created_at, str):
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_time = created_at
                    
                days_old = (datetime.now(timezone.utc) - created_time).days
                recency_score = max(0, (365 - days_old) / 365)  # Linear decay over 1 year
                score += recency_score * 0.5  # Weight recency less than content
            except:
                pass
        
        scored_memories.append({
            'memory': memory,
            'score': score,
            'content_length': len(content),
            'entity_count': len(entities),
            'source': source
        })
    
    # Sort by score (highest first)
    scored_memories.sort(key=lambda x: x['score'], reverse=True)
    
    # Smart selection to ensure diversity
    selected = []
    used_sources = set()
    
    # First pass: Take highest scoring memories, ensuring source diversity
    for item in scored_memories:
        if len(selected) >= target_count:
            break
            
        source = item['source']
        
        # Always take high-scoring memories, but prefer source diversity
        if len(selected) < target_count // 2:  # First half: pure quality
            selected.append(item['memory'])
            used_sources.add(source)
        else:  # Second half: balance quality with diversity
            if source not in used_sources or len([s for s in used_sources if s == source]) < 3:
                selected.append(item['memory'])
                used_sources.add(source)
    
    # Fill remaining slots if needed with next highest scoring
    remaining_memories = [item['memory'] for item in scored_memories if item['memory'] not in selected]
    while len(selected) < target_count and remaining_memories:
        selected.append(remaining_memories.pop(0))
    
    return selected

# Progressive node expansion endpoint
@router.get("/life-graph-expand/{node_id}")
async def expand_graph_node(
    node_id: str,
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    limit: int = Query(20, description="Maximum number of related memories to return"),
    db: Session = Depends(get_db)
):
    """
    Expand a specific node to show related memories and entities.
    Returns additional nodes and edges connected to the specified node.
    """
    supabase_user_id_str = str(current_supa_user.id)
    
    try:
        # Get memory client
        from app.utils.memory import get_async_memory_client
        memory_client = await get_async_memory_client()
        
        # Search for memories related to this node
        # Use node content as search query to find similar memories
        search_query = f"related to {node_id} similar memories"
        
        memory_results = await memory_client.search(
            query=search_query,
            user_id=supabase_user_id_str,
            limit=limit
        )
        
        # Process results similar to main endpoint but focused on expansion
        memories = []
        if isinstance(memory_results, dict) and 'results' in memory_results:
            memories = memory_results['results']
        elif isinstance(memory_results, list):
            memories = memory_results
        
        # Create expansion nodes
        expansion_nodes = []
        expansion_edges = []
        
        for i, mem in enumerate(memories):
            content = mem.get('memory', mem.get('content', ''))
            if not content or len(content.strip()) < 5:
                continue
                
            expansion_node_id = f"exp_{node_id}_{i}"
            expansion_nodes.append({
                'id': expansion_node_id,
                'type': 'memory',
                'content': content.strip(),
                'source': mem.get('metadata', {}).get('app_name', 'Jean Memory V2'),
                'size': 0.8,  # Smaller than core nodes
                'is_expansion': True,
                'parent_node': node_id
            })
            
            # Create edge to parent node
            expansion_edges.append({
                'source': node_id,
                'target': expansion_node_id,
                'type': 'expansion',
                'strength': 0.7
            })
        
        return {
            "expansion_nodes": expansion_nodes,
            "expansion_edges": expansion_edges,
            "parent_node": node_id,
            "total_expansions": len(expansion_nodes)
        }
        
    except Exception as e:
        logger.error(f"❌ Error expanding node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to expand node: {str(e)}")

# Simple fallback endpoint for life graph data (SQL memories only)
@router.get("/life-graph-data-simple")
async def get_life_graph_data_simple(
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    limit: int = Query(50, description="Maximum number of memories to analyze"),
    focus_query: Optional[str] = Query(None, description="Optional query to focus the graph on specific topics"),
    db: Session = Depends(get_db)
):
    """
    Simple life graph data endpoint using only SQL memories.
    No Jean Memory V2, Redis, or complex dependencies - just basic processing.
    """
    supabase_user_id_str = str(current_supa_user.id)
    user = get_or_create_user(db, supabase_user_id_str, current_supa_user.email)
    
    try:
        # Get SQL memories using the same query as the main memories endpoint
        query = db.query(Memory).filter(
            Memory.user_id == user.id,
            Memory.state != MemoryState.deleted,
            Memory.state != MemoryState.archived
        )
        
        # Apply search filter if provided
        if focus_query:
            query = query.filter(Memory.content.ilike(f"%{focus_query}%"))
        
        # Add joins and limit
        query = query.outerjoin(App, Memory.app_id == App.id)
        query = query.order_by(Memory.created_at.desc()).limit(limit)
        
        # Get memories
        sql_memories = query.options(joinedload(Memory.app), joinedload(Memory.categories)).all()
        
        # Simple processing - just create memory nodes without complex entity extraction
        nodes = []
        for i, memory in enumerate(sql_memories):
            node = {
                'id': f"memory_{i}",
                'type': 'memory',
                'content': memory.content.strip(),
                'source': memory.app.name if memory.app else 'unknown',
                'timestamp': memory.created_at.isoformat(),
                'size': min(max(len(memory.content) / 100, 0.5), 2.0),
                'position': {
                    'x': (i % 10 - 5) * 3,  # Simple grid layout
                    'y': (i // 10 - 5) * 3,
                    'z': 0
                }
            }
            nodes.append(node)
        
        return {
            'nodes': nodes,
            'edges': [],  # Simple version doesn't include edges
            'clusters': [],
            'metadata': {
                'total_memories': len(sql_memories),
                'total_nodes': len(nodes),
                'total_edges': 0,
                'focus_query': focus_query,
                'generated_at': datetime.datetime.now(UTC).isoformat(),
                'simple_mode': True
            }
        }
        
    except Exception as e:
        logger.error(f"Simple Life Graph Data failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Simple life graph data generation failed: {str(e)}"
        )






