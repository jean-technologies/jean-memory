import logging
import json
import gc  # Add garbage collection
import functools
import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
# Defer heavy imports
# from app.utils.memory import get_memory_client
from fastapi import FastAPI, Request, Depends, Header, Response
from fastapi.routing import APIRouter
import contextvars
import os
from dotenv import load_dotenv
from app.database import SessionLocal
from app.models import Memory, MemoryState, MemoryStatusHistory, MemoryAccessLog, Document, DocumentChunk, User, SubscriptionTier
from app.utils.db import get_user_and_app, get_or_create_user
from app.middleware.subscription_middleware import SubscriptionChecker
import uuid
import datetime
from app.utils.permissions import check_memory_access_permissions
from app.auth import get_current_user
from typing import Optional, Dict
# Defer heavy imports
# from qdrant_client import models as qdrant_models
# from app.integrations.substack_service import SubstackService
# from app.utils.gemini import GeminiService
import asyncio
# Defer heavy imports
# import google.generativeai as genai
# from app.services.chunking_service import ChunkingService
from sqlalchemy import text
from app.config.memory_limits import MEMORY_LIMITS
from fastapi.responses import JSONResponse
from .utils.decorators import retry_on_exception
from qdrant_client import QdrantClient


# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Initialize MCP
mcp = FastMCP("Jean Memory")

# Add logging for MCP initialization
logger.info(f"Initialized MCP server with name: Jean Memory")
logger.info(f"MCP server object: {mcp}")
logger.info(f"MCP internal server: {mcp._mcp_server}")

# DO NOT initialize memory_client globally:
# memory_client = get_memory_client()

# Context variables for user_id (Supabase User ID string) and client_name
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("supa_user_id")
client_name_var: contextvars.ContextVar[str] = contextvars.ContextVar("client_name")

# Global dictionary to manage SSE connections
sse_message_queues: Dict[str, asyncio.Queue] = {}

# FIXED: Session-based ID mapping to prevent race conditions
# Each user session gets its own mapping that gets cleaned up
chatgpt_session_mappings: Dict[str, Dict[str, str]] = {}

def cleanup_old_chatgpt_sessions():
    """Clean up old session mappings to prevent memory leaks"""
    # Keep only the 50 most recent sessions
    if len(chatgpt_session_mappings) > 50:
        # Remove oldest sessions (simple cleanup strategy)
        sessions_to_remove = list(chatgpt_session_mappings.keys())[:-50]
        for session_id in sessions_to_remove:
            del chatgpt_session_mappings[session_id]
        logger.info(f"Cleaned up {len(sessions_to_remove)} old ChatGPT session mappings")

# Create a router for MCP endpoints
mcp_router = APIRouter(prefix="/mcp")

# Initialize SSE transport
sse = SseServerTransport("/mcp/messages/")

# Analytics tracking - only active if ENABLE_ANALYTICS=true
def _track_tool_usage(tool_name: str, properties: dict = None):
    """Analytics tracking - only active if enabled via environment variable"""
    # Only track if explicitly enabled via environment variable
    if not os.getenv('ENABLE_ANALYTICS', 'false').lower() == 'true':
        return
    
    try:
        from app.utils.posthog_client import get_posthog_client
        from datetime import datetime
        
        supa_uid = user_id_var.get(None)
        client_name = client_name_var.get(None)
        
        if supa_uid:
            posthog = get_posthog_client()
            
            # Create the event name
            event_name = f'mcp_core_{tool_name}' if not tool_name.startswith('chatgpt_') else f'mcp_{tool_name}'
            
            # Merge default properties with provided ones
            event_properties = {
                'tool_type': 'core_mcp',
                'source': 'mcp_server',
                'client_name': client_name,
                'timestamp': datetime.now().isoformat(),
                **(properties or {})
            }
            
            # Send to PostHog
            posthog.capture(
                user_id=supa_uid,
                event=event_name,
                properties=event_properties
            )
            
            logger.debug(f"Tracked tool usage: {event_name} for user {supa_uid}")
    except Exception:
        # Never let analytics break the main functionality
        pass

@mcp.tool(description="Add new memories to the user's memory")
@retry_on_exception(retries=3, delay=1, backoff=2, exceptions=(ConnectionError,))
async def add_memories(text: str, tags: Optional[list[str]] = None) -> str:
    """
    Add memories to the user's personal memory bank.
    These memories are stored in a vector database and can be searched later.
    Optionally, add a list of string tags for later filtering.
    """
    # Lazy import
    from app.utils.memory import get_memory_client
    import time
    start_time = time.time()
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    logger.info(f"add_memories: Starting for user {supa_uid}")

    # 🚨 CRITICAL: Add comprehensive logging to detect contamination
    logger.error(f"🔍 ADD_MEMORIES DEBUG - User ID from context: {supa_uid}")
    logger.error(f"🔍 ADD_MEMORIES DEBUG - Client name from context: {client_name}")
    logger.error(f"🔍 ADD_MEMORIES DEBUG - Memory content preview: {text[:100]}...")

    
    memory_client = get_memory_client()

    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"

    # Detect if this is Claude Desktop for simpler response
    is_claude_desktop = (client_name not in ["chatgpt", "default_agent_app"] and 
                        not client_name.startswith("api_"))

    # For Claude Desktop: return immediately and process in background
    if is_claude_desktop:
        # Start background task - fire and forget
        asyncio.create_task(_add_memories_background_claude(text, tags, supa_uid, client_name))
        
        # Return immediately for instant response
        return "✅ Memory added."

    # For API users and other clients: keep synchronous for reliability
    try:
        # Track memory addition (only if private analytics available)
        _track_tool_usage('add_memories', {
            'text_length': len(text),
            'has_tags': bool(tags)
        })
        
        db_start_time = time.time()
        db = SessionLocal()
        db_duration = time.time() - db_start_time
        logger.info(f"add_memories: DB connection for user {supa_uid} took {db_duration:.2f}s")
        try:
            user, app = get_user_and_app(db, supabase_user_id=supa_uid, app_name=client_name, email=None)
            
            # Check if user is trying to use Pro feature (tags)
            if tags and tags:  # If tags are provided and not empty
                try:
                    SubscriptionChecker.check_pro_features(user, "metadata tagging")
                except Exception as e:
                    return f"Error: {str(e)}"

            if not app.is_active:
                return f"Error: App {app.name} is currently paused. Cannot create new memories."

            mem0_start_time = time.time()
            logger.info(f"add_memories: Starting mem0 client call for user {supa_uid}")

            metadata = {
                "source_app": "openmemory_mcp",
                "mcp_client": client_name,
                "app_db_id": str(app.id)
            }
            if tags:
                metadata['tags'] = tags

            message_to_add = {
                "role": "user",
                "content": text
            }

            logger.info(f"🔍 DEBUG: Passing this metadata to mem0.add: {metadata}")

            loop = asyncio.get_running_loop()
            add_call = functools.partial(
                memory_client.add,
                messages=[message_to_add],
                user_id=supa_uid,
                metadata=metadata
            )
            response = await loop.run_in_executor(None, add_call)

            mem0_duration = time.time() - mem0_start_time
            logger.info(f"add_memories: mem0 client call for user {supa_uid} took {mem0_duration:.2f}s")

            if isinstance(response, dict) and 'results' in response:
                added_count = 0
                updated_count = 0
                first_added_id = None
                
                for result in response['results']:
                    mem0_memory_id_str = result['id']
                    mem0_content = result.get('memory', text)

                    # Capture the ID of the first memory that is ADDED
                    if result.get('event') == 'ADD' and not first_added_id:
                        first_added_id = mem0_memory_id_str

                    if result.get('event') == 'ADD':
                        sql_memory_record = Memory(
                            user_id=user.id,
                            app_id=app.id,
                            content=mem0_content,
                            state=MemoryState.active,
                            metadata_={**result.get('metadata', {}), "mem0_id": mem0_memory_id_str}
                        )
                        db.add(sql_memory_record)
                        db.flush()  # Flush to get the memory ID before creating history
                        added_count += 1
                        
                        # Don't create history for initial creation since old_state cannot be NULL
                        # The memory is created with state=active, which is sufficient
                        # History tracking starts from the first state change
                    elif result.get('event') == 'DELETE':
                        # Find the existing SQL memory record by mem0_id
                        sql_memory_record = db.query(Memory).filter(
                            text("metadata_->>'mem0_id' = :mem0_id"),
                            Memory.user_id == user.id
                        ).params(mem0_id=mem0_memory_id_str).first()
                        
                        if sql_memory_record:
                            sql_memory_record.state = MemoryState.deleted
                            sql_memory_record.deleted_at = datetime.datetime.now(datetime.UTC)
                            history = MemoryStatusHistory(
                                memory_id=sql_memory_record.id,
                                changed_by=user.id,
                                old_state=MemoryState.active,
                                new_state=MemoryState.deleted
                            )
                            db.add(history)
                    elif result.get('event') == 'UPDATE':
                        updated_count += 1
                        
                db_commit_start_time = time.time()
                db.commit()
                db_commit_duration = time.time() - db_commit_start_time
                logger.info(f"add_memories: DB commit for user {supa_uid} took {db_commit_duration:.2f}s")
                
                # Detailed response for API users and other clients
                response_message = ""
                if added_count > 0:
                    response_message = f"Successfully added {added_count} new memory(ies)."
                elif updated_count > 0:
                    response_message = f"Updated {updated_count} existing memory(ies)."
                else:
                    response_message = "Memory processed but no changes made (possibly duplicate)."

                response_data = {
                    "message": response_message,
                    "first_added_id": first_added_id,
                    "content_preview": f"{text[:100]}{'...' if len(text) > 100 else ''}"
                }
                return json.dumps(response_data)
            else:
                # Handle case where response doesn't have expected format
                total_duration = time.time() - start_time
                return json.dumps({"message": f"Memory processed successfully in {total_duration:.2f}s.", "response_preview": f"{str(response)[:200]}{'...' if len(str(response)) > 200 else ''}"})
        finally:
            db.close()
    except Exception as e:
        total_duration = time.time() - start_time
        logging.error(f"Error in add_memories MCP tool after {total_duration:.2f}s: {e}", exc_info=True)
        return f"Error adding to memory: {e}"


