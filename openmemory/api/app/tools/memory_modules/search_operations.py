"""
Memory search operations module.
Contains all memory search and query functionality.
"""

import logging
import asyncio
from typing import Optional, List
from sqlalchemy import text

from app.context import user_id_var, client_name_var
from app.database import SessionLocal
from app.models import Memory, MemoryState, User
from app.utils.db import get_user_and_app
from app.config.memory_limits import MEMORY_LIMITS
from app.utils.decorators import retry_on_exception
from .utils import safe_json_dumps, track_tool_usage, format_memory_response, format_error_response
from .chunk_search import (
    search_document_chunks, 
    extract_document_ids_from_results,
    merge_search_results,
    should_trigger_deep_search
)

logger = logging.getLogger(__name__)


@retry_on_exception(retries=3, delay=1, backoff=2, exceptions=(ConnectionError,))
async def search_memory(query: str, limit: int = None, tags_filter: Optional[List[str]] = None, deep_search: bool = False) -> str:
    """
    Search the user's memory for memories that match the query.
    Returns memories that are semantically similar to the query.
    
    Args:
        query: The search term or phrase to look for
        limit: Maximum number of results to return (default: 10, max: 50) 
        tags_filter: Optional list of tags to filter results (e.g., ["work", "project-alpha"])
                    Only memories containing ALL specified tags will be returned.
        deep_search: Enable deep search through document chunks (useful for Substack content)
    
    Returns:
        JSON string containing list of matching memories with their content and metadata
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid:
        return format_error_response("Supabase user_id not available in context", "search_memory")
    if not client_name:
        return format_error_response("client_name not available in context", "search_memory")
    
    # Use configured limits
    if limit is None:
        limit = MEMORY_LIMITS.search_default
    limit = min(max(1, limit), MEMORY_LIMITS.search_max)
    
    try:
        # Track search usage (only if private analytics available)
        track_tool_usage('search_memory', {
            'query_length': len(query),
            'limit': limit,
            'has_tags_filter': bool(tags_filter),
            'deep_search': deep_search
        })
        
        # Add timeout to prevent hanging
        return await asyncio.wait_for(
            _search_memory_unified_impl(query, supa_uid, client_name, limit, tags_filter, deep_search), 
            timeout=30.0 if not deep_search else 45.0  # More time for deep search
        )
    except asyncio.TimeoutError:
        return format_error_response("Search timed out. Please try a simpler query.", "search_memory")
    except Exception as e:
        logger.error(f"Error in search_memory MCP tool: {e}", exc_info=True)
        return format_error_response(f"Error searching memory: {e}", "search_memory")


async def _search_memory_unified_impl(query: str, supa_uid: str, client_name: str, 
                                    limit: int = 10, tags_filter: Optional[List[str]] = None,
                                    deep_search: bool = False) -> str:
    """Unified implementation that supports both basic search, tag filtering, and deep search"""
    from app.utils.memory import get_async_memory_client
    
    memory_client = await get_async_memory_client()
    db = SessionLocal()
    
    try:
        user, app = get_user_and_app(db, supa_uid, client_name)
        
        # Search using the memory client
        search_result = await memory_client.search(query, user_id=supa_uid, limit=limit)
        
        # Process results - handle different return formats from mem0/graphiti
        search_results = []
        if isinstance(search_result, dict) and 'results' in search_result:
            search_results = search_result['results']
        elif isinstance(search_result, list):
            search_results = search_result
        elif search_result:
            # Handle other formats
            logger.warning(f"Unexpected search result format: {type(search_result)}")
            search_results = []
        
        if not search_results:
            return format_memory_response([], 0, query)
        
        # Format Jean Memory V2 results directly without SQL lookup
        formatted_memories = []
        for result in search_results:
            if isinstance(result, dict):
                # Extract content from different possible fields
                content = result.get('memory', result.get('content', result.get('text', '')))
                
                # Apply tag filtering if specified
                if tags_filter:
                    result_tags = result.get('categories', [])
                    if not all(tag.lower() in [t.lower() for t in result_tags] for tag in tags_filter):
                        continue
                
                formatted_memories.append({
                    'id': str(result.get('id', '')),
                    'content': content,
                    'created_at': result.get('created_at', result.get('timestamp', '')),
                    'categories': result.get('categories', []),
                    'metadata': result.get('metadata', {}),
                    'score': result.get('score', 0.0)
                })
            else:
                logger.warning(f"Unexpected result format in search: {type(result)}")
                continue
        
        # Handle deep search if requested or triggered automatically
        if deep_search or await should_trigger_deep_search(query, formatted_memories):
            logger.info(f"Deep search activated for query: {query}")
            
            # Extract document IDs from vector results
            document_ids = extract_document_ids_from_results(formatted_memories)
            
            if document_ids:
                logger.info(f"Searching chunks for {len(document_ids)} documents")
                
                # Search through document chunks
                chunk_results = await search_document_chunks(
                    query=query,
                    user_id=supa_uid,
                    document_ids=list(document_ids),
                    limit_per_doc=3,
                    total_limit=15
                )
                
                if chunk_results:
                    logger.info(f"Found {len(chunk_results)} relevant chunks")
                    
                    # Merge vector and chunk results
                    formatted_memories = merge_search_results(
                        vector_results=formatted_memories,
                        chunk_results=chunk_results,
                        query=query,
                        max_results=limit
                    )
                    
                    # Add deep search metadata to response
                    for memory in formatted_memories:
                        if memory.get('source_type') == 'chunk':
                            memory['metadata']['deep_search'] = True
        
        return format_memory_response(formatted_memories, len(formatted_memories), query)
        
    except Exception as e:
        logger.error(f"Error in search implementation: {e}", exc_info=True)
        return format_error_response(f"Search failed: {str(e)}", "search_memory")
    finally:
        db.close()


async def search_memory_v2(query: str, limit: int = None, tags_filter: Optional[List[str]] = None, deep_search: bool = False) -> str:
    """
    Enhanced memory search with improved ranking and filtering.
    Now includes deep search capability for document chunks.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid or not client_name:
        return format_error_response("Missing user context", "search_memory_v2")
    
    if limit is None:
        limit = MEMORY_LIMITS.search_default
    limit = min(max(1, limit), MEMORY_LIMITS.search_max)
    
    try:
        track_tool_usage('search_memory_v2', {
            'query_length': len(query),
            'limit': limit,
            'has_tags_filter': bool(tags_filter),
            'deep_search': deep_search
        })
        
        return await asyncio.wait_for(
            _search_memory_v2_impl(query, supa_uid, client_name, limit, tags_filter, deep_search),
            timeout=30.0 if not deep_search else 45.0
        )
    except asyncio.TimeoutError:
        return format_error_response("Search timed out", "search_memory_v2")
    except Exception as e:
        logger.error(f"Error in search_memory_v2: {e}", exc_info=True)
        return format_error_response(f"Enhanced search failed: {e}", "search_memory_v2")


