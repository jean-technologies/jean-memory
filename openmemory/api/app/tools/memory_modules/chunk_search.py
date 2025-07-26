"""
Document chunk search operations.
Provides deep search capabilities for Substack and other long-form content.
"""

import logging
from typing import List, Dict, Optional, Set
from sqlalchemy import func, text, or_
from sqlalchemy.orm import Session

from app.models import DocumentChunk, Document, Memory, MemoryState
from app.database import SessionLocal

logger = logging.getLogger(__name__)


async def search_document_chunks(
    query: str,
    user_id: str,
    document_ids: Optional[List[str]] = None,
    limit_per_doc: int = 3,
    total_limit: int = 15
) -> List[Dict]:
    """
    Fast text search through document chunks using ILIKE (fallback from full-text search).
    
    Args:
        query: Search query
        user_id: User ID for filtering
        document_ids: Optional list of document IDs to search within
        limit_per_doc: Max chunks per document
        total_limit: Total max chunks to return
        
    Returns:
        List of chunk results formatted as memory-like objects
    """
    db = SessionLocal()
    try:
        # Build base query
        chunks_query = db.query(DocumentChunk).join(Document)
        
        # Filter by user
        chunks_query = chunks_query.filter(Document.user_id == user_id)
        
        # Filter by document IDs if provided
        if document_ids:
            chunks_query = chunks_query.filter(Document.id.in_(document_ids))
        
        # Skip full-text search entirely for now - use ILIKE directly
        # TODO: Fix PostgreSQL full-text search setup in production
        logger.info(f"Using ILIKE search for query: {query}")
        
        # Split query into words for better ILIKE matching
        query_words = query.lower().split()
        ilike_conditions = []
        
        for word in query_words[:5]:  # Limit to first 5 words
            if len(word) > 2:  # Skip very short words
                ilike_conditions.append(DocumentChunk.content.ilike(f"%{word}%"))
        
        if ilike_conditions:
            chunks = chunks_query.filter(
                or_(*ilike_conditions)
            ).limit(total_limit).all()
        else:
            chunks = []
        
        logger.info(f"ILIKE search found {len(chunks)} chunks")
        
        # Format chunks as memory-like objects
        formatted_chunks = []
        doc_chunk_counts = {}  # Track chunks per document
        
        for chunk in chunks:
            doc_id = str(chunk.document_id)
            
            # Enforce per-document limit
            if doc_chunk_counts.get(doc_id, 0) >= limit_per_doc:
                continue
                
            doc_chunk_counts[doc_id] = doc_chunk_counts.get(doc_id, 0) + 1
            
            # Get document details
            document = chunk.document
            
            formatted_chunks.append({
                'id': f"chunk_{chunk.id}",
                'content': chunk.content,
                'created_at': chunk.created_at.isoformat() if chunk.created_at else None,
                'categories': [],  # Chunks don't have categories
                'metadata': {
                    'source': 'document_chunk',
                    'document_id': str(document.id),
                    'document_title': document.title,
                    'document_type': document.document_type,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.metadata_.get('total_chunks', 0) if chunk.metadata_ else 0,
                    'document_url': document.source_url
                },
                'score': 0.85,  # Fixed score for text matches (lower than vector matches)
                'is_chunk': True  # Flag to identify chunks in results
            })
        
        return formatted_chunks
        
    except Exception as e:
        logger.error(f"Error searching document chunks: {e}")
        # Rollback the transaction to prevent cascading errors
        try:
            db.rollback()
        except:
            pass
        return []
    finally:
        try:
            db.close()
        except:
            pass


def extract_document_ids_from_results(search_results: List[Dict]) -> Set[str]:
    """
    Extract document IDs from vector search results.
    
    Args:
        search_results: Results from vector search
        
    Returns:
        Set of document IDs that have associated documents
    """
    document_ids = set()
    
    for result in search_results:
        metadata = result.get('metadata', {})
        
        # Check for document_id in metadata
        doc_id = metadata.get('document_id')
        if doc_id:
            document_ids.add(str(doc_id))
        
        # Also check for substack-specific metadata
        if metadata.get('source_app') == 'substack' and metadata.get('type') == 'document_summary':
            if doc_id:
                document_ids.add(str(doc_id))
    
    return document_ids


def merge_search_results(
    vector_results: List[Dict],
    chunk_results: List[Dict],
    query: str,
    max_results: int = 50
) -> List[Dict]:
    """
    Merge and re-rank vector search results with chunk search results.
    
    Strategy:
    1. Keep all high-score vector results (>0.8)
    2. Interleave chunk results with lower-score vector results
    3. Remove duplicates based on content similarity
    
    Args:
        vector_results: Results from vector search
        chunk_results: Results from chunk search
        query: Original search query
        max_results: Maximum total results to return
        
    Returns:
        Merged and ranked results
    """
    # Separate high and low confidence vector results
    high_confidence = [r for r in vector_results if r.get('score', 0) > 0.8]
    low_confidence = [r for r in vector_results if r.get('score', 0) <= 0.8]
    
    # Start with high confidence results
    merged = high_confidence.copy()
    
    # Interleave chunks with low confidence results
    chunk_idx = 0
    low_idx = 0
    
    while len(merged) < max_results and (chunk_idx < len(chunk_results) or low_idx < len(low_confidence)):
        # Add a chunk result if available
        if chunk_idx < len(chunk_results) and len(merged) < max_results:
            chunk = chunk_results[chunk_idx]
            
            # Check for content duplication
            is_duplicate = False
            chunk_content_lower = chunk['content'].lower()[:200]  # Compare first 200 chars
            
            for existing in merged:
                existing_content_lower = existing['content'].lower()[:200]
                if chunk_content_lower in existing_content_lower or existing_content_lower in chunk_content_lower:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(chunk)
                
            chunk_idx += 1
        
        # Add a low confidence result if available
        if low_idx < len(low_confidence) and len(merged) < max_results:
            merged.append(low_confidence[low_idx])
            low_idx += 1
    
    # Add source diversity metadata
    for result in merged:
        if result.get('is_chunk'):
            result['source_type'] = 'chunk'
        else:
            result['source_type'] = 'vector'
    
    return merged[:max_results]


async def should_trigger_deep_search(
    query: str,
    initial_results: List[Dict],
    user_preferences: Optional[Dict] = None
) -> bool:
    """
    Determine if deep search should be triggered automatically.
    
    Triggers when:
    - Low confidence results (all scores < 0.7)
    - Query contains deep search keywords
    - User has Substack content and few results
    
    Args:
        query: Search query
        initial_results: Initial vector search results
        user_preferences: Optional user preferences
        
    Returns:
        True if deep search should be triggered
    """
    # Check for explicit deep search keywords
    deep_keywords = ['details', 'specifically', 'exact', 'full', 'complete', 'entire']
    query_lower = query.lower()
    
    if any(keyword in query_lower for keyword in deep_keywords):
        logger.info("Deep search triggered by keyword")
        return True
    
    # Check for low confidence results
    if initial_results:
        max_score = max(r.get('score', 0) for r in initial_results)
        if max_score < 0.7:
            logger.info(f"Deep search triggered by low confidence (max score: {max_score})")
            return True
    
    # Check if results contain Substack content
    has_substack = any(
        r.get('metadata', {}).get('source_app') == 'substack' 
        for r in initial_results
    )
    
    # If few results and user has Substack content
    if len(initial_results) < 3 and has_substack:
        logger.info("Deep search triggered by few results with Substack content")
        return True
    
    return False