async def _add_memories_background_claude(text: str, tags: Optional[list[str]], supa_uid: str, client_name: str):
    """Background memory processing for Claude Desktop - fire and forget"""
    try:
        # Reuse the same logic as the synchronous version
        from app.utils.memory import get_memory_client
        
        memory_client = get_memory_client()
        
        # Track memory addition (only if private analytics available)
        _track_tool_usage('add_memories', {
            'text_length': len(text),
            'has_tags': bool(tags)
        })
        
        db = SessionLocal()
        try:
            user, app = get_user_and_app(db, supabase_user_id=supa_uid, app_name=client_name, email=None)
            
            # Skip Pro features check for background - just ignore tags if not Pro
            if tags and tags:
                try:
                    SubscriptionChecker.check_pro_features(user, "metadata tagging")
                except Exception:
                    tags = None  # Just remove tags instead of failing
                    
            if not app.is_active:
                logger.warning(f"Background memory add skipped - app {app.name} is paused for user {supa_uid}")
                return

            metadata = {
                "source_app": "openmemory_mcp",
                "mcp_client": client_name,
                "app_db_id": str(app.id)
            }
            if tags:
                metadata['tags'] = tags

            message_to_add = {
                "role": "user",
                "content": text
            }

            loop = asyncio.get_running_loop()
            add_call = functools.partial(
                memory_client.add,
                messages=[message_to_add],
                user_id=supa_uid,
                metadata=metadata
            )
            response = await loop.run_in_executor(None, add_call)

            if isinstance(response, dict) and 'results' in response:
                for result in response['results']:
                    mem0_memory_id_str = result['id']
                    mem0_content = result.get('memory', text)

                    if result.get('event') == 'ADD':
                        sql_memory_record = Memory(
                            user_id=user.id,
                            app_id=app.id,
                            content=mem0_content,
                            state=MemoryState.active,
                            metadata_={**result.get('metadata', {}), "mem0_id": mem0_memory_id_str}
                        )
                        db.add(sql_memory_record)
                    elif result.get('event') == 'DELETE':
                        sql_memory_record = db.query(Memory).filter(
                            text("metadata_->>'mem0_id' = :mem0_id"),
                            Memory.user_id == user.id
                        ).params(mem0_id=mem0_memory_id_str).first()
                        
                        if sql_memory_record:
                            sql_memory_record.state = MemoryState.deleted
                            sql_memory_record.deleted_at = datetime.datetime.now(datetime.UTC)
                            history = MemoryStatusHistory(
                                memory_id=sql_memory_record.id,
                                changed_by=user.id,
                                old_state=MemoryState.active,
                                new_state=MemoryState.deleted
                            )
                            db.add(history)
                            
                db.commit()
                logger.info(f"Background memory add completed for user {supa_uid}: {text[:50]}...")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Background memory add failed for user {supa_uid}: {e}", exc_info=True)
        # Don't re-raise - this is fire and forget


@mcp.tool(description="Add new memory/fact/observation about the user. Use this to save: 1) Important information learned in conversation, 2) User preferences/values/beliefs, 3) Facts about their work/life/interests, 4) Anything the user wants remembered. The memory will be permanently stored and searchable.")
async def add_observation(text: str) -> str:
    """
    This is an alias for the add_memories tool with a more descriptive prompt for the agent.
    Functionally, it performs the same action.
    """
    # This function now simply calls the other one to avoid code duplication.
    # Note: This alias does not expose the 'tags' parameter.
    return await add_memories(text)


@mcp.tool(description="Search the user's memory for memories that match the query. Optionally filter by tags.")
@retry_on_exception(retries=3, delay=1, backoff=2, exceptions=(ConnectionError,))
async def search_memory(query: str, limit: int = None, tags_filter: Optional[list[str]] = None) -> str:
    """
    Search the user's memory for memories that match the query.
    Returns memories that are semantically similar to the query.
    
    Args:
        query: The search term or phrase to look for
        limit: Maximum number of results to return (default: 10, max: 50) 
        tags_filter: Optional list of tags to filter results (e.g., ["work", "project-alpha"])
                    Only memories containing ALL specified tags will be returned.
    
    Returns:
        JSON string containing list of matching memories with their content and metadata
    """
    # Lazy import
    from app.utils.memory import get_memory_client
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    # Use configured limits
    if limit is None:
        limit = MEMORY_LIMITS.search_default
    limit = min(max(1, limit), MEMORY_LIMITS.search_max)
    
    try:
        # Track search usage (only if private analytics available)
        _track_tool_usage('search_memory', {
            'query_length': len(query),
            'limit': limit,
            'has_tags_filter': bool(tags_filter)
        })
        
        # Add timeout to prevent hanging
        return await asyncio.wait_for(_search_memory_unified_impl(query, supa_uid, client_name, limit, tags_filter), timeout=30.0)
    except asyncio.TimeoutError:
        return f"Search timed out. Please try a simpler query."
    except Exception as e:
        logging.error(f"Error in search_memory MCP tool: {e}", exc_info=True)
        return f"Error searching memory: {e}"


async def _search_memory_unified_impl(query: str, supa_uid: str, client_name: str, limit: int = 10, tags_filter: Optional[list[str]] = None) -> str:
    """Unified implementation that supports both basic search and tag filtering"""
    from app.utils.memory import get_memory_client
    memory_client = get_memory_client()
    db = SessionLocal()
    
    try:
        # Get user (but don't filter by specific app - search ALL memories)
        user = get_or_create_user(db, supa_uid, None)
        
        # Check if user is trying to use Pro feature (tag filtering)
        if tags_filter and tags_filter:  # If tags_filter is provided and not empty
            try:
                SubscriptionChecker.check_pro_features(user, "advanced tag filtering")
            except Exception as e:
                return f"Error: {str(e)}"
        
        # 🚨 CRITICAL: Add user validation logging
        logger.info(f"🔍 SEARCH DEBUG - User ID: {supa_uid}, DB User ID: {user.id}, DB User user_id: {user.user_id}")
        
        # SECURITY CHECK: Verify user ID matches
        if user.user_id != supa_uid:
            logger.error(f"🚨 USER ID MISMATCH: Expected {supa_uid}, got {user.user_id}")
            return f"Error: User ID validation failed. Security issue detected."

        # We fetch a larger pool of results to filter from if a filter is applied
        fetch_limit = limit * 5 if tags_filter else limit

        # Run blocking I/O in a separate thread
        loop = asyncio.get_running_loop()
        search_call = functools.partial(memory_client.search, query=query, user_id=supa_uid, limit=fetch_limit)
        mem0_search_results = await loop.run_in_executor(None, search_call)
        
        # 🚨 CRITICAL: Log the search results for debugging
        logger.info(f"🔍 SEARCH DEBUG - Query: {query}, Results count: {len(mem0_search_results.get('results', [])) if isinstance(mem0_search_results, dict) else len(mem0_search_results) if isinstance(mem0_search_results, list) else 0}")

        processed_results = []
        actual_results_list = []
        if isinstance(mem0_search_results, dict) and 'results' in mem0_search_results:
             actual_results_list = mem0_search_results['results']
        elif isinstance(mem0_search_results, list):
             actual_results_list = mem0_search_results

        if actual_results_list and tags_filter:
            logger.info(f"🔍 DEBUG: First result metadata: {actual_results_list[0].get('metadata')}")

        for mem_data in actual_results_list:
            # Skip if we've reached our limit
            if len(processed_results) >= limit:
                break
                
            mem0_id = mem_data.get('id')
            if not mem0_id: 
                continue
            
            # Apply tag filtering if requested
            if tags_filter:
                # Handle the metadata null case
                metadata = mem_data.get('metadata') or {}
                mem_tags = metadata.get('tags', [])
                
                # Only include if ALL specified tags are present
                if not all(tag in mem_tags for tag in tags_filter):
                    continue
            
            processed_results.append(mem_data)
        
        # 🚨 Log final results count
        logger.info(f"🔍 SEARCH FINAL - User {supa_uid}: {len(processed_results)} memories returned after filtering (tags_filter: {tags_filter})")
        
        return json.dumps(processed_results)
    finally:
        db.close()


