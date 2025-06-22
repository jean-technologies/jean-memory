"""
Unified Memory System - Clean Implementation

This module provides a unified interface for memory operations that combines:
- Mem0 for vector-based semantic search and entity extraction
- Mem0's built-in graph store for entity relationships
- Graphiti for temporal graph-based relationship modeling

Key Features:
- Temporal context extraction from memory text and dates
- Memory date inference for MCP tools
- Safe local development environment
- No impact on production infrastructure
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
import concurrent.futures

logger = logging.getLogger(__name__)

# Conditional imports for unified memory system
try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    GRAPHITI_AVAILABLE = True
    logger.info("Graphiti is available for temporal graph features")
except ImportError:
    logger.warning("Graphiti not available. Temporal graph features will be disabled.")
    GRAPHITI_AVAILABLE = False

try:
    from mem0 import Memory
    from mem0.configs.base import MemoryConfig
    MEM0_AVAILABLE = True
    logger.info("Mem0 is available for vector and graph features")
except ImportError:
    logger.error("Mem0 not available. Unified memory system cannot function.")
    MEM0_AVAILABLE = False


class TemporalExtractor:
    """Extract temporal context from memory text and dates."""
    
    @staticmethod
    def extract_memory_date(text: str) -> Optional[datetime]:
        """
        Extract a memory date from text using NLP patterns.
        This is used when no explicit memory_date is provided (e.g., MCP tools).
        """
        # Common date patterns
        patterns = [
            r'(?:on|in|during)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # on 12/25/2023
            r'(?:on|in)\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',  # in January 15, 2023
            r'(?:yesterday|today|tomorrow)',  # relative dates
            r'(?:last|this|next)\s+(week|month|year|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)',  # relative periods
        ]
        
        # For now, return None to indicate we should use creation_date
        # TODO: Implement proper NLP date extraction using a library like dateutil or spacy
        return None
    
    @staticmethod
    def extract_temporal_context(text: str, creation_date: datetime, memory_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Extract temporal context for Graphiti episode creation.
        
        Args:
            text: The memory text
            creation_date: When the memory was created in the system
            memory_date: When the memory event actually occurred (if known)
            
        Returns:
            Dictionary with temporal context for Graphiti
        """
        # Use memory_date if provided, otherwise fall back to creation_date
        reference_time = memory_date or creation_date
        
        # Extract temporal keywords from text
        temporal_keywords = []
        temporal_patterns = [
            r'\b(yesterday|today|tomorrow)\b',
            r'\b(last|this|next)\s+(week|month|year)\b',
            r'\b(morning|afternoon|evening|night)\b',
            r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',
        ]
        
        for pattern in temporal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            temporal_keywords.extend([match if isinstance(match, str) else ' '.join(match) for match in matches])
        
        return {
            "reference_time": reference_time,
            "creation_date": creation_date,
            "memory_date": memory_date,
            "temporal_keywords": temporal_keywords,
            "has_explicit_memory_date": memory_date is not None
        }


