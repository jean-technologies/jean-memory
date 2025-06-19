"""
Unified Memory System Integration

This module provides a unified interface for memory operations that combines:
- Mem0 for vector-based semantic search and entity extraction
- Graphiti for temporal graph-based relationship modeling

The system is designed to work in both local development (with local Neo4j/Qdrant)
and production environments (with cloud services).
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv

from app.settings import config

logger = logging.getLogger(__name__)

# Conditional imports for unified memory system
try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    GRAPHITI_AVAILABLE = True
except ImportError:
    logger.warning("Graphiti not available. Unified memory features will be limited.")
    GRAPHITI_AVAILABLE = False

# Import existing memory client
from app.utils.memory import get_memory_client


class UnifiedMemorySystem:
    """
    Unified Memory System that combines Mem0 and Graphiti for enhanced memory capabilities.
    
    This system provides:
    - Vector-based semantic search via Mem0
    - Graph-based entity and relationship modeling via Mem0's graph store
    - Temporal graph relationships via Graphiti
    - Unified search across both systems
    """
    
    def __init__(self, use_unified: bool = None):
        """
        Initialize the Unified Memory System.
        
        Args:
            use_unified: Whether to use unified memory features. If None, determined by config.
        """
        self.use_unified = use_unified if use_unified is not None else self._should_use_unified()
        self.mem0_client = None
        self.graphiti_client = None
        self.is_graphiti_initialized = False
        
        # Always initialize Mem0 (our existing system)
        self.mem0_client = get_memory_client()
        
        # Initialize Graphiti only if unified memory is enabled and available
        if self.use_unified and GRAPHITI_AVAILABLE:
            self._init_graphiti()
    
    def _should_use_unified(self) -> bool:
        """Determine if unified memory should be used based on configuration."""
        return (
            config.is_local_development and 
            os.getenv("USE_UNIFIED_MEMORY", "false").lower() == "true"
        )
    
    def _init_graphiti(self):
        """Initialize Graphiti client for temporal graph capabilities."""
        try:
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD")
            
            if not neo4j_password:
                logger.warning("NEO4J_PASSWORD not set. Graphiti initialization may fail.")
                return
            
            logger.info(f"Initializing Graphiti with Neo4j URI: {neo4j_uri}")
            self.graphiti_client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
            
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            self.graphiti_client = None
    
    async def async_init(self):
        """Perform asynchronous initialization, particularly for Graphiti indices."""
        if self.use_unified and self.graphiti_client and not self.is_graphiti_initialized:
            try:
                logger.info("Building Graphiti indices and constraints...")
                await self.graphiti_client.build_indices_and_constraints()
                self.is_graphiti_initialized = True
                logger.info("Graphiti initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Graphiti indices: {e}")
    
    async def add_memory(
        self, 
        content: str, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Add a memory to both Mem0 and Graphiti (if enabled).
        
        Args:
            content: The memory content/text
            user_id: User identifier
            metadata: Optional metadata dictionary
            timestamp: Optional timestamp for the memory (defaults to now)
            
        Returns:
            Dictionary with results from both systems
        """
        if metadata is None:
            metadata = {}
        
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        results = {
            "mem0_result": None,
            "graphiti_result": None,
            "unified": self.use_unified
        }
        
        # Add to Mem0 (always)
        try:
            logger.info(f"Adding to Mem0: '{content[:50]}...' for user_id '{user_id}'")
            
            # Run Mem0 add in executor since it's synchronous
            loop = asyncio.get_event_loop()
            mem0_messages = [{"role": "user", "content": content}]
            
            mem0_result = await loop.run_in_executor(
                None, 
                lambda: self.mem0_client.add(mem0_messages, user_id=user_id, metadata=metadata)
            )
            
            results["mem0_result"] = mem0_result
            logger.info(f"Successfully added memory to Mem0 for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error adding memory to Mem0: {e}")
            results["mem0_result"] = {"error": str(e)}
        
        # Add to Graphiti (if unified memory is enabled)
        if self.use_unified and self.graphiti_client:
            try:
                if not self.is_graphiti_initialized:
                    await self.async_init()
                
                if self.is_graphiti_initialized:
                    episode_name = f"{user_id}_memory_{timestamp.isoformat()}"
                    logger.info(f"Adding to Graphiti: '{content[:50]}...' as episode '{episode_name}'")
                    
                    await self.graphiti_client.add_episode(
                        name=episode_name,
                        episode_body=content,
                        source=EpisodeType.text,
                        source_description=metadata.get("source_description", "Unified Memory System Entry"),
                        reference_time=timestamp,
                    )
                    
                    results["graphiti_result"] = {"episode_name": episode_name, "status": "success"}
                    logger.info(f"Successfully added episode to Graphiti: {episode_name}")
                else:
                    results["graphiti_result"] = {"error": "Graphiti not initialized"}
                    
            except Exception as e:
                logger.error(f"Error adding episode to Graphiti: {e}")
                results["graphiti_result"] = {"error": str(e)}
        
        return results
    
    async def search_memory(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search memories across both Mem0 and Graphiti systems.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with results from both systems
        """
        results = {
            "mem0_results": [],
            "graphiti_results": [],
            "unified": self.use_unified,
            "query": query
        }
        
        # Search Mem0 (always)
        try:
            logger.info(f"Searching Mem0 for: '{query}' with user_id '{user_id}'")
            
            # Run Mem0 search in executor since it's synchronous
            loop = asyncio.get_event_loop()
            mem0_search_results = await loop.run_in_executor(
                None, 
                lambda: self.mem0_client.search(query, user_id=user_id, limit=limit)
            )
            
            # Handle different result formats from Mem0
            if isinstance(mem0_search_results, dict) and 'results' in mem0_search_results:
                results["mem0_results"] = mem0_search_results['results']
            elif isinstance(mem0_search_results, list):
                results["mem0_results"] = mem0_search_results
            else:
                results["mem0_results"] = mem0_search_results
                
            logger.info(f"Mem0 search found {len(results['mem0_results'])} results")
            
        except Exception as e:
            logger.error(f"Error searching Mem0: {e}")
            results["mem0_results"] = {"error": str(e)}
        
        # Search Graphiti (if unified memory is enabled)
        if self.use_unified and self.graphiti_client and self.is_graphiti_initialized:
            try:
                logger.info(f"Searching Graphiti for: '{query}'")
                graphiti_search_results = await self.graphiti_client.search(query)
                
                # Format Graphiti results
                results["graphiti_results"] = [
                    {
                        "fact": r.fact,
                        "uuid": r.uuid,
                        "source_node_uuid": r.source_node_uuid,
                        "target_node_uuid": r.target_node_uuid,
                        "valid_at": r.valid_at.isoformat() if hasattr(r, 'valid_at') and r.valid_at else None,
                        "invalid_at": r.invalid_at.isoformat() if hasattr(r, 'invalid_at') and r.invalid_at else None,
                    }
                    for r in graphiti_search_results
                ]
                
                logger.info(f"Graphiti search found {len(results['graphiti_results'])} results")
                
            except Exception as e:
                logger.error(f"Error searching Graphiti: {e}")
                results["graphiti_results"] = {"error": str(e)}
        
        return results
    
    def add_sync(
        self, 
        content: str, 
        user_id: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Synchronous wrapper for add_memory (for compatibility with existing code).
        
        Args:
            content: The memory content/text
            user_id: User identifier
            metadata: Optional metadata dictionary
            
        Returns:
            Result from Mem0 (for backward compatibility)
        """
        if not self.use_unified:
            # Use existing Mem0 client directly for production
            messages = [{"role": "user", "content": content}]
            return self.mem0_client.add(messages, user_id=user_id, metadata=metadata)
        else:
            # For unified memory, we need to run the async version
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.add_memory(content, user_id, metadata))
                return result.get("mem0_result", result)
            finally:
                loop.close()
    
    def search_sync(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 10
    ) -> Any:
        """
        Synchronous wrapper for search_memory (for compatibility with existing code).
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results to return
            
        Returns:
            Results (Mem0 format for backward compatibility, or unified results)
        """
        if not self.use_unified:
            # Use existing Mem0 client directly for production
            return self.mem0_client.search(query, user_id=user_id, limit=limit)
        else:
            # For unified memory, we need to run the async version
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.search_memory(query, user_id, limit))
                # Return unified results for local development
                return result
            finally:
                loop.close()
    
    async def close(self):
        """Close connections to external services."""
        if self.graphiti_client:
            try:
                await self.graphiti_client.close()
                logger.info("Graphiti connection closed")
            except Exception as e:
                logger.error(f"Error closing Graphiti connection: {e}")
        
        # Mem0 client doesn't have an explicit close method
        logger.info("Unified Memory System connections closed")


# Global instance for the application
_unified_memory_instance = None


def get_unified_memory_client() -> UnifiedMemorySystem:
    """
    Get or create a global unified memory client instance.
    
    Returns:
        UnifiedMemorySystem instance
    """
    global _unified_memory_instance
    
    if _unified_memory_instance is None:
        _unified_memory_instance = UnifiedMemorySystem()
    
    return _unified_memory_instance


async def initialize_unified_memory():
    """
    Initialize the unified memory system asynchronously.
    This should be called during application startup.
    """
    client = get_unified_memory_client()
    if client.use_unified:
        await client.async_init()
        logger.info("Unified memory system initialized")
    else:
        logger.info("Using standard memory system (Mem0 only)") 