@mcp.tool(description="Search the user's memory, with optional tag filtering (V2).")
@retry_on_exception(retries=3, delay=1, backoff=2, exceptions=(ConnectionError,))
async def search_memory_v2(query: str, limit: int = None, tags_filter: Optional[list[str]] = None) -> str:
    """
    V2 search tool. Search user's memory with optional tag filtering.
    Returns memories that are semantically similar to the query.
    This is the recommended search tool for API key users.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    if limit is None:
        limit = MEMORY_LIMITS.search_default
    limit = min(max(1, limit), MEMORY_LIMITS.search_max)
    
    try:
        # Track search v2 usage (only if private analytics available)
        _track_tool_usage('search_memory_v2', {
            'query_length': len(query),
            'limit': limit,
            'has_tags_filter': bool(tags_filter)
        })
        
        return await asyncio.wait_for(_search_memory_v2_impl(query, supa_uid, client_name, limit, tags_filter), timeout=30.0)
    except asyncio.TimeoutError:
        return f"Search timed out. Please try a simpler query."
    except Exception as e:
        logging.error(f"Error in search_memory_v2 MCP tool: {e}", exc_info=True)
        return f"Error searching memory: {e}"

async def _search_memory_v2_impl(query: str, supa_uid: str, client_name: str, limit: int = 10, tags_filter: Optional[list[str]] = None) -> str:
    """Implementation of V2 search memory with post-fetch filtering."""
    from app.utils.memory import get_memory_client
    memory_client = get_memory_client()
    
    # We fetch a larger pool of results to filter from if a filter is applied
    fetch_limit = limit * 5 if tags_filter else limit

    # Call the original search function without the metadata filter to avoid the bug
    search_call = functools.partial(memory_client.search, query=query, user_id=supa_uid, limit=fetch_limit)
    loop = asyncio.get_running_loop()
    mem0_search_results = await loop.run_in_executor(None, search_call)
    
    actual_results_list = []
    if isinstance(mem0_search_results, dict) and 'results' in mem0_search_results:
         actual_results_list = mem0_search_results['results']
    elif isinstance(mem0_search_results, list):
         actual_results_list = mem0_search_results

    if actual_results_list:
        logger.info(f"🔍 DEBUG: Metadata of first result in _search_memory_v2_impl: {actual_results_list[0].get('metadata')}")

    # Perform filtering in our application code if a filter is provided
    if tags_filter:
        filtered_results = []
        for mem in actual_results_list:
            if len(filtered_results) >= limit:
                break
            
            # Robustly handle cases where metadata is missing or null.
            metadata = mem.get('metadata') or {}
            mem_tags = metadata.get('tags', [])
            if all(tag in mem_tags for tag in tags_filter):
                filtered_results.append(mem)
        processed_results = filtered_results
    else:
        processed_results = actual_results_list

    return json.dumps(processed_results)


@mcp.tool(description="List all memories in the user's memory")
@retry_on_exception(retries=3, delay=1, backoff=2, exceptions=(ConnectionError,))
async def list_memories(limit: int = None) -> str:
    """
    List all memories for the user.
    Returns a formatted list of memories with their content and metadata.
    """
    # Lazy import
    from app.utils.memory import get_memory_client
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    # Use configured limits
    if limit is None:
        limit = MEMORY_LIMITS.list_default
    limit = min(max(1, limit), MEMORY_LIMITS.list_max)
    
    try:
        # Track list usage (only if private analytics available)
        _track_tool_usage('list_memories', {'limit': limit})
        
        # Add timeout to prevent hanging
        return await asyncio.wait_for(_list_memories_impl(supa_uid, client_name, limit), timeout=30.0)
    except asyncio.TimeoutError:
        return f"List memories timed out. Please try again."
    except Exception as e:
        logging.error(f"Error in list_memories MCP tool: {e}", exc_info=True)
        return f"Error getting memories: {e}"


async def _list_memories_impl(supa_uid: str, client_name: str, limit: int = 20) -> str:
    """Implementation of list_memories with timeout protection"""
    from app.utils.memory import get_memory_client
    import time
    import asyncio
    import functools
    start_time = time.time()
    logger.info(f"list_memories: Starting for user {supa_uid}")

    memory_client = get_memory_client()
    db = SessionLocal()
    try:
        # Get user (but don't filter by specific app - show ALL memories)
        user = get_or_create_user(db, supa_uid, None)
        
        # 🚨 CRITICAL: Add user validation logging
        logger.info(f"📋 LIST DEBUG - User ID: {supa_uid}, DB User ID: {user.id}, DB User user_id: {user.user_id}")
        
        # SECURITY CHECK: Verify user ID matches
        if user.user_id != supa_uid:
            logger.error(f"🚨 USER ID MISMATCH: Expected {supa_uid}, got {user.user_id}")
            return f"Error: User ID validation failed. Security issue detected."

        # Get ALL memories for this user across all apps with limit
        fetch_start_time = time.time()
        
        # Run blocking I/O in a separate thread
        loop = asyncio.get_running_loop()
        get_all_call = functools.partial(memory_client.get_all, user_id=supa_uid, limit=limit)
        all_mem0_memories = await loop.run_in_executor(None, get_all_call)

        fetch_duration = time.time() - fetch_start_time
        
        results_count = len(all_mem0_memories.get('results', [])) if isinstance(all_mem0_memories, dict) else len(all_mem0_memories) if isinstance(all_mem0_memories, list) else 0
        logger.info(f"list_memories: mem0.get_all took {fetch_duration:.2f}s, found {results_count} results for user {supa_uid}")

        processed_results = []
        actual_results_list = []
        if isinstance(all_mem0_memories, dict) and 'results' in all_mem0_memories:
             actual_results_list = all_mem0_memories['results']
        elif isinstance(all_mem0_memories, list):
             actual_results_list = all_mem0_memories

        for mem_data in actual_results_list[:limit]:  # Extra safety to ensure limit
            mem0_id = mem_data.get('id')
            if not mem0_id: continue
            
            # 🚨 CRITICAL: Check if this memory belongs to the correct user
            memory_content = mem_data.get('memory', mem_data.get('content', ''))
            
            # Log suspicious content that might belong to other users
            if any(suspicious in memory_content.lower() for suspicious in ['pralayb', '/users/pralayb', 'faircopyfolder']):
                logger.error(f"🚨 SUSPICIOUS MEMORY DETECTED - User {supa_uid} got memory: {memory_content[:100]}...")
                logger.error(f"🚨 Memory metadata: {mem_data.get('metadata', {})}")
                continue  # Skip this memory
            
            processed_results.append(mem_data)
        
        # 🚨 Log final results count
        logger.info(f"📋 LIST FINAL - User {supa_uid}: {len(processed_results)} memories returned after filtering")
        
        json_start_time = time.time()
        response_json = json.dumps(processed_results)
        json_duration = time.time() - json_start_time
        
        total_duration = time.time() - start_time
        logger.info(f"list_memories: Completed for user {supa_uid} in {total_duration:.2f}s (fetch: {fetch_duration:.2f}s, json: {json_duration:.2f}s)")
        
        return response_json
    finally:
        db.close()


@mcp.tool(description="Delete all memories in the user's memory")
async def delete_all_memories() -> str:
    """
    Delete all memories for the user. This action cannot be undone.
    Requires confirmation by being called explicitly.
    """
    # Lazy import
    from app.utils.memory import get_memory_client
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    memory_client = get_memory_client() # Initialize client when tool is called
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    try:
        # Track delete all usage (only if private analytics available)
        _track_tool_usage('delete_all_memories', {})
        
        db = SessionLocal()
        try:
            user, app = get_user_and_app(db, supabase_user_id=supa_uid, app_name=client_name, email=None)

            memory_client.delete_all(user_id=supa_uid)

            sql_memories_to_delete = db.query(Memory).filter(Memory.user_id == user.id).all()
            now = datetime.datetime.now(datetime.UTC)
            for mem_record in sql_memories_to_delete:
                if mem_record.state != MemoryState.deleted:
                    history = MemoryStatusHistory(
                        memory_id=mem_record.id,
                        changed_by=user.id,
                        old_state=mem_record.state,
                        new_state=MemoryState.deleted
                    )
                    db.add(history)
                    mem_record.state = MemoryState.deleted
                    mem_record.deleted_at = now
                    
                    access_log = MemoryAccessLog(
                        memory_id=mem_record.id,
                        app_id=app.id,
                        access_type="delete_all_mcp",
                        metadata_={
                            "operation": "bulk_delete_mcp_tool",
                            "mem0_user_id_cleared": supa_uid
                        }
                    )
                    db.add(access_log)
            
            return f"Successfully initiated deletion of all memories for user {supa_uid} via mem0 and updated SQL records."
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error in delete_all_memories MCP tool: {e}", exc_info=True)
        return f"Error deleting memories: {e}"


@mcp.tool(description="Get detailed information about a specific memory by its ID")
async def get_memory_details(memory_id: str) -> str:
    """
    Get detailed information about a specific memory, including all metadata.
    Use this to understand context about when and how a memory was created.
    """
    # Lazy import
    from app.utils.memory import get_memory_client
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    try:
        # Track memory details usage (only if private analytics available)
        _track_tool_usage('get_memory_details', {'memory_id_length': len(memory_id)})
        
        # Add timeout to prevent hanging
        return await asyncio.wait_for(_get_memory_details_impl(memory_id, supa_uid, client_name), timeout=10.0)
    except asyncio.TimeoutError:
        return f"Memory lookup timed out. Try again or check if memory ID '{memory_id}' is correct."
    except Exception as e:
        logging.error(f"Error in get_memory_details MCP tool: {e}", exc_info=True)
        return f"Error retrieving memory details: {e}"


async def _get_memory_details_impl(memory_id: str, supa_uid: str, client_name: str) -> str:
    """Optimized implementation of get_memory_details"""
    from app.utils.memory import get_memory_client
    
    db = SessionLocal()
    try:
        # Get user quickly
        user = get_or_create_user(db, supa_uid, None)
        
        # First try SQL database (fastest)
        sql_memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user.id,
            Memory.state != MemoryState.deleted
        ).first()
        
        if sql_memory:
            memory_details = {
                "id": str(sql_memory.id),
                "content": sql_memory.content,
                "created_at": sql_memory.created_at.isoformat() if sql_memory.created_at else None,
                "updated_at": sql_memory.updated_at.isoformat() if sql_memory.updated_at else None,
                "state": sql_memory.state.value if sql_memory.state else None,
                "metadata": sql_memory.metadata_ or {},
                "app_name": sql_memory.app.name if sql_memory.app else None,
                "categories": [cat.name for cat in sql_memory.categories] if sql_memory.categories else [],
                "source": "sql_database"
            }
            return json.dumps(memory_details, indent=2)
        
        # Try mem0 with direct search instead of getting all memories
        memory_client = get_memory_client()
        
        # Use search with the exact ID as query - much faster than get_all()
        search_result = memory_client.search(query=memory_id, user_id=supa_uid, limit=20)
        
        memories_list = []
        if isinstance(search_result, dict) and 'results' in search_result:
            memories_list = search_result['results']
        elif isinstance(search_result, list):
            memories_list = search_result
        
        # Look for exact ID match
        for mem in memories_list:
            if isinstance(mem, dict) and mem.get('id') == memory_id:
                return json.dumps({
                    "id": mem.get('id'),
                    "content": mem.get('memory', mem.get('content', 'No content available')),
                    "metadata": mem.get('metadata', {}),
                    "created_at": mem.get('created_at'),
                    "updated_at": mem.get('updated_at'),
                    "score": mem.get('score'),
                    "source": "mem0_vector_store"
                }, indent=2)
        
        return f"Memory with ID '{memory_id}' not found. Possible reasons:\n1. Memory doesn't exist\n2. Belongs to different user\n3. Has been deleted\n4. ID format incorrect"
        
    finally:
        db.close()


@mcp.tool(description="Sync Substack posts for the user. Provide the Substack URL (e.g., https://username.substack.com or username.substack.com). Note: This process may take 30-60 seconds depending on the number of posts being processed.")
async def sync_substack_posts(substack_url: str, max_posts: int = 20) -> str:
    # Lazy import
    from app.integrations.substack_service import SubstackService
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    # Track Substack sync usage (only if private analytics available)
    _track_tool_usage('sync_substack_posts', {
        'substack_url_length': len(substack_url),
        'max_posts': max_posts
    })
    
    # Let user know we're starting
    logger.info(f"Starting Substack sync for {substack_url}")
    
    try:
        db = SessionLocal()
        try:
            # Use the SubstackService to handle the sync
            service = SubstackService()
            synced_count, message = await service.sync_substack_posts(
                db=db,
                supabase_user_id=supa_uid,
                substack_url=substack_url,
                max_posts=max_posts,
                use_mem0=True  # Try to use mem0, but it will gracefully degrade if not available
            )
            
            # Enhanced return message
            if synced_count > 0:
                return f"✅ {message}\n\n📊 Processed {synced_count} posts and added them to your memory system. Posts are now searchable using memory tools."
            else:
                return f"⚠️ {message}"
            
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error in sync_substack_posts MCP tool: {e}", exc_info=True)
        return f"❌ Error syncing Substack: {str(e)}"


@mcp.tool(description="Deep memory search with automatic full document inclusion. Use this for: 1) Reading/summarizing specific essays (e.g. 'summarize The Irreverent Act'), 2) Analyzing personality/writing style across documents, 3) Finding insights from essays written months/years ago, 4) Any query needing full essay context. Automatically detects and includes complete relevant documents using dynamic scoring.")
async def deep_memory_query(search_query: str, memory_limit: int = None, chunk_limit: int = None, include_full_docs: bool = True) -> str:
    """
    Performs a deep, comprehensive search across ALL user content using Gemini.
    Automatically detects when specific documents/essays are referenced and includes their full content.
    This is thorough but slower - use search_memory for simple queries.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    try:
        # Track deep memory usage (only if private analytics available)
        _track_tool_usage('deep_memory_query', {
            'query_length': len(search_query),
            'memory_limit': memory_limit,
            'chunk_limit': chunk_limit,
            'include_full_docs': include_full_docs
        })
        
        # Add timeout to prevent hanging - 60 seconds max
        return await asyncio.wait_for(
            _deep_memory_query_impl(search_query, supa_uid, client_name, memory_limit, chunk_limit, include_full_docs),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        return f"Deep memory search timed out for query '{search_query}'. Try using 'search_memory' for faster results, or simplify your query."
    except Exception as e:
        logger.error(f"Error in deep_memory_query: {e}", exc_info=True)
        return f"Error performing deep search: {str(e)}"


async def _deep_memory_query_impl(search_query: str, supa_uid: str, client_name: str, memory_limit: int = None, chunk_limit: int = None, include_full_docs: bool = True) -> str:
    """Optimized implementation of deep_memory_query"""
    # Lazy imports
    from app.utils.memory import get_memory_client
    from app.utils.gemini import GeminiService
    from app.services.chunking_service import ChunkingService
    import google.generativeai as genai
    
    # Use conservative limits to prevent timeouts
    if memory_limit is None:
        memory_limit = min(10, MEMORY_LIMITS.deep_memory_default)  # Cap at 10 for timeout prevention
    if chunk_limit is None:
        chunk_limit = min(8, MEMORY_LIMITS.deep_chunk_default)   # Cap at 8 for timeout prevention
    memory_limit = min(max(1, memory_limit), min(15, MEMORY_LIMITS.deep_memory_max))  # Hard cap at 15
    chunk_limit = min(max(1, chunk_limit), min(10, MEMORY_LIMITS.deep_chunk_max))    # Hard cap at 10
    
    import time
    start_time = time.time()
    logger.info(f"deep_memory_query: Starting for user {supa_uid}")
    
    try:
        db = SessionLocal()
        try:
            # Get user and app
            user, app = get_user_and_app(db, supa_uid, client_name)
            if not user or not app:
                return "Error: User or app not found"
            
            # Initialize services
            memory_client = get_memory_client()
            gemini_service = GeminiService()
            chunking_service = ChunkingService()
            
            # 1. Get ALL memories for comprehensive context
            mem_fetch_start_time = time.time()
            all_memories_result = memory_client.get_all(user_id=supa_uid, limit=memory_limit)
            search_memories_result = memory_client.search(
                query=search_query,
                user_id=supa_uid,
                limit=memory_limit
            )
            mem_fetch_duration = time.time() - mem_fetch_start_time
            
            # Combine and prioritize memories
            all_memories = []
            search_memories = []
            
            if isinstance(all_memories_result, dict) and 'results' in all_memories_result:
                all_memories = all_memories_result['results']
            elif isinstance(all_memories_result, list):
                all_memories = all_memories_result
                
            if isinstance(search_memories_result, dict) and 'results' in search_memories_result:
                search_memories = search_memories_result['results']
            elif isinstance(search_memories_result, list):
                search_memories = search_memories_result
            
            # Prioritize search results, then add other memories
            memory_ids_seen = set()
            prioritized_memories = []
            
            # Add search results first
            for mem in search_memories:
                if isinstance(mem, dict) and mem.get('id'):
                    memory_ids_seen.add(mem['id'])
                    prioritized_memories.append(mem)
            
            # Add other memories up to limit
            for mem in all_memories:
                if len(prioritized_memories) >= memory_limit:
                    break
                if isinstance(mem, dict) and mem.get('id') and mem['id'] not in memory_ids_seen:
                    prioritized_memories.append(mem)
            
            logger.info(f"deep_memory_query: Memory fetching for user {supa_uid} took {mem_fetch_duration:.2f}s. Found {len(prioritized_memories)} memories.")

            # 2. Get ALL documents for comprehensive analysis
            doc_fetch_start_time = time.time()
            all_db_documents = db.query(Document).filter(
                Document.user_id == user.id
            ).order_by(Document.created_at.desc()).limit(20).all()
            doc_fetch_duration = time.time() - doc_fetch_start_time
            logger.info(f"deep_memory_query: Document fetching for user {supa_uid} took {doc_fetch_duration:.2f}s. Found {len(all_db_documents)} documents.")
            
            # Smart document selection based on query
            query_lower = search_query.lower()
            query_words = [w for w in query_lower.split() if len(w) > 2]
            selected_documents = []
            
            # Score each document for relevance
            for doc in all_db_documents:
                doc_title_lower = doc.title.lower()
                doc_content_lower = doc.content.lower() if doc.content else ""
                relevance_score = 0
                match_reasons = []
                
                # Title matching (highest priority)
                for word in query_words:
                    if word in doc_title_lower:
                        relevance_score += 10
                        match_reasons.append("title_keyword")
                
                # Check if entire title appears in query
                if doc_title_lower in query_lower:
                    relevance_score += 50
                    match_reasons.append("exact_title")
                
                # Content relevance scoring
                if doc_content_lower:
                    for word in query_words:
                        count = doc_content_lower.count(word)
                        relevance_score += min(count, 5)
                
                # Thematic matching
                if any(theme in query_lower for theme in ["personality", "values", "philosophy", "beliefs"]):
                    if any(word in doc_content_lower[:2000] for word in ["i think", "i believe", "my view"]):
                        relevance_score += 7
                        match_reasons.append("thematic_match")
                
                if relevance_score > 0:
                    selected_documents.append((doc, relevance_score, match_reasons))
            
            # Sort by relevance
            selected_documents.sort(key=lambda x: x[1], reverse=True)
            
            # If no documents matched but query seems to want documents, include recent ones
            if not selected_documents and any(word in query_lower for word in ["essay", "document", "post"]):
                selected_documents = [(doc, 1, ["recent"]) for doc in all_db_documents[:3]]
            
            # 3. Search document chunks
            chunk_search_start_time = time.time()
            relevant_chunks = []
            semantic_chunks = chunking_service.search_chunks(
                db=db,
                query=search_query,
                user_id=str(user.id),
                limit=chunk_limit
            )
            relevant_chunks.extend(semantic_chunks)
            chunk_search_duration = time.time() - chunk_search_start_time
            logger.info(f"deep_memory_query: Chunk searching for user {supa_uid} took {chunk_search_duration:.2f}s. Found {len(relevant_chunks)} chunks.")
            
            # 4. Build comprehensive context
            context = "=== USER'S COMPLETE KNOWLEDGE BASE ===\n\n"
            
            # Add memories with rich context
            if prioritized_memories:
                context += "=== MEMORIES (Thoughts, Experiences, Facts) ===\n\n"
                for i, mem in enumerate(prioritized_memories, 1):
                    if isinstance(mem, dict):
                        memory_text = mem.get('memory', mem.get('content', str(mem)))
                        metadata = mem.get('metadata', {})
                        created_at = mem.get('created_at', 'Unknown date')
                        
                        context += f"Memory {i}:\n"
                        context += f"Content: {memory_text}\n"
                        context += f"Date: {created_at}\n"
                        
                        if metadata:
                            source_app = metadata.get('source_app', 'Unknown')
                            context += f"Source: {source_app}\n"
                        context += "\n"
                context += "\n"
            
            # Add document information
            if all_db_documents:
                context += "=== ALL DOCUMENTS (Essays, Posts, Articles) ===\n\n"
                for i, doc in enumerate(all_db_documents, 1):
                    context += f"Document {i}: {doc.title}\n"
                    context += f"Type: {doc.document_type}\n"
                    context += f"URL: {doc.source_url or 'No URL'}\n"
                    context += f"Created: {doc.created_at}\n"
                    
                    if doc.content:
                        if len(doc.content) > 200:
                            context += f"Preview: {doc.content[:200]}...\n"
                        else:
                            context += f"Content: {doc.content}\n"
                    context += "\n"
                context += "\n"
            
            # Add relevant chunks
            if relevant_chunks:
                context += "=== RELEVANT DOCUMENT EXCERPTS ===\n\n"
                for i, chunk in enumerate(relevant_chunks, 1):
                    doc = next((d for d in all_db_documents if d.id == chunk.document_id), None)
                    if doc:
                        context += f"Excerpt {i} from '{doc.title}':\n"
                        context += f"Content: {chunk.content}\n\n"
                context += "\n"
            
            # 5. Include full documents based on relevance
            if include_full_docs and selected_documents:
                context += "=== FULL DOCUMENT CONTENT ===\n\n"
                
                docs_included = 0
                for doc, score, reasons in selected_documents:
                    if docs_included >= 3:  # Reasonable limit
                        break
                        
                    context += f"=== FULL CONTENT: {doc.title} ===\n"
                    context += f"Type: {doc.document_type}\n"
                    context += f"Relevance Score: {score} ({', '.join(reasons)})\n\n"
                    
                    if doc.content:
                        context += doc.content
                    
                    context += "\n\n" + "="*50 + "\n\n"
                    docs_included += 1
            
            # 6. Comprehensive prompt
            prompt = f"""You are an AI assistant with access to a comprehensive knowledge base about a specific user. Answer their question using all available information.

USER'S QUESTION: {search_query}

{context}

INSTRUCTIONS:
1. Answer comprehensively using the provided information
2. Draw connections between different pieces of information
3. Cite specific sources when making points
4. Be conversational and insightful
5. If you notice patterns across sources, point them out
6. If information is missing, be honest about limitations

Provide a thorough, insightful response."""
            
            # 7. Generate response (direct call for speed)
            gemini_start_time = time.time()
            logger.info(f"deep_memory_query: Starting Gemini call for user {supa_uid}")
            response = gemini_service.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096
                )
            )
            gemini_duration = time.time() - gemini_start_time
            logger.info(f"deep_memory_query: Gemini call for user {supa_uid} took {gemini_duration:.2f}s")
            
            processing_time = time.time() - start_time
            result = response.text
            result += f"\n\n📊 Deep Analysis: total={processing_time:.2f}s, mem_fetch={mem_fetch_duration:.2f}s, doc_fetch={doc_fetch_duration:.2f}s, chunk_search={chunk_search_duration:.2f}s, gemini={gemini_duration:.2f}s"
            
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in deep_memory_query after {processing_time:.2f}s: {e}", exc_info=True)
        return f"Error performing deep search: {str(e)}"