async def _search_memory_v2_impl(query: str, supa_uid: str, client_name: str,
                               limit: int = 10, tags_filter: Optional[List[str]] = None,
                               deep_search: bool = False) -> str:
    """Enhanced search implementation with better ranking"""
    from app.utils.memory import get_async_memory_client
    
    try:
        # Use the optimized V2 client
        memory_client = await get_async_memory_client()
        
        # Perform enhanced search
        search_result = await memory_client.search(
            query=query,
            user_id=supa_uid,
            limit=limit,
            filters={"tags": tags_filter} if tags_filter else None
        )
        
        # Process results - handle different return formats from mem0/graphiti
        search_results = []
        if isinstance(search_result, dict) and 'results' in search_result:
            search_results = search_result['results']
        elif isinstance(search_result, list):
            search_results = search_result
        elif search_result:
            # Handle other formats
            logger.warning(f"Unexpected search result format: {type(search_result)}")
            search_results = []
        
        if not search_results:
            return format_memory_response([], 0, query)
        
        # Format and return results
        formatted_results = []
        for result in search_results:
            if isinstance(result, dict):
                formatted_results.append({
                    'id': result.get('id'),
                    'content': result.get('memory', result.get('content', '')),
                    'score': result.get('score', 0.0),
                    'categories': result.get('categories', []),
                    'created_at': result.get('created_at', ''),
                    'metadata': result.get('metadata', {})
                })
            else:
                logger.warning(f"Unexpected result format in search: {type(result)}")
                continue
        
        # Handle deep search if requested
        if deep_search or await should_trigger_deep_search(query, formatted_results):
            logger.info(f"Deep search activated for v2 query: {query}")
            
            # Extract document IDs from vector results
            document_ids = extract_document_ids_from_results(formatted_results)
            
            if document_ids:
                logger.info(f"Searching chunks for {len(document_ids)} documents")
                
                # Search through document chunks
                chunk_results = await search_document_chunks(
                    query=query,
                    user_id=supa_uid,
                    document_ids=list(document_ids),
                    limit_per_doc=3,
                    total_limit=15
                )
                
                if chunk_results:
                    logger.info(f"Found {len(chunk_results)} relevant chunks")
                    
                    # Merge vector and chunk results
                    formatted_results = merge_search_results(
                        vector_results=formatted_results,
                        chunk_results=chunk_results,
                        query=query,
                        max_results=limit
                    )
                    
                    # Add deep search metadata
                    for result in formatted_results:
                        if result.get('source_type') == 'chunk':
                            result['metadata']['deep_search'] = True
        
        return format_memory_response(formatted_results, len(formatted_results), query)
        
    except Exception as e:
        logger.error(f"Error in enhanced search: {e}", exc_info=True)
        return format_error_response(f"Enhanced search failed: {str(e)}", "search_memory_v2")