class UnifiedMemorySystem:
    """
    Clean, safe unified memory system for local development.
    
    Architecture:
    - Mem0 Vector Store: Semantic search
    - Mem0 Graph Store: Entity relationships  
    - Graphiti: Temporal episodes and time-aware relationships
    """
    
    def __init__(self):
        """Initialize the unified memory system."""
        self.mem0_client = None
        self.graphiti_client = None
        self.is_initialized = False
        self.temporal_extractor = TemporalExtractor()
        
        # Only initialize if we're in local development
        if self._is_local_development():
            self._init_clients()
        else:
            logger.info("Not in local development mode. Unified memory disabled.")
    
    def _is_local_development(self) -> bool:
        """Check if we're in local development mode."""
        return (
            os.getenv("ENVIRONMENT", "development").lower() == "development" and
            os.getenv("USE_UNIFIED_MEMORY", "false").lower() == "true"
        )
    
    def _init_clients(self):
        """Initialize Mem0 and Graphiti clients."""
        if not MEM0_AVAILABLE:
            logger.error("Cannot initialize unified memory: Mem0 not available")
            return
            
        try:
            # Initialize Mem0 with both vector and graph stores
            mem0_config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "unified_memory_dev"
                    }
                },
                "graph_store": {
                    "provider": "neo4j",
                    "config": {
                        "url": "bolt://localhost:7687",
                        "username": "neo4j",
                        "password": os.getenv("NEO4J_PASSWORD", "fasho93fasho")
                    }
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                },
                "version": "v1.1"
            }
            
            self.mem0_client = Memory.from_config(config_dict=mem0_config)
            logger.info("✅ Mem0 initialized with vector + graph stores")
            
            # Initialize Graphiti if available
            if GRAPHITI_AVAILABLE:
                self._init_graphiti()
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize unified memory system: {e}")
            self.mem0_client = None
            self.graphiti_client = None
    
    def _init_graphiti(self):
        """Initialize Graphiti client."""
        try:
            neo4j_uri = "bolt://localhost:7687"
            neo4j_user = "neo4j"
            neo4j_password = os.getenv("NEO4J_PASSWORD", "fasho93fasho")
            
            self.graphiti_client = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
            logger.info("✅ Graphiti initialized for temporal graphs")
            
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            self.graphiti_client = None
    
    async def async_init(self):
        """Perform async initialization (mainly for Graphiti indices)."""
        if self.graphiti_client:
            try:
                await self.graphiti_client.build_indices_and_constraints()
                logger.info("✅ Graphiti indices built successfully")
            except Exception as e:
                logger.error(f"Failed to build Graphiti indices: {e}")
    
    async def add_memory(
        self,
        text: str,
        user_id: str,
        creation_date: Optional[datetime] = None,
        memory_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a memory to the unified system.
        
        Args:
            text: The memory content
            user_id: User identifier
            creation_date: When the memory was created (defaults to now)
            memory_date: When the memory event occurred (optional, inferred if not provided)
            metadata: Additional metadata
            
        Returns:
            Results from all storage systems
        """
        if not self.is_initialized:
            return {"error": "Unified memory system not initialized"}
        
        if creation_date is None:
            creation_date = datetime.now(timezone.utc)
        
        # Try to infer memory_date if not provided
        if memory_date is None:
            memory_date = self.temporal_extractor.extract_memory_date(text)
        
        # Extract temporal context
        temporal_context = self.temporal_extractor.extract_temporal_context(
            text, creation_date, memory_date
        )
        
        results = {
            "mem0_result": None,
            "graphiti_result": None,
            "temporal_context": temporal_context,
            "unified": True
        }
        
        # Add to Mem0 (vector + graph)
        if self.mem0_client:
            try:
                logger.info(f"Adding to Mem0: '{text[:50]}...' for user '{user_id}'")
                
                # Prepare metadata for Mem0
                mem0_metadata = metadata or {}
                mem0_metadata.update({
                    "creation_date": creation_date.isoformat(),
                    "memory_date": memory_date.isoformat() if memory_date else None,
                    "source": "unified_memory_system"
                })
                
                # Run Mem0 add in executor (it's synchronous)
                loop = asyncio.get_event_loop()
                mem0_result = await loop.run_in_executor(
                    None,
                    lambda: self.mem0_client.add(text, user_id=user_id, metadata=mem0_metadata)
                )
                
                results["mem0_result"] = mem0_result
                logger.info(f"✅ Added to Mem0 for user {user_id}")
                
            except Exception as e:
                logger.error(f"Error adding to Mem0: {e}")
                results["mem0_result"] = {"error": str(e)}
        
        # Add to Graphiti (temporal episodes)
        if self.graphiti_client:
            try:
                logger.info(f"Adding to Graphiti: '{text[:50]}...' as temporal episode")
                
                episode_name = f"memory_{user_id}_{creation_date.strftime('%Y%m%d_%H%M%S')}"
                reference_time = temporal_context["reference_time"]
                
                await self.graphiti_client.add_episode(
                    name=episode_name,
                    episode_body=text,
                    source=EpisodeType.text,
                    source_description=f"Unified Memory: {temporal_context.get('temporal_keywords', [])}",
                    reference_time=reference_time
                )
                
                results["graphiti_result"] = {
                    "episode_name": episode_name,
                    "reference_time": reference_time.isoformat(),
                    "status": "success"
                }
                logger.info(f"✅ Added to Graphiti as episode: {episode_name}")
                
            except Exception as e:
                logger.error(f"Error adding to Graphiti: {e}")
                results["graphiti_result"] = {"error": str(e)}
        
        return results
    
    async def search_memory(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search memories across all systems.
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum results to return
            
        Returns:
            Combined search results
        """
        if not self.is_initialized:
            return {"error": "Unified memory system not initialized"}
        
        results = {
            "mem0_results": [],
            "graphiti_results": [],
            "unified": True,
            "query": query
        }
        
        # Search Mem0 (vector + graph)
        if self.mem0_client:
            try:
                logger.info(f"Searching Mem0 for: '{query}' (user: {user_id})")
                
                loop = asyncio.get_event_loop()
                mem0_search = await loop.run_in_executor(
                    None,
                    lambda: self.mem0_client.search(query, user_id=user_id, limit=limit)
                )
                
                # Handle different Mem0 result formats
                if isinstance(mem0_search, dict):
                    results["mem0_results"] = mem0_search.get("results", [])
                    # Include relations if available (from graph store)
                    if "relations" in mem0_search:
                        results["mem0_relations"] = mem0_search["relations"]
                elif isinstance(mem0_search, list):
                    results["mem0_results"] = mem0_search
                else:
                    results["mem0_results"] = [mem0_search] if mem0_search else []
                
                logger.info(f"✅ Mem0 search found {len(results['mem0_results'])} results")
                
            except Exception as e:
                logger.error(f"Error searching Mem0: {e}")
                results["mem0_results"] = {"error": str(e)}
        
        # Search Graphiti (temporal episodes)
        if self.graphiti_client:
            try:
                logger.info(f"Searching Graphiti for: '{query}' for user '{user_id}'")
                
                graphiti_search = await self.graphiti_client.search(query, user_id)
                
                # Format Graphiti results
                results["graphiti_results"] = [
                    {
                        "fact": getattr(r, "fact", ""),
                        "uuid": getattr(r, "uuid", ""),
                        "valid_at": getattr(r, "valid_at", None),
                        "invalid_at": getattr(r, "invalid_at", None),
                    }
                    for r in graphiti_search
                ]
                
                logger.info(f"✅ Graphiti search found {len(results['graphiti_results'])} results")
                
            except Exception as e:
                logger.error(f"Error searching Graphiti: {e}")
                results["graphiti_results"] = {"error": str(e)}
        
        return results
    
    def add_sync(self, text: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for add_memory."""
        return self._run_async_safely(self.add_memory(text, user_id, **kwargs))
    
    def search_sync(self, query: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """Synchronous wrapper for search_memory."""
        return self._run_async_safely(self.search_memory(query, user_id, **kwargs))
    
    def _run_async_safely(self, coro) -> Any:
        """Safely run async code from sync context."""
        try:
            # Check if there's already a running loop
            loop = asyncio.get_running_loop()
            
            # If we're in an async context, we need to use a thread executor
            # to avoid "got Future attached to a different loop" errors
            import threading
            result = None
            exception = None
            
            def run_in_new_loop():
                nonlocal result, exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        result = new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
            return result
            
        except RuntimeError:
            # No running loop, can use asyncio.run directly
            return asyncio.run(coro)


# Global instance
_unified_memory_client: Optional[UnifiedMemorySystem] = None


async def get_unified_memory_client() -> UnifiedMemorySystem:
    """Get or create the unified memory client."""
    global _unified_memory_client
    
    if _unified_memory_client is None:
        logger.info("Initializing Unified Memory System...")
        _unified_memory_client = UnifiedMemorySystem()
        
        if _unified_memory_client.is_initialized:
            await _unified_memory_client.async_init()
            logger.info("✅ Unified Memory System fully initialized")
        else:
            logger.info("ℹ️ Unified Memory System disabled (not in local dev mode)")
    
    return _unified_memory_client


def get_unified_memory_client_sync() -> UnifiedMemorySystem:
    """Synchronous wrapper to get the unified memory client."""
    try:
        loop = asyncio.get_running_loop()
        # If loop is running, use thread executor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, get_unified_memory_client())
            return future.result()
    except RuntimeError:
        # No running loop, can use asyncio.run directly
        return asyncio.run(get_unified_memory_client()) 