@mcp.tool(description="Fast memory search for simple questions - try this first before using heavier tools")
async def ask_memory(question: str) -> str:
    """
    Fast memory search for simple questions about the user.
    This searches stored memories only (not full documents) and returns quick, conversational answers.
    Perfect for everyday questions like "What are my preferences?" or "What do you know about me?"
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)

    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"

    try:
        # Track usage (only if private analytics available)
        _track_tool_usage('ask_memory', {'query_length': len(question)})
        
        # Lightweight version for better performance
        return await _lightweight_ask_memory_impl(question, supa_uid, client_name)
    except Exception as e:
        logger.error(f"Error in ask_memory: {e}", exc_info=True)
        return f"I had trouble processing your question: {str(e)}. Try rephrasing or use 'search_memory' for simpler queries."


async def _lightweight_ask_memory_impl(question: str, supa_uid: str, client_name: str) -> str:
    """Lightweight ask_memory implementation for quick answers"""
    from app.utils.memory import get_memory_client
    from mem0.llms.openai import OpenAILLM
    from mem0.configs.llms.base import BaseLlmConfig
    
    import time
    import asyncio # Import asyncio for timeout
    import functools
    start_time = time.time()
    logger.info(f"ask_memory: Starting for user {supa_uid}")
    
    try:
        db = SessionLocal()
        try:
            # Get user quickly
            user = get_or_create_user(db, supa_uid, None)
            
            # SECURITY CHECK: Verify user ID matches
            if user.user_id != supa_uid:
                logger.error(f"🚨 USER ID MISMATCH: Expected {supa_uid}, got {user.user_id}")
                return f"Error: User ID validation failed. Security issue detected."

            # Initialize services
            memory_client = get_memory_client()
            llm = OpenAILLM(config=BaseLlmConfig(model="gpt-4o-mini"))
            
            # 1. Quick memory search (limit to 10 for speed)
            search_start_time = time.time()
            logger.info(f"ask_memory: Starting memory search for user {supa_uid}")
            
            # Run blocking I/O in a separate thread
            loop = asyncio.get_running_loop()
            search_call = functools.partial(memory_client.search, query=question, user_id=supa_uid, limit=10)
            search_result = await loop.run_in_executor(None, search_call)

            search_duration = time.time() - search_start_time
            
            # Process results
            memories = []
            if isinstance(search_result, dict) and 'results' in search_result:
                memories = search_result['results'][:10]
            elif isinstance(search_result, list):
                memories = search_result[:10]
            
            logger.info(f"ask_memory: Memory search for user {supa_uid} took {search_duration:.2f}s. Found {len(memories)} results.")
            
            # Filter out contaminated memories and limit token usage
            clean_memories = []
            total_chars = 0
            max_chars = 8000  # Conservative limit to avoid token issues
            
            for idx, mem in enumerate(memories):
                memory_text = mem.get('memory', mem.get('content', ''))
                memory_line = f"Memory {idx+1}: {memory_text}"
                
                # Stop adding memories if we're approaching token limits
                if total_chars + len(memory_line) > max_chars:
                    break
                    
                clean_memories.append(memory_line)
                total_chars += len(memory_line)
            
            # Use LLM for fast, cheap synthesis with safer prompt
            prompt = f"""Based on the user's memories below, please answer their question.
            
            Memories:
            {chr(10).join(clean_memories)}
            
            Question: {question}
            
            Answer concisely based only on the provided memories."""
            
            try:
                llm_start_time = time.time()
                logger.info(f"ask_memory: Starting LLM call for user {supa_uid}")
                
                # Enforce a 25-second timeout on the LLM call and run it in a separate thread
                loop = asyncio.get_running_loop()
                llm_call = functools.partial(llm.generate_response, [{"role": "user", "content": prompt}])
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, llm_call),
                    timeout=25.0
                )

                llm_duration = time.time() - llm_start_time
                logger.info(f"ask_memory: LLM call for user {supa_uid} took {llm_duration:.2f}s")
                # Access response.text safely
                result = response
                total_duration = time.time() - start_time
                result += f"\n\n💡 Timings: search={search_duration:.2f}s, llm={llm_duration:.2f}s, total={total_duration:.2f}s | {len(clean_memories)} memories"
                
                return result
            except asyncio.TimeoutError:
                logger.error(f"LLM call for ask_memory timed out after 25s for user {supa_uid}.")
                return "I'm sorry, my connection to my thinking process was interrupted. Please try again."
            except ValueError as e:
                # Handle cases where the response is blocked or has no content
                if "finish_reason" in str(e):
                    logger.error(f"LLM response for ask_memory was blocked or invalid. Query: '{question}'. Error: {e}")
                    return "The response to your question could not be generated, possibly due to safety filters or an invalid request. Please try rephrasing your question."
                else:
                    logger.error(f"Error processing LLM response in ask_memory: {e}", exc_info=True)
                    return f"An error occurred while generating the response: {e}"
            except Exception as e:
                logger.error(f"Error in lightweight ask_memory: {e}", exc_info=True)
                return f"An unexpected error occurred in ask_memory: {e}"
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in lightweight ask_memory: {e}", exc_info=True)
        total_duration = time.time() - start_time
        logger.error(f"ask_memory: Failed after {total_duration:.2f}s for user {supa_uid}")
        return f"An unexpected error occurred in ask_memory: {e}"


@mcp.tool(description="Advanced memory search (temporarily disabled for stability)")
async def smart_memory_query(search_query: str) -> str:
    """
    Advanced memory search temporarily disabled due to performance issues.
    Use deep_memory_query or search_memory instead.
    """
    return "⚠️ Smart memory query is temporarily disabled for stability. Please use 'search_memory' or 'deep_memory_query' instead."


@mcp.tool(description="DEBUG: Directly fetch a point's payload from Qdrant.")
async def debug_get_qdrant_payload(point_id: str) -> str:
    """
    A temporary debugging tool to directly inspect a point's payload in Qdrant,
    bypassing the mem0 library's search function to verify if metadata is being written.
    """
    from qdrant_client import QdrantClient
    import os
    import json

    try:
        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        collection_name = os.getenv("MAIN_QDRANT_COLLECTION_NAME")

        if not all([qdrant_host, collection_name]):
            return "Error: Missing Qdrant environment variables for debugging."

        client = QdrantClient(
            url=f"https://{qdrant_host}",
            api_key=qdrant_api_key,
        )

        logger.info(f"🔍 DEBUG_QDRANT: Attempting to retrieve point '{point_id}' from collection '{collection_name}'")

        points = client.retrieve(
            collection_name=collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=False
        )

        if not points:
            return f"Error: Point with ID '{point_id}' not found in Qdrant collection '{collection_name}'."

        point_data = points[0]
        payload = point_data.payload

        logger.info(f"🔍 DEBUG_QDRANT: Successfully retrieved payload for point '{point_id}': {payload}")

        return json.dumps(payload, indent=2)

    except Exception as e:
        logger.error(f"Error in debug_get_qdrant_payload: {e}", exc_info=True)
        return f"An unexpected error occurred while debugging Qdrant: {str(e)}"


# @mcp.tool(description="Process documents into chunks for efficient retrieval. Run this after syncing new documents.")
async def chunk_documents() -> str:
    """
    Chunks all documents for the current user into smaller pieces for efficient search.
    This runs in the background and improves search performance.
    """
    # Lazy import
    from app.services.chunking_service import ChunkingService
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "Error: Supabase user_id not available in context"
    if not client_name:
        return "Error: client_name not available in context"
    
    try:
        db = SessionLocal()
        try:
            # Get user
            user, app = get_user_and_app(db, supa_uid, client_name)
            if not user or not app:
                return "Error: User or app not found"
            
            # Run chunking
            chunking_service = ChunkingService()
            processed = chunking_service.chunk_all_documents(db, str(user.id))
            
            return f"Successfully chunked {processed} documents. Your searches will now be faster and more accurate."
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in chunk_documents: {e}")
        return f"Error chunking documents: {str(e)}"


@mcp.tool(description="Test MCP connection and verify all systems are working")
async def test_connection() -> str:
    """
    Test the MCP connection and verify that all systems are working properly.
    This is useful for diagnosing connection issues.
    """
    # Lazy imports
    from app.utils.memory import get_memory_client
    from app.utils.gemini import GeminiService
    
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return "❌ Error: Supabase user_id not available in context. Connection may be broken."
    if not client_name:
        return "❌ Error: client_name not available in context. Connection may be broken."
    
    try:
        # Track test connection usage (only if private analytics available)
        _track_tool_usage('test_connection', {})
        
        db = SessionLocal()
        try:
            # Test database connection
            user, app = get_user_and_app(db, supa_uid, client_name)
            if not user or not app:
                return f"❌ Database connection failed: User or app not found for {supa_uid}/{client_name}"
            
            # Test memory client
            memory_client = get_memory_client()
            test_memories = memory_client.get_all(user_id=supa_uid, limit=1)
            
            # Test Gemini service
            gemini_service = GeminiService()
            
            # Build status report
            status_report = "🔍 MCP Connection Test Results:\n\n"
            status_report += f"✅ User ID: {supa_uid}\n"
            status_report += f"✅ Client: {client_name}\n"
            status_report += f"✅ Database: Connected (User: {user.email or 'No email'}, App: {app.name})\n"
            status_report += f"✅ Memory Client: Connected\n"
            status_report += f"✅ Gemini Service: Available\n"
            
            # Memory count
            if isinstance(test_memories, dict) and 'results' in test_memories:
                memory_count = len(test_memories['results'])
            elif isinstance(test_memories, list):
                memory_count = len(test_memories)
            else:
                memory_count = 0
            
            status_report += f"📊 Available memories: {memory_count}\n"
            
            # Document count
            doc_count = db.query(Document).filter(Document.user_id == user.id).count()
            status_report += f"📄 Available documents: {doc_count}\n"
            
            status_report += f"\n🎉 All systems operational! Connection is healthy."
            status_report += f"\n⏰ Test completed at: {datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            
            return status_report
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in test_connection: {e}", exc_info=True)
        return f"❌ Connection test failed: {str(e)}\n\n💡 Try restarting Claude Desktop if this persists."


@mcp_router.post("/messages/")
async def handle_post_message(request: Request):
    """
    Handles a single, stateless JSON-RPC message with dual-path authentication
    and selective tool exposure.
    """
    from app.auth import get_user_from_api_key_header
    
    api_key_auth_success = await get_user_from_api_key_header(request)
    
    if api_key_auth_success and hasattr(request.state, 'user') and request.state.user:
        is_api_key_path = True
        user_id_from_header = str(request.state.user.user_id)
        client_name_from_header = request.headers.get("x-client-name", "default_agent_app")
    else:
        is_api_key_path = False
        user_id_from_header = request.headers.get("x-user-id")
        client_name_from_header = request.headers.get("x-client-name")

    if not user_id_from_header or not client_name_from_header:
        return JSONResponse(status_code=400, content={"error": "Missing user authentication details"})
            
    user_token = user_id_var.set(user_id_from_header)
    client_token = client_name_var.set(client_name_from_header)
    
    try:
        body = await request.json()
        method_name = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if method_name == "initialize":
            # Adaptive protocol version - respond with client's version or highest we both support
            client_version = params.get("protocolVersion", "2024-11-05")
            
            # Protocol version negotiation
            if client_version == "2025-03-26":
                # Client supports latest - use advanced features
                protocol_version = "2025-03-26"
                capabilities = {
                    "tools": {"listChanged": False},
                    "logging": {},
                    "sampling": {}
                }
            else:
                # Client uses older version - maintain compatibility
                protocol_version = "2024-11-05"
                capabilities = {"tools": {}}
            
            response_payload = {
                "jsonrpc": "2.0", 
                "result": {
                    "protocolVersion": protocol_version, 
                    "capabilities": capabilities, 
                    "serverInfo": {
                        "name": "Jean Memory", 
                        "version": "1.0.0"
                    }
                }, 
                "id": request_id
            }
            return JSONResponse(content=response_payload)

        elif method_name == "tools/list":
            # Select the correct tool schema based on the client
            if client_name_from_header == "chatgpt":
                tools_to_show = get_chatgpt_tools_schema()
            elif is_api_key_path:
                tools_to_show = get_api_tools_schema()
            else:
                # This will cover the playground case and default
                tools_to_show = get_original_tools_schema()

            # 🚨 CRITICAL DEBUGGING: Log the exact schema being sent
            logger.info(f"🔍 TOOLS/LIST DEBUG - Client: {client_name_from_header}, is_api_key: {is_api_key_path}, Schema: {json.dumps(tools_to_show, indent=2)}")

            return JSONResponse(content={"jsonrpc": "2.0", "result": {"tools": tools_to_show}, "id": request_id})

        elif method_name == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            is_chatgpt = client_name_from_header == "chatgpt"
            
            # Handle ChatGPT-specific tools
            if is_chatgpt:
                if tool_name == "search":
                    try:
                        result = await handle_chatgpt_search(user_id_from_header, tool_args.get("query", ""))
                        return JSONResponse(content={"jsonrpc": "2.0", "result": result, "id": request_id})
                    except Exception as e:
                        return JSONResponse(content={"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": request_id})
                
                elif tool_name == "fetch":
                    try:
                        result = await handle_chatgpt_fetch(user_id_from_header, tool_args.get("id", ""))
                        return JSONResponse(content={"jsonrpc": "2.0", "result": result, "id": request_id})
                    except ValueError as e:
                        return JSONResponse(content={"jsonrpc": "2.0", "error": {"code": -32602, "message": str(e)}, "id": request_id})
                    except Exception as e:
                        return JSONResponse(content={"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": request_id})
                
                else:
                    return JSONResponse(status_code=404, content={"error": f"ChatGPT tool '{tool_name}' not found"})
            
            # Handle regular MCP tools for non-ChatGPT clients
            else:
                # Prevent API-only tools from being accessed by Claude Desktop
                if not is_api_key_path and tool_name == "search_memory_v2":
                     return JSONResponse(status_code=404, content={"error": f"Tool '{tool_name}' not found"})
                
                # Filter out complex parameters for Claude Desktop to keep interface simple
                if not is_api_key_path and tool_name == "search_memory":
                    # Remove tags_filter for Claude to prevent complexity issues
                    tool_args.pop("tags_filter", None)
                elif not is_api_key_path and tool_name == "add_memories":
                    # Remove tags for Claude to prevent complexity issues  
                    tool_args.pop("tags", None)
                
                tool_function = tool_registry.get(tool_name)
                if not tool_function:
                    return JSONResponse(status_code=404, content={"error": f"Tool '{tool_name}' not found"})
                try:
                    result = await tool_function(**tool_args)
                    return JSONResponse(content={"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": result}]}, "id": request_id})
                except TypeError as e:
                    return JSONResponse(status_code=422, content={"jsonrpc": "2.0", "error": {"code": -32602, "message": f"Invalid parameters for tool '{tool_name}': {e}"}, "id": request_id})

        elif method_name == "notifications/initialized":
            logger.info(f"Received initialization notification from client '{client_name_from_header}'")
            return JSONResponse(content={"status": "acknowledged"})
        
        elif method_name == "notifications/cancelled":
            logger.info(f"Received cancellation notification for request {params.get('requestId', 'unknown')}")
            return JSONResponse(content={"status": "acknowledged"})
        
        elif method_name == "resources/list":
            return JSONResponse(content={"jsonrpc": "2.0", "result": {"resources": []}, "id": request_id})
        
        elif method_name == "prompts/list":
            return JSONResponse(content={"jsonrpc": "2.0", "result": {"prompts": []}, "id": request_id})
        
        else:
            return JSONResponse(status_code=404, content={"error": f"Method '{method_name}' not found"})

    except Exception as e:
        logger.error(f"Error executing MCP method: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        user_id_var.reset(user_token)
        client_name_var.reset(client_token)

def get_original_tools_schema(include_annotations=False):
    """Returns the JSON schema for the original tools, optionally with 2025-03-26 annotations."""
    tools = [
        {
            "name": "ask_memory",
            "description": "FAST memory search for simple questions about the user's memories, thoughts, documents, or experiences",
            "inputSchema": {"type": "object", "properties": {"question": {"type": "string", "description": "A natural language question"}}, "required": ["question"]}
        },
        {
            "name": "add_memories",
            "description": "Store important information, preferences, facts, and observations about the user. Use this tool to remember key details learned during conversation.",
            "inputSchema": {"type": "object", "properties": {"text": {"type": "string", "description": "The information to store"}}, "required": ["text"]}
        },
        {
            "name": "search_memory", 
            "description": "Quick keyword-based search through the user's memories. Use this for fast lookups when you need specific information or when ask_memory might be too comprehensive.",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "query": {"type": "string", "description": "The search query"}, 
                    "limit": {"type": "integer", "description": "Max results"}
                }, 
                "required": ["query"]
            }
        },
        {
            "name": "list_memories",
            "description": "Browse through the user's stored memories to get an overview of what you know about them.",
            "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "description": "Max results"}}}
        },
        {
            "name": "deep_memory_query", 
            "description": "COMPREHENSIVE search that analyzes ALL user content including full documents and essays. Takes 30-60 seconds. Use sparingly for complex analysis.",
            "inputSchema": {"type": "object", "properties": {"search_query": {"type": "string", "description": "The complex query"}}, "required": ["search_query"]}
        }
    ]
    
    # Add annotations only for 2025-03-26 clients
    if include_annotations:
        annotations_map = {
            "ask_memory": {"readOnly": True, "sensitive": False, "destructive": False},
            "add_memories": {"readOnly": False, "sensitive": True, "destructive": False},
            "search_memory": {"readOnly": True, "sensitive": False, "destructive": False},
            "list_memories": {"readOnly": True, "sensitive": True, "destructive": False},
            "deep_memory_query": {"readOnly": True, "sensitive": False, "destructive": False, "expensive": True}
        }
        
        for tool in tools:
            if tool["name"] in annotations_map:
                tool["annotations"] = annotations_map[tool["name"]]
    
    return tools

def get_api_tools_schema():
    """Returns the JSON schema for API key users with 2025-03-26 annotations and enhanced features."""
    return [
        {
            "name": "ask_memory",
            "description": "FAST memory search for simple questions about the user's memories, thoughts, documents, or experiences",
            "inputSchema": {"type": "object", "properties": {"question": {"type": "string", "description": "A natural language question"}}, "required": ["question"]},
            "annotations": {
                "readOnly": True,
                "sensitive": False,
                "destructive": False
            }
        },
        {
            "name": "add_memories",
            "description": "Store important information with optional tag-based organization. Optionally, add a list of string tags for later filtering.",
            "inputSchema": {"type": "object", "properties": {"text": {"type": "string", "description": "The information to store"}, "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional list of tags"}}, "required": ["text"]},
            "annotations": {
                "readOnly": False,
                "sensitive": True,
                "destructive": False
            }
        },
        {
            "name": "search_memory_v2", 
            "description": "Quick keyword-based search with optional tag filtering. Enhanced version with metadata filtering capabilities.",
            "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "description": "The search query"}, "limit": {"type": "integer", "description": "Max results"}, "tags_filter": {"type": "array", "items": {"type": "string"}, "description": "Optional list of tags to filter by"}}, "required": ["query"]},
            "annotations": {
                "readOnly": True,
                "sensitive": False,
                "destructive": False
            }
        },
        {
            "name": "list_memories",
            "description": "Browse through the user's stored memories to get an overview of what you know about them.",
            "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "description": "Max results"}}},
            "annotations": {
                "readOnly": True,
                "sensitive": True,
                "destructive": False
            }
        },
        {
            "name": "deep_memory_query", 
            "description": "COMPREHENSIVE search that analyzes ALL user content including full documents and essays. Takes 30-60 seconds. Use sparingly for complex analysis.",
            "inputSchema": {"type": "object", "properties": {"search_query": {"type": "string", "description": "The complex query"}}, "required": ["search_query"]},
            "annotations": {
                "readOnly": True,
                "sensitive": False,
                "destructive": False,
                "expensive": True
            }
        }
    ]

# Core memory tools registry - simplified for better performance
tool_registry = {
    "add_memories": add_memories,
    "search_memory": search_memory,
    "search_memory_v2": search_memory_v2,
    "list_memories": list_memories,
    "ask_memory": ask_memory,
    "sync_substack_posts": sync_substack_posts,
    "deep_memory_query": deep_memory_query,
}

# Simple in-memory message queue for SSE connections
sse_message_queues = {}

# Add SSE endpoint for supergateway compatibility
@mcp_router.get("/{client_name}/sse/{user_id}")
async def handle_sse_connection(client_name: str, user_id: str, request: Request):
    """
    SSE endpoint for supergateway compatibility
    This allows npx supergateway to connect to the local development server
    """
    from fastapi.responses import StreamingResponse
    from fastapi import HTTPException
    import asyncio
    import json
    
    # Allow any user ID for production usage
    
    logger.info(f"SSE connection from {client_name} for user {user_id}")
    
    # Create a message queue for this connection
    connection_id = f"{client_name}_{user_id}"
    if connection_id not in sse_message_queues:
        sse_message_queues[connection_id] = asyncio.Queue()
    
    async def event_generator():
        try:
            # Send the endpoint event that supergateway expects
            yield f"event: endpoint\ndata: /mcp/{client_name}/messages/{user_id}\n\n"
            
            # CRITICAL FIX: Send an immediate heartbeat to satisfy impatient clients like ChatGPT
            # and prevent the connection from being dropped before the first message.
            yield f"event: heartbeat\ndata: {{'timestamp': '{datetime.datetime.now(datetime.UTC).isoformat()}'}}\n\n"

            # Main event loop
            while True:
                try:
                    # Check for messages with timeout
                    message = await asyncio.wait_for(
                        sse_message_queues[connection_id].get(), 
                        timeout=1.0
                    )
                    # Send the message through SSE
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat when no messages
                    yield f"event: heartbeat\ndata: {{'timestamp': '{datetime.datetime.now(datetime.UTC).isoformat()}'}}\n\n"
                    
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for {client_name}/{user_id}")
            # Clean up the message queue
            if connection_id in sse_message_queues:
                del sse_message_queues[connection_id]
            return
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

# Add messages endpoint for supergateway compatibility  
@mcp_router.post("/{client_name}/messages/{user_id}")
async def handle_sse_messages(client_name: str, user_id: str, request: Request):
    """
    Messages endpoint for supergateway compatibility
    This handles the actual MCP tool calls from supergateway
    """
    # Set context variables
    user_token = user_id_var.set(user_id)
    client_token = client_name_var.set(client_name)
    
    try:
        body = await request.json()
        method_name = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"Handling MCP method '{method_name}' for local user with params: {params}")

        response_payload = None
        
        # Handle MCP protocol methods (same as the existing /messages/ handler)
        if method_name == "initialize":
            # Adaptive protocol version - respond with client's version or highest we both support
            client_version = params.get("protocolVersion", "2024-11-05")
            
            # Protocol version negotiation
            if client_version == "2025-03-26":
                # Client supports latest - use advanced features
                protocol_version = "2025-03-26"
                capabilities = {
                    "tools": {"listChanged": False},
                    "logging": {},
                    "sampling": {}
                }
            else:
                # Client uses older version - maintain compatibility
                protocol_version = "2024-11-05"
                capabilities = {"tools": {}}
            
            response_payload = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": protocol_version,
                    "capabilities": capabilities,
                    "serverInfo": {
                        "name": "Jean Memory",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }
        
        elif method_name == "tools/list":
            # Detect ChatGPT client for local development
            if client_name == "chatgpt":
                tools = get_chatgpt_tools_schema()
            else:
                # Use the standardized schema function for consistency
                tools = get_original_tools_schema()
            
            response_payload = {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
        
        elif method_name == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            # Handle ChatGPT-specific tools
            if client_name == "chatgpt":
                if tool_name == "search":
                    try:
                        result = await handle_chatgpt_search(user_id, tool_args.get("query", ""))
                        response_payload = {
                            "jsonrpc": "2.0",
                            "result": result,
                            "id": request_id
                        }
                    except Exception as e:
                        response_payload = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            },
                            "id": request_id
                        }
                
                elif tool_name == "fetch":
                    try:
                        result = await handle_chatgpt_fetch(user_id, tool_args.get("id", ""))
                        response_payload = {
                            "jsonrpc": "2.0",
                            "result": result,
                            "id": request_id
                        }
                    except ValueError as e:
                        response_payload = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32602,
                                "message": str(e)
                            },
                            "id": request_id
                        }
                    except Exception as e:
                        response_payload = {
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32603,
                                "message": str(e)
                            },
                            "id": request_id
                        }
                
                else:
                    response_payload = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"ChatGPT tool '{tool_name}' not found"
                        },
                        "id": request_id
                    }
            else:
                # Handle regular tools for other clients
                tool_function = tool_registry.get(tool_name)
                if not tool_function:
                    response_payload = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found"
                        },
                        "id": request_id
                    }
                else:
                    # Execute the tool and await its result
                    result = await tool_function(**tool_args)
                    
                    response_payload = {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": result
                                }
                            ]
                        },
                        "id": request_id
                    }
        
        else:
            # Unknown method
            response_payload = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method_name}"
                },
                "id": request_id
            }
        
        # For Cursor, return JSON-RPC directly instead of SSE
        if client_name == "cursor":
            return JSONResponse(content=response_payload)

        connection_id = f"{client_name}_{user_id}"
        # Check if a persistent SSE connection exists for this user.
        # If it does, use the queue. Otherwise, return a direct response for stateless clients.
        if connection_id in sse_message_queues:
            await sse_message_queues[connection_id].put(response_payload)
            # CRITICAL FIX: Immediately send a heartbeat after the message to keep the connection alive.
            heartbeat_message = f"event: heartbeat\ndata: {{'timestamp': '{datetime.datetime.now(datetime.UTC).isoformat()}'}}\n\n"
            await sse_message_queues[connection_id].put(heartbeat_message)
            # Return empty response to close HTTP request
            return Response(status_code=204)
        else:
            # No active SSE connection, so return the full payload directly.
            # This handles local testing with tools like the OpenAI Playground.
            return JSONResponse(content=response_payload)
    
    except Exception as e:
        logger.error(f"Error in SSE messages handler: {e}")
        response_payload = {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            },
            "id": request_id if 'request_id' in locals() else None
        }
        
        # For Cursor, return JSON-RPC directly instead of SSE
        if client_name == "cursor":
            return JSONResponse(content=response_payload)

        connection_id = f"{client_name}_{user_id}"
        # Also check here for stateless vs. stateful error reporting
        if connection_id in sse_message_queues:
            # Send error through SSE queue
            await sse_message_queues[connection_id].put(response_payload)
            return Response(status_code=204)
        else:
            # Return error directly for stateless clients
            return JSONResponse(content=response_payload, status_code=500)
    
    finally:
        # Clean up context variables
        user_id_var.reset(user_token)
        client_name_var.reset(client_token)

def setup_mcp_server(app: FastAPI):
    """Setup MCP server with the FastAPI application"""
    # The new stateless /messages endpoint is the primary way to interact.
    # The old SSE endpoints are no longer needed with the Cloudflare Worker architecture.
    app.include_router(mcp_router)
    # RE-ENABLED: chorus_router for direct backend connection (bypasses Worker completely)
    app.include_router(chorus_router)
    logger.info("MCP server setup complete - stateless router and chorus router included.")

def get_chatgpt_tools_schema():
    """Returns ONLY search and fetch tools for ChatGPT clients - OpenAI compliant schemas"""
    return [
        {
            "name": "search",
            "description": "Search for memories and documents",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to find relevant memories and documents"
                    }
                },
                "required": ["query"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "structuredContent": {
                        "type": "object",
                        "properties": {
                            "results": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "title": {"type": "string"},
                                        "text": {"type": "string"},
                                        "url": {"type": ["string", "null"]}
                                    },
                                    "required": ["id", "title", "text"]
                                }
                            }
                        },
                        "required": ["results"]
                    },
                    "content": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "text": {"type": "string"}
                            },
                            "required": ["type", "text"]
                        }
                    }
                },
                "required": ["structuredContent", "content"]
            }
        },
        {
            "name": "fetch",
            "description": "Fetch memory or document by ID",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "ID of the memory or document to fetch"}
                },
                "required": ["id"]
            },
            "outputSchema": {
                "type": "object",
                "properties": {
                    "structuredContent": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "text": {"type": "string"},
                            "url": {"type": ["string", "null"]},
                            "metadata": {
                                "type": ["object", "null"],
                                "additionalProperties": {"type": "string"}
                            }
                        },
                        "required": ["id", "title", "text"]
                    },
                    "content": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "text": {"type": "string"}
                            },
                            "required": ["type", "text"]
                        }
                    }
                },
                "required": ["structuredContent", "content"]
            }
        }
    ]

async def handle_chatgpt_search(user_id: str, query: str):
    """
    DIRECT DEEP MEMORY APPROACH for ChatGPT search.
    
    Based on testing, ChatGPT can handle responses up to 47+ seconds, so we can 
    directly return comprehensive deep memory analysis instead of the hybrid approach.
    
    This gives ChatGPT immediate access to the full deep analysis without complexity.
    """
    try:
        # Track ChatGPT search usage (only if private analytics available)
        try:
            from app.utils.private_analytics import track_tool_usage
            track_tool_usage(
                user_id=user_id,
                tool_name='chatgpt_search',
                properties={
                    'client_name': 'chatgpt',
                    'query_length': len(query),
                    'is_chatgpt': True
                }
            )
        except (ImportError, Exception):
            pass
        
        # 🚀 DIRECT DEEP MEMORY TEST: Call deep analysis directly (testing timeout limits)
        logger.info(f"🧠 DIRECT: Starting deep memory analysis for ChatGPT query: '{query}' (user: {user_id})")
        
        deep_analysis_result = await _deep_memory_query_impl(
            search_query=query, 
            supa_uid=user_id, 
            client_name="chatgpt",
            memory_limit=10,  # Reasonable limit for comprehensive results
            chunk_limit=8,    # Good balance of speed vs depth
            include_full_docs=True
        )
        
        # 🎯 SCHEMA COMPLIANT: Return deep analysis as single article (fits required schema)
        citation_url = "https://jeanmemory.com"
        
        article = {
            "id": "1",  # Single comprehensive result
            "title": f"Deep Analysis: {query[:50]}{'...' if len(query) > 50 else ''}",
            "text": deep_analysis_result,  # 🧠 Full comprehensive deep analysis
            "url": citation_url
        }
        
        # sobannon's exact working response format
        search_response = {"results": [article]}
        
        logger.info(f"🧠 DIRECT: Deep memory analysis completed for query: '{query}' (user: {user_id})")
        
        # Return sobannon's exact format: structuredContent + content
        return {
            "structuredContent": search_response,  # For programmatic access
            "content": [
                {
                    "type": "text", 
                    "text": json.dumps(search_response)  # For display
                }
            ]
        }

    except Exception as e:
        logger.error(f"ChatGPT search error: {e}", exc_info=True)
        # Return empty results in the same format
        empty_response = {"results": []}
        return {
            "structuredContent": empty_response,
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(empty_response)
                }
            ]
        }

async def handle_chatgpt_fetch(user_id: str, memory_id: str):
    """
    DIRECT DEEP MEMORY: Simple fetch for single comprehensive analysis result
    """
    try:
        # Track ChatGPT fetch usage (only if private analytics available)
        try:
            from app.utils.private_analytics import track_tool_usage
            track_tool_usage(
                user_id=user_id,
                tool_name='chatgpt_fetch',
                properties={
                    'client_name': 'chatgpt',
                    'memory_id': memory_id,
                    'is_chatgpt': True
                }
            )
        except (ImportError, Exception):
            pass
        
        # With direct approach, we only have one result with ID "1" containing the full analysis
        if memory_id == "1":
            citation_url = "https://jeanmemory.com"
            
            article = {
                "id": "1",
                "title": "Deep Memory Analysis - Full Context",
                "text": "The comprehensive deep memory analysis was provided in the search results. This fetch confirms the analysis covers all available memories, documents, and insights about the query.",
                "url": citation_url,
                "metadata": {"type": "deep_analysis_confirmation"}
            }
            
            logger.info(f"🧠 DIRECT FETCH: Returning deep analysis confirmation for user {user_id}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(article)
                    }
                ],
                "structuredContent": article
            }
        else:
            # No other IDs exist in direct approach
            raise ValueError("unknown id")
            
    except Exception as e:
        logger.error(f"ChatGPT direct fetch error: {e}", exc_info=True)
        raise ValueError("unknown id")

# Add Streamable HTTP endpoint for API Playground compatibility
@mcp_router.post("/chatgpt/streamable/{user_id}")
async def handle_streamable_http(user_id: str, request: Request):
    """
    Streamable HTTP endpoint for OpenAI API Playground compatibility.
    This handles both tools/list and tools/call via POST to a single endpoint.
    """
    # Set context variables for ChatGPT client
    user_token = user_id_var.set(user_id)
    client_token = client_name_var.set("chatgpt")
    
    try:
        body = await request.json()
        method_name = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"Streamable HTTP request: {method_name} for user {user_id}")

        if method_name == "initialize":
            response_payload = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "Jean Memory",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }
        
        elif method_name == "tools/list":
            tools = get_chatgpt_tools_schema()
            response_payload = {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
        
        elif method_name == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "search":
                try:
                    result = await handle_chatgpt_search(user_id, tool_args.get("query", ""))
                    response_payload = {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id
                    }
                except Exception as e:
                    response_payload = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": str(e)},
                        "id": request_id
                    }
            
            elif tool_name == "fetch":
                try:
                    result = await handle_chatgpt_fetch(user_id, tool_args.get("id", ""))
                    response_payload = {
                        "jsonrpc": "2.0",
                        "result": result,
                        "id": request_id
                    }
                except ValueError as e:
                    response_payload = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32602, "message": str(e)},
                        "id": request_id
                    }
                except Exception as e:
                    response_payload = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": str(e)},
                        "id": request_id
                    }
            
            else:
                response_payload = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                    "id": request_id
                }
        
        else:
            response_payload = {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method '{method_name}' not found"},
                "id": request_id
            }

        return JSONResponse(content=response_payload)

    except Exception as e:
        logger.error(f"Error in streamable HTTP handler: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_id if 'request_id' in locals() else None
            }
        )
    finally:
        user_id_var.reset(user_token)
        client_name_var.reset(client_token)

async def _chatgpt_fetch_memory_by_id(user_id: str, memory_id: str):
    """
    A dedicated and robust fetch implementation for the ChatGPT client.
    It reliably finds a memory by its vector ID using a get_all fallback,
    ensuring it does not interfere with other tool functionalities.
    """
    from app.utils.memory import get_memory_client
    memory_client = get_memory_client()

    # Use get_all() and iterate in Python, as search(query=<id>) is unreliable.
    all_memories_result = memory_client.get_all(user_id=user_id, limit=2000) # High limit for thoroughness

    memories_list = []
    if isinstance(all_memories_result, dict) and 'results' in all_memories_result:
        memories_list = all_memories_result['results']
    elif isinstance(all_memories_result, list):
        memories_list = all_memories_result

    # Look for the exact ID match in the full list
    for mem in memories_list:
        if isinstance(mem, dict) and mem.get('id') == memory_id:
            # Found it. Return the full dictionary.
            return {
                "id": mem.get('id'),
                "content": mem.get('memory', mem.get('content', 'No content available')),
                "metadata": mem.get('metadata', {}),
                "created_at": mem.get('created_at'),
                "updated_at": mem.get('updated_at'),
                "score": mem.get('score'),
                "source": "mem0_vector_store"
            }
    
    # If we get here, the memory was not found.
    return None

# Simple in-memory cache for deep analyses
deep_analysis_cache: Dict[str, Dict] = {}
DEEP_CACHE_TTL = 1800  # 30 minutes

# New: Session-based deep analysis cache for ChatGPT hybrid approach
chatgpt_deep_analysis_cache: Dict[str, Dict] = {}

async def trigger_background_deep_analysis(user_id: str, query: str, session_key: str):
    """
    Trigger background deep memory analysis for ChatGPT hybrid approach.
    This runs after search returns, so ChatGPT gets immediate results
    while comprehensive analysis prepares for fetch calls.
    
    CRITICAL: This function runs completely independently and never blocks the search response.
    """
    try:
        logger.info(f"🧠 DEEP ANALYSIS: Starting background analysis for user {user_id}, query: '{query}'")
        
        # 🚀 CRITICAL FIX: Add small delay to ensure search response is sent first
        await asyncio.sleep(0.1)  # Let search response complete first
        
        # Use the existing deep memory implementation with conservative limits for faster processing
        analysis_result = await _deep_memory_query_impl(
            search_query=query, 
            supa_uid=user_id, 
            client_name="chatgpt",
            memory_limit=8,   # Reduced for faster processing
            chunk_limit=5,    # Reduced for faster processing  
            include_full_docs=True
        )
        
        # Cache the analysis for this session
        chatgpt_deep_analysis_cache[session_key] = {
            "query": query,
            "analysis": analysis_result,
            "status": "completed",
            "timestamp": datetime.datetime.now(datetime.UTC),
            "user_id": user_id
        }
        
        logger.info(f"🧠 DEEP ANALYSIS: Completed and cached for session {session_key}")
        
    except Exception as e:
        logger.error(f"🧠 DEEP ANALYSIS: Failed for session {session_key}: {e}")
        # Store error result so fetch doesn't wait indefinitely
        chatgpt_deep_analysis_cache[session_key] = {
            "query": query,
            "analysis": f"Deep analysis encountered an error: {str(e)}. Falling back to basic memory search.",
            "status": "error",
            "timestamp": datetime.datetime.now(datetime.UTC),
            "user_id": user_id,
            "error": True
        }

def cleanup_old_deep_analysis_cache():
    """Clean up old deep analysis cache entries"""
    current_time = datetime.datetime.now(datetime.UTC)
    expired_keys = []
    
    for session_key, data in chatgpt_deep_analysis_cache.items():
        if (current_time - data["timestamp"]).total_seconds() > DEEP_CACHE_TTL:
            expired_keys.append(session_key)
    
    for key in expired_keys:
        del chatgpt_deep_analysis_cache[key]
    
    if expired_keys:
        logger.info(f"🧠 DEEP ANALYSIS: Cleaned up {len(expired_keys)} expired cache entries")

# Dedicated router for Chorus for stability and isolation
chorus_router = APIRouter(prefix="/mcp/chorus")

# Minimal SSE endpoint for Chorus (for mcp-remote compatibility)
@chorus_router.get("/sse/{user_id}")
async def handle_chorus_sse(user_id: str, request: Request):
    """
    Minimal SSE endpoint that just provides the messages endpoint
    Chorus will use HTTP responses, not actual SSE streaming
    """
    from fastapi.responses import StreamingResponse
    
    async def simple_sse():
        # Just send the endpoint event and close
        yield f"event: endpoint\ndata: /mcp/chorus/messages/{user_id}\n\n"
    
    return StreamingResponse(
        simple_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# Chorus messages endpoint - returns JSON-RPC directly via HTTP (no SSE)
@chorus_router.post("/messages/{user_id}")
async def handle_chorus_messages(user_id: str, request: Request):
    """
    Direct HTTP JSON-RPC endpoint for Chorus - bypasses Worker completely
    Returns JSON-RPC responses directly via HTTP without SSE
    """
    # Set context variables
    user_token = user_id_var.set(user_id)
    client_token = client_name_var.set("chorus")
    
    try:
        body = await request.json()
        method_name = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"Chorus direct HTTP: {method_name} for user {user_id}")

        # Handle MCP methods directly (same logic as main /messages/ endpoint)
        if method_name == "initialize":
            response_payload = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "Jean Memory",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }
        
        elif method_name == "tools/list":
            tools = get_original_tools_schema()
            response_payload = {
                "jsonrpc": "2.0",
                "result": {"tools": tools},
                "id": request_id
            }
        
        elif method_name == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            tool_function = tool_registry.get(tool_name)
            if not tool_function:
                response_payload = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                    "id": request_id
                }
            else:
                try:
                    result = await tool_function(**tool_args)
                    response_payload = {
                        "jsonrpc": "2.0",
                        "result": {"content": [{"type": "text", "text": result}]},
                        "id": request_id
                    }
                except Exception as e:
                    response_payload = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": f"Tool execution failed: {str(e)}"},
                        "id": request_id
                    }
        
        else:
            response_payload = {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method '{method_name}' not found"},
                "id": request_id
            }

        # Return JSON-RPC directly via HTTP (no SSE)
        return JSONResponse(content=response_payload)

    except Exception as e:
        logger.error(f"Error in Chorus direct HTTP handler: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_id if 'request_id' in locals() else None
            }
        )
    finally:
        user_id_var.reset(user_token)
        client_name_var.reset(client_token)