async def ask_memory(question: str) -> str:
    """
    Ask a question about the user's memories and get an AI-generated response.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid or not client_name:
        return format_error_response("Missing user context", "ask_memory")
    
    try:
        track_tool_usage('ask_memory', {'question_length': len(question)})
        
        return await asyncio.wait_for(
            _lightweight_ask_memory_impl(question, supa_uid, client_name),
            timeout=45.0
        )
    except asyncio.TimeoutError:
        return format_error_response("Question processing timed out", "ask_memory")
    except Exception as e:
        logger.error(f"Error in ask_memory: {e}", exc_info=True)
        return format_error_response(f"Failed to process question: {e}", "ask_memory")


async def _lightweight_ask_memory_impl(question: str, supa_uid: str, client_name: str) -> str:
    """Lightweight ask_memory implementation for quick answers using mem0 + graphiti search"""
    from app.utils.memory import get_async_memory_client
    from mem0.llms.openai import OpenAILLM
    from mem0.configs.llms.base import BaseLlmConfig
    from app.database import SessionLocal
    from app.utils.db import get_or_create_user
    
    import time
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
                return format_error_response("User ID validation failed. Security issue detected.", "ask_memory")

            # Initialize services
            memory_client = await get_async_memory_client()
            llm = OpenAILLM(config=BaseLlmConfig(model="gpt-4o-mini"))
            
            # 1. Initial vector search
            search_start_time = time.time()
            logger.info(f"ask_memory: Starting memory search for user {supa_uid}")
            
            # Call async memory client directly - this uses Jean Memory V2 mem0 + graphiti search
            search_result = await memory_client.search(query=question, user_id=supa_uid, limit=10)
            
            # Process initial results
            initial_memories = []
            if isinstance(search_result, dict) and 'results' in search_result:
                initial_memories = search_result['results']
            elif isinstance(search_result, list):
                initial_memories = search_result
            
            # Check if we should do deep search (for questions about detailed content)
            has_substack = any(
                m.get('metadata', {}).get('source_app') == 'substack' 
                for m in initial_memories
            )
            
            # Trigger deep search for questions that need detailed content
            should_deep_search = (
                has_substack and (
                    'detail' in question.lower() or
                    'specific' in question.lower() or
                    'exactly' in question.lower() or
                    'full' in question.lower() or
                    len(initial_memories) < 3
                )
            )
            
            if should_deep_search:
                logger.info("ask_memory: Triggering deep search for detailed content")
                
                # Extract document IDs
                document_ids = extract_document_ids_from_results(initial_memories)
                
                if document_ids:
                    # Search chunks for more detailed content
                    chunk_results = await search_document_chunks(
                        query=question,
                        user_id=supa_uid,
                        document_ids=list(document_ids),
                        limit_per_doc=3,
                        total_limit=10
                    )
                    
                    # Combine results for LLM context
                    if chunk_results:
                        # Add chunks to the search results
                        search_result = {
                            'results': initial_memories + chunk_results
                        }

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
            
            # 2. Generate conversational response using LLM
            if clean_memories:
                memory_context = "\n".join(clean_memories)
                prompt = f"""Based on the following memories, answer the question: "{question}"

Relevant memories:
{memory_context}

Provide a helpful and conversational answer based on the memories above. If the memories don't contain enough information to answer the question, say so."""
            else:
                prompt = f"""The user asked: "{question}"

No relevant memories were found. Provide a helpful response indicating that no relevant information was found in their memory."""
            
            synthesis_start_time = time.time()
            response = llm.generate_response([{"role": "user", "content": prompt}])
            synthesis_duration = time.time() - synthesis_start_time
            
            total_duration = time.time() - start_time
            
            logger.info(f"ask_memory: Completed for user {supa_uid} in {total_duration:.2f}s (search: {search_duration:.2f}s, synthesis: {synthesis_duration:.2f}s)")
            
            return safe_json_dumps({
                "status": "success",
                "question": question,
                "answer": response,
                "memories_found": len(memories),
                "search_duration": round(search_duration, 2),
                "total_duration": round(total_duration, 2)
            })
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Error in ask memory implementation: {e}", exc_info=True)
        return format_error_response(f"Failed to generate answer: {str(e)}", "ask_memory")


async def smart_memory_query(search_query: str) -> str:
    """
    Intelligent memory query that combines search and Q&A capabilities.
    """
    supa_uid = user_id_var.get(None)
    client_name = client_name_var.get(None)
    
    if not supa_uid or not client_name:
        return format_error_response("Missing user context", "smart_memory_query")
    
    try:
        track_tool_usage('smart_memory_query', {'query_length': len(search_query)})
        
        # First try semantic search
        search_results = await _search_memory_unified_impl(
            search_query, supa_uid, client_name, limit=5
        )
        
        # If search results are good, return them
        # Otherwise, try ask_memory for more conversational response
        try:
            search_data = safe_json_dumps(search_results)
            if '"memories": []' not in search_data:
                return search_results
        except:
            pass
        
        # Fallback to conversational Q&A
        return await _lightweight_ask_memory_impl(search_query, supa_uid, client_name)
        
    except Exception as e:
        logger.error(f"Error in smart_memory_query: {e}", exc_info=True)
        return format_error_response(f"Smart query failed: {e}", "smart_memory_query")