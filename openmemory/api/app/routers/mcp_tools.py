"""
Simple HTTP-based MCP tools that bypass the complex SSE implementation.
These endpoints can be called directly by Claude via HTTP.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.auth import get_current_supa_user
from gotrue.types import User as SupabaseUser
from app.utils.db import get_or_create_user, get_user_and_app
from app.models import User, Document, DocumentChunk
from app.utils.memory import get_memory_client, get_memory_client_for_user, should_use_unified_memory
from app.services.chunking_service import ChunkingService
from app.integrations.substack_service import SubstackService
from app.config.memory_limits import MEMORY_LIMITS
from app.utils.posthog_client import get_posthog_client
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp-tools"])

@router.post("/search_memory")
async def search_memory_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Search the user's memory for memories that match the query"""
    try:
        query = request.get("query", "")
        limit = request.get("limit", MEMORY_LIMITS.search_default)
        
        if not query:
            return {"error": "Query parameter is required"}
        
        # Enforce configured limits
        limit = min(max(1, limit), MEMORY_LIMITS.search_max)
        
        # Get user
        user = get_or_create_user(db, str(current_supa_user.id), current_supa_user.email)
        
        # Search memories with limit - use user-specific routing
        from app.utils.memory import get_memory_client_for_user
        memory_client = get_memory_client_for_user(str(current_supa_user.id))
        results = memory_client.search(query=query, user_id=str(current_supa_user.id), limit=limit)
        
        # Process results
        processed_results = []
        if isinstance(results, dict) and 'results' in results:
            processed_results = results['results'][:limit]  # Extra safety
        elif isinstance(results, list):
            processed_results = results[:limit]  # Extra safety
        
        # 📊 Track MCP search usage with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_search_memory',
                properties={
                    'user_email': current_supa_user.email,
                    'query_length': len(query),
                    'results_count': len(processed_results),
                    'limit_requested': limit,
                    'tool_type': 'external_mcp'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for search_memory: {e}")
        
        return {
            "status": "success",
            "results": processed_results,
            "count": len(processed_results),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error in search_memory_http: {e}")
        return {"error": f"Search failed: {str(e)}"}


@router.post("/list_memories")
async def list_memories_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """List all memories in the user's memory"""
    try:
        limit = request.get("limit", MEMORY_LIMITS.list_default)
        
        # Enforce configured limits
        limit = min(max(1, limit), MEMORY_LIMITS.list_max)
        
        # Get user
        user = get_or_create_user(db, str(current_supa_user.id), current_supa_user.email)
        
        # Get memories with limit - use user-specific routing
        from app.utils.memory import get_memory_client_for_user
        memory_client = get_memory_client_for_user(str(current_supa_user.id))
        results = memory_client.get_all(user_id=str(current_supa_user.id), limit=limit)
        
        # Process results
        processed_results = []
        if isinstance(results, dict) and 'results' in results:
            processed_results = results['results'][:limit]  # Extra safety
        elif isinstance(results, list):
            processed_results = results[:limit]  # Extra safety
        
        # 📊 Track MCP list usage with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_list_memories',
                properties={
                    'user_email': current_supa_user.email,
                    'memories_count': len(processed_results),
                    'limit_requested': limit,
                    'tool_type': 'external_mcp'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for list_memories: {e}")
        
        return {
            "status": "success",
            "results": processed_results,
            "count": len(processed_results),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error in list_memories_http: {e}")
        return {"error": f"List memories failed: {str(e)}"}


@router.post("/add_memories")
async def add_memories_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Add new memories to the user's memory"""
    try:
        text = request.get("text", "")
        if not text:
            return {"error": "Text parameter is required"}
        
        # Get user and app
        user, app = get_user_and_app(db, str(current_supa_user.id), "claude", current_supa_user.email)
        
        if not app.is_active:
            return {"error": f"App {app.name} is currently paused. Cannot create new memories."}
        
        # Add memory - use user-specific routing
        memory_client = get_memory_client_for_user(str(current_supa_user.id))
        response = memory_client.add(
            messages=text,
            user_id=str(current_supa_user.id),
            metadata={
                "source_app": "openmemory_http",
                "mcp_client": "claude",
                "app_db_id": str(app.id)
            }
        )
        
        # 📊 Track MCP memory creation with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_add_memory',
                properties={
                    'user_email': current_supa_user.email,
                    'memory_length': len(text),
                    'app_name': app.name,
                    'tool_type': 'external_mcp'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for add_memories: {e}")
        
        return {
            "status": "success",
            "response": response
        }
        
    except Exception as e:
        logger.error(f"Error in add_memories_http: {e}")
        return {"error": f"Add memory failed: {str(e)}"}


@router.post("/chunk_documents")
async def chunk_documents_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Chunk all documents for the authenticated user"""
    try:
        # Get user
        user = get_or_create_user(db, str(current_supa_user.id), current_supa_user.email)
        
        # Run chunking
        chunking_service = ChunkingService()
        processed = await asyncio.to_thread(
            chunking_service.chunk_all_documents,
            db,
            str(user.id)
        )
        
        # 📊 Track MCP document chunking with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_chunk_documents',
                properties={
                    'user_email': current_supa_user.email,
                    'documents_processed': processed,
                    'tool_type': 'external_mcp'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for chunk_documents: {e}")
        
        return {
            "status": "success",
            "documents_processed": processed,
            "message": f"Successfully chunked {processed} documents. Your searches will now be faster and more accurate."
        }
        
    except Exception as e:
        logger.error(f"Error in chunk_documents_http: {e}")
        return {"error": f"Chunking failed: {str(e)}"}


@router.post("/sync_substack")
async def sync_substack_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Sync Substack posts for the user"""
    try:
        substack_url = request.get("substack_url", "")
        max_posts = request.get("max_posts", 20)
        
        if not substack_url:
            return {"error": "Substack URL is required"}
        
        # Use the SubstackService to handle the sync
        service = SubstackService()
        synced_count, message = await service.sync_substack_posts(
            db=db,
            supabase_user_id=str(current_supa_user.id),
            substack_url=substack_url,
            max_posts=max_posts,
            use_mem0=True
        )
        
        # 📊 Track MCP Substack sync with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_sync_substack',
                properties={
                    'user_email': current_supa_user.email,
                    'substack_url': substack_url,
                    'max_posts_requested': max_posts,
                    'synced_count': synced_count,
                    'tool_type': 'external_mcp'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for sync_substack: {e}")
        
        return {
            "status": "success",
            "synced_count": synced_count,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error in sync_substack_http: {e}")
        return {"error": f"Substack sync failed: {str(e)}"}


# Unified Memory System Endpoints (Local Development)

@router.post("/unified_search")
async def unified_search_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Advanced search using unified memory system (Mem0 + Graphiti)"""
    try:
        query = request.get("query", "")
        limit = request.get("limit", MEMORY_LIMITS.search_default)
        
        if not query:
            return {"error": "Query parameter is required"}
        
        # Check if unified memory is available
        if not should_use_unified_memory():
            return {"error": "Unified memory system not available. Enable with USE_UNIFIED_MEMORY=true in local development."}
        
        # Enforce configured limits
        limit = min(max(1, limit), MEMORY_LIMITS.search_max)
        
        # Get user
        user = get_or_create_user(db, str(current_supa_user.id), current_supa_user.email)
        
        # Use unified memory client
        from app.utils.memory import get_enhanced_memory_client
        unified_client = get_enhanced_memory_client()
        
        # Perform unified search
        results = await unified_client.search_memory(
            query=query, 
            user_id=str(current_supa_user.id), 
            limit=limit
        )
        
        # 📊 Track unified search usage with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_unified_search',
                properties={
                    'user_email': current_supa_user.email,
                    'query_length': len(query),
                    'mem0_results_count': len(results.get('mem0_results', [])),
                    'graphiti_results_count': len(results.get('graphiti_results', [])),
                    'limit_requested': limit,
                    'tool_type': 'unified_memory'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for unified_search: {e}")
        
        return {
            "status": "success",
            "results": results,
            "unified": True
        }
        
    except Exception as e:
        logger.error(f"Error in unified_search_http: {e}")
        return {"error": f"Unified search failed: {str(e)}"}


@router.post("/unified_add_memory")
async def unified_add_memory_http(
    request: Dict[str, Any],
    current_supa_user: SupabaseUser = Depends(get_current_supa_user),
    db: Session = Depends(get_db)
):
    """Add memory using unified memory system (Mem0 + Graphiti)"""
    try:
        text = request.get("text", "")
        timestamp_str = request.get("timestamp")  # Optional ISO timestamp
        
        if not text:
            return {"error": "Text parameter is required"}
        
        # Check if unified memory is available
        if not should_use_unified_memory():
            return {"error": "Unified memory system not available. Enable with USE_UNIFIED_MEMORY=true in local development."}
        
        # Get user and app
        user, app = get_user_and_app(db, str(current_supa_user.id), "claude", current_supa_user.email)
        
        if not app.is_active:
            return {"error": f"App {app.name} is currently paused. Cannot create new memories."}
        
        # Parse timestamp if provided
        timestamp = None
        if timestamp_str:
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                return {"error": "Invalid timestamp format. Use ISO format (e.g., 2024-01-01T12:00:00Z)"}
        
        # Use unified memory client
        from app.utils.memory import get_enhanced_memory_client
        unified_client = get_enhanced_memory_client()
        
        # Add memory with unified system
        results = await unified_client.add_memory(
            content=text,
            user_id=str(current_supa_user.id),
            metadata={
                "source_app": "openmemory_unified",
                "mcp_client": "claude",
                "app_db_id": str(app.id)
            },
            timestamp=timestamp
        )
        
        # 📊 Track unified memory creation with PostHog
        try:
            posthog = get_posthog_client()
            posthog.capture(
                user_id=str(current_supa_user.id),
                event='mcp_unified_add_memory',
                properties={
                    'user_email': current_supa_user.email,
                    'memory_length': len(text),
                    'app_name': app.name,
                    'has_custom_timestamp': timestamp is not None,
                    'tool_type': 'unified_memory'
                }
            )
        except Exception as e:
            logger.error(f"PostHog tracking failed for unified_add_memory: {e}")
        
        return {
            "status": "success",
            "results": results,
            "unified": True
        }
        
    except Exception as e:
        logger.error(f"Error in unified_add_memory_http: {e}")
        return {"error": f"Unified add memory failed: {str(e)}"} 