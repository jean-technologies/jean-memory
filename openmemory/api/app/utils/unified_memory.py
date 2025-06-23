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


"""
Unified Memory Client - Compatibility layer for migrating from Qdrant to Multi-layer RAG
"""

import os
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

from mem0 import Memory
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from neo4j import AsyncGraphDatabase
import psycopg2
from psycopg2.extras import RealDictCursor

try:
    from app.settings import config
    from app.utils.memory import get_memory_client as get_qdrant_memory_client
except ImportError:
    # Fallback for script execution
    try:
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).parent.parent))
        from settings import config
        from utils.memory import get_memory_client as get_qdrant_memory_client
    except ImportError:
        # Create a mock config for testing
        class MockConfig:
            def __init__(self):
                self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
                self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.EMBEDDER_MODEL = os.getenv("EMBEDDER_MODEL", "text-embedding-3-small")
                self.NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                self.NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
                self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
                self.PG_HOST = os.getenv("PG_HOST", "localhost")
                self.PG_PORT = int(os.getenv("PG_PORT", "5432"))
                self.PG_USER = os.getenv("PG_USER", "postgres")
                self.PG_PASSWORD = os.getenv("PG_PASSWORD")
                self.PG_DBNAME = os.getenv("PG_DBNAME", "mem0_unified")
        
        config = MockConfig()
        
        def get_qdrant_memory_client():
            # Mock function for testing
            return None

logger = logging.getLogger(__name__)


class UnifiedMemoryClient:
    """
    Compatibility layer supporting both old (Qdrant) and new (pgvector + Neo4j) systems
    Enables gradual migration with zero downtime
    """
    
    def __init__(self, use_new_system: bool = False, user_id: Optional[str] = None):
        self.use_new_system = use_new_system
        self.user_id = user_id
        
        if use_new_system:
            # Initialize new multi-layer system
            self.mem0_client = self._init_mem0_pgvector()
            self.graphiti_client = None  # Initialize later if needed
            self.neo4j_driver = self._init_neo4j()
            self.pg_connection = self._init_postgres()
            self._setup_postgres_tables()
            logger.info("✅ Initialized unified memory system (pgvector + Neo4j)")
        else:
            # Use existing Qdrant system
            self.mem0_client = get_qdrant_memory_client()
            self.graphiti_client = None
            self.neo4j_driver = None
            self.pg_connection = None
            logger.info("✅ Using existing Qdrant memory system")
    
    def _init_mem0_pgvector(self) -> Memory:
        """Initialize mem0 with pgvector backend"""
        # Check if this is the test user and use test infrastructure
        enable_test_user = os.getenv("ENABLE_UNIFIED_MEMORY_TEST_USER", "false").lower() == "true"
        test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "")
        is_test_user = enable_test_user and test_user_id and self.user_id == test_user_id
        
        if is_test_user:
            # Use test infrastructure
            neo4j_uri = os.getenv("TEST_NEO4J_URI", "bolt://localhost:7688")
            pg_config = {
                "user": os.getenv("TEST_PG_USER", "postgres"),
                "password": os.getenv("TEST_PG_PASSWORD", "secure_postgres_test_2024"),
                "host": os.getenv("TEST_PG_HOST", "localhost"),
                "port": os.getenv("TEST_PG_PORT", "5433"),
                "dbname": os.getenv("TEST_PG_DBNAME", "mem0_unified"),
                "collection_name": "test_user_memories"
            }
            neo4j_config = {
                "url": neo4j_uri,
                "username": os.getenv("TEST_NEO4J_USER", "neo4j"),
                "password": os.getenv("TEST_NEO4J_PASSWORD", "secure_neo4j_test_2024")
            }
            logger.info(f"🧪 Using TEST infrastructure for user {self.user_id}")
        else:
            # Use production infrastructure
            neo4j_config = {
                "url": config.NEO4J_URI,
                "username": config.NEO4J_USER,
                "password": config.NEO4J_PASSWORD
            }
            pg_config = {
                "user": config.PG_USER,
                "password": config.PG_PASSWORD,
                "host": config.PG_HOST,
                "port": config.PG_PORT,
                "dbname": config.PG_DBNAME,
                "collection_name": "unified_memory_mem0"
            }
            logger.info(f"🏭 Using PRODUCTION infrastructure for user {self.user_id}")
        
        mem0_config = {
            "graph_store": {
                "provider": "neo4j",
                "config": neo4j_config
            },
            "vector_store": {
                "provider": "pgvector",
                "config": pg_config
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": config.OPENAI_MODEL,
                    "api_key": config.OPENAI_API_KEY
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": config.EMBEDDER_MODEL,
                    "api_key": config.OPENAI_API_KEY
                }
            },
            "version": "v1.1"
        }
        
        return Memory.from_config(config_dict=mem0_config)
    
    async def _init_graphiti(self) -> Graphiti:
        """Initialize Graphiti for episodic memory"""
        # Check if this is the test user and use test infrastructure
        enable_test_user = os.getenv("ENABLE_UNIFIED_MEMORY_TEST_USER", "false").lower() == "true"
        test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "")
        is_test_user = enable_test_user and test_user_id and self.user_id == test_user_id
        
        if is_test_user:
            # Use test Neo4j
            neo4j_uri = os.getenv("TEST_NEO4J_URI", "bolt://localhost:7688")
            neo4j_user = os.getenv("TEST_NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("TEST_NEO4J_PASSWORD", "secure_neo4j_test_2024")
        else:
            # Use production Neo4j
            neo4j_uri = config.NEO4J_URI
            neo4j_user = config.NEO4J_USER
            neo4j_password = config.NEO4J_PASSWORD
        
        graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
        
        # Build indices and constraints
        await graphiti.build_indices_and_constraints()
        
        return graphiti
    
    def _init_neo4j(self) -> AsyncGraphDatabase.driver:
        """Initialize direct Neo4j driver for advanced queries"""
        # Check if this is the test user and use test infrastructure
        enable_test_user = os.getenv("ENABLE_UNIFIED_MEMORY_TEST_USER", "false").lower() == "true"
        test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "")
        is_test_user = enable_test_user and test_user_id and self.user_id == test_user_id
        
        if is_test_user:
            # Use test Neo4j
            neo4j_uri = os.getenv("TEST_NEO4J_URI", "bolt://localhost:7688")
            neo4j_user = os.getenv("TEST_NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("TEST_NEO4J_PASSWORD", "secure_neo4j_test_2024")
        else:
            # Use production Neo4j
            neo4j_uri = config.NEO4J_URI
            neo4j_user = config.NEO4J_USER
            neo4j_password = config.NEO4J_PASSWORD
        
        return AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection for direct queries"""
        # Check if this is the test user and use test infrastructure
        enable_test_user = os.getenv("ENABLE_UNIFIED_MEMORY_TEST_USER", "false").lower() == "true"
        test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "")
        is_test_user = enable_test_user and test_user_id and self.user_id == test_user_id
        
        if is_test_user:
            # Use test PostgreSQL
            return psycopg2.connect(
                host=os.getenv("TEST_PG_HOST", "localhost"),
                port=int(os.getenv("TEST_PG_PORT", "5433")),
                database=os.getenv("TEST_PG_DBNAME", "mem0_unified"),
                user=os.getenv("TEST_PG_USER", "postgres"),
                password=os.getenv("TEST_PG_PASSWORD", "secure_postgres_test_2024")
            )
        else:
            # Use production PostgreSQL
            return psycopg2.connect(
                host=config.PG_HOST,
                port=config.PG_PORT,
                database=config.PG_DBNAME,
                user=config.PG_USER,
                password=config.PG_PASSWORD
            )
    
    def _setup_postgres_tables(self):
        """Create necessary PostgreSQL tables"""
        if not self.pg_connection:
            return
        
        cursor = self.pg_connection.cursor()
        try:
            # Create unified_memories table for episode tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unified_memories (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create index on user_id for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_unified_memories_user_id 
                ON unified_memories(user_id);
            """)
            
            # Create index on created_at for temporal queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_unified_memories_created_at 
                ON unified_memories(created_at);
            """)
            
            self.pg_connection.commit()
            logger.info("✅ PostgreSQL tables setup complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup PostgreSQL tables: {e}")
            self.pg_connection.rollback()
        finally:
            cursor.close()
    
    async def add(self, text: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add memory to the appropriate system"""
        if self.use_new_system:
            # Add to pgvector + create graph relationships
            result = await self._add_to_unified_system(text, user_id, metadata)
            
            # Create episodic memories asynchronously
            asyncio.create_task(self._create_episodes(user_id))
            
            return result
        else:
            # Use existing mem0/Qdrant
            return self.mem0_client.add(text, user_id=user_id, metadata=metadata)
    
    async def _add_to_unified_system(self, text: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add memory to unified system with graph relationships"""
        try:
            # Add to mem0 (which handles pgvector + Neo4j graph)
            result = self.mem0_client.add(
                text,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Track in PostgreSQL for episode generation
            if self.pg_connection:
                cursor = self.pg_connection.cursor()
                cursor.execute("""
                    INSERT INTO unified_memories (user_id, content, metadata, created_at)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, text, json.dumps(metadata or {}), datetime.now(timezone.utc)))
                self.pg_connection.commit()
                cursor.close()
            
            logger.info(f"✅ Added memory to unified system: {result.get('id', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to add to unified system: {e}")
            raise
    
    async def search(self, query: str, user_id: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search memories from the appropriate system"""
        if self.use_new_system:
            # Multi-layer search
            return await self._unified_search(query, user_id, limit, **kwargs)
        else:
            # Existing Qdrant search
            return self.mem0_client.search(query=query, user_id=user_id, limit=limit)
    
    async def _unified_search(self, query: str, user_id: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Perform multi-layer search across all memory systems"""
        results = []
        
        # 1. Semantic search via mem0 (pgvector)
        semantic_results = self.mem0_client.search(query=query, user_id=user_id, limit=limit)
        for result in semantic_results:
            result['source'] = 'semantic'
            results.append(result)
        
        # 2. Graph search for relationships
        if self.neo4j_driver:
            graph_results = await self._search_graph_relationships(query, user_id, limit)
            results.extend(graph_results)
        
        # 3. Episode search via Graphiti
        if self.graphiti_client:
            episode_results = await self._search_episodes(query, user_id, limit)
            results.extend(episode_results)
        
        # Deduplicate and sort by relevance
        seen_ids = set()
        unique_results = []
        for result in results:
            result_id = result.get('id', result.get('memory', ''))
            if result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        # Sort by score/confidence
        unique_results.sort(key=lambda x: x.get('score', x.get('confidence', 0)), reverse=True)
        
        return unique_results[:limit]
    
    async def _search_graph_relationships(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Search Neo4j graph for entity relationships"""
        results = []
        
        async with self.neo4j_driver.session() as session:
            # Search for entities mentioned in the query
            cypher_query = """
            MATCH (m:Memory {user_id: $user_id})-[:MENTIONS]->(e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($query) 
               OR toLower(m.content) CONTAINS toLower($query)
            OPTIONAL MATCH (e)-[r:RELATES_TO]-(e2:Entity)
            RETURN DISTINCT m.content as memory, m.id as id, 
                   collect(DISTINCT e.name) as entities,
                   collect(DISTINCT {from: e.name, to: e2.name, type: type(r)}) as relationships
            LIMIT $limit
            """
            
            result = await session.run(
                cypher_query,
                user_id=user_id,
                query=query,
                limit=limit
            )
            
            async for record in result:
                results.append({
                    'id': record['id'],
                    'memory': record['memory'],
                    'source': 'graph',
                    'entities': record['entities'],
                    'relationships': [r for r in record['relationships'] if r['to'] is not None],
                    'score': 0.9  # High confidence for graph matches
                })
        
        return results
    
    async def _search_episodes(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Search Graphiti episodes"""
        results = []
        
        try:
            # Search episodes via Graphiti
            episode_results = await self.graphiti_client.search(query)
            
            for episode in episode_results[:limit]:
                results.append({
                    'id': f"episode_{episode.uuid}",
                    'memory': episode.fact if hasattr(episode, 'fact') else str(episode),
                    'source': 'episodic',
                    'episode_name': getattr(episode, 'name', 'Unknown'),
                    'score': getattr(episode, 'score', 0.8)
                })
                
        except Exception as e:
            logger.error(f"Episode search error: {e}")
        
        return results
    
    async def search_multilayer(self, query: str, user_id: str, limit: int = 10, 
                               search_types: List[str] = None, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Advanced multi-layer search with fine control"""
        if not self.use_new_system:
            # Fallback to regular search for old system
            return await self.search(query, user_id, limit)
        
        search_types = search_types or ["semantic", "graph", "episodic"]
        all_results = []
        
        if "semantic" in search_types:
            semantic_results = self.mem0_client.search(query=query, user_id=user_id, limit=limit)
            for r in semantic_results:
                r['source'] = 'semantic'
                all_results.append(r)
        
        if "graph" in search_types:
            graph_results = await self._search_graph_relationships(query, user_id, limit)
            all_results.extend(graph_results)
        
        if "episodic" in search_types:
            episode_results = await self._search_episodes(query, user_id, limit)
            all_results.extend(episode_results)
        
        # Apply filters if provided
        if filters:
            all_results = self._apply_filters(all_results, filters)
        
        # Sort and limit
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return all_results[:limit]
    
    def _apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to search results"""
        filtered = []
        
        for result in results:
            include = True
            
            # Tag filter
            if 'tags' in filters and filters['tags']:
                result_tags = result.get('metadata', {}).get('tags', [])
                if not all(tag in result_tags for tag in filters['tags']):
                    include = False
            
            # Date range filter
            if 'date_from' in filters:
                created_at = result.get('created_at', '')
                if created_at and created_at < filters['date_from']:
                    include = False
            
            if 'date_to' in filters:
                created_at = result.get('created_at', '')
                if created_at and created_at > filters['date_to']:
                    include = False
            
            if include:
                filtered.append(result)
        
        return filtered
    
    async def _create_episodes(self, user_id: str):
        """Background task to create episodes from recent memories"""
        if not self.graphiti_client:
            return
        
        try:
            # Get recent memories for the user
            cursor = self.pg_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM unified_memories 
                WHERE user_id = %s 
                AND created_at > NOW() - INTERVAL '1 day'
                ORDER BY created_at DESC
                LIMIT 50
            """, (user_id,))
            
            recent_memories = cursor.fetchall()
            cursor.close()
            
            if len(recent_memories) < 3:
                return  # Not enough memories for episodes
            
            # Group by temporal proximity (within same day)
            temporal_groups = defaultdict(list)
            for memory in recent_memories:
                date_key = memory['created_at'].strftime('%Y-%m-%d')
                temporal_groups[date_key].append(memory)
            
            # Create episodes for each group
            for date_key, memories in temporal_groups.items():
                if len(memories) >= 3:
                    episode_name = f"user_{user_id}_daily_{date_key}"
                    episode_content = "\n".join([
                        f"Memory {i+1}: {m['content']}" 
                        for i, m in enumerate(memories)
                    ])
                    
                    await self.graphiti_client.add_episode(
                        name=episode_name,
                        episode_body=episode_content,
                        source=EpisodeType.text,
                        source_description=f"Daily activities for {date_key}",
                        reference_time=datetime.now(timezone.utc)
                    )
                    
                    logger.info(f"✅ Created episode: {episode_name}")
                    
        except Exception as e:
            logger.error(f"❌ Episode creation failed: {e}")
    
    async def get_all(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all memories for a user"""
        if self.use_new_system:
            # Get from pgvector via mem0
            return self.mem0_client.get_all(user_id=user_id, limit=limit)
        else:
            # Get from Qdrant
            return self.mem0_client.get_all(user_id=user_id, limit=limit)
    
    async def add_with_vector(self, text: str, user_id: str, metadata: Dict[str, Any], 
                             vector: List[float]) -> Dict[str, Any]:
        """Add memory with pre-computed vector (for migration)"""
        if not self.use_new_system:
            raise NotImplementedError("Vector migration only supported for new system")
        
        # Direct insert to pgvector
        cursor = self.pg_connection.cursor()
        cursor.execute("""
            INSERT INTO memories (user_id, content, embedding, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            user_id, 
            text, 
            vector, 
            json.dumps(metadata),
            metadata.get('created_at', datetime.now(timezone.utc))
        ))
        
        memory_id = cursor.fetchone()[0]
        self.pg_connection.commit()
        cursor.close()
        
        # Also add to Neo4j graph
        async with self.neo4j_driver.session() as session:
            await session.run("""
                CREATE (m:Memory {
                    id: $id,
                    user_id: $user_id,
                    content: $content,
                    created_at: $created_at
                })
            """, id=str(memory_id), user_id=user_id, content=text, 
                created_at=metadata.get('created_at', datetime.now(timezone.utc).isoformat()))
        
        return {"id": str(memory_id), "status": "migrated"}
    
    async def generate_user_episodes(self, user_id: str):
        """Generate all episodes for a user (used after migration)"""
        if not self.graphiti_client:
            return
        
        # Get all user memories
        cursor = self.pg_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM unified_memories 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        all_memories = cursor.fetchall()
        cursor.close()
        
        # Create temporal episodes
        await self._create_temporal_episodes(user_id, all_memories)
        
        # Create semantic episodes
        await self._create_semantic_episodes(user_id, all_memories)
    
    async def _create_temporal_episodes(self, user_id: str, memories: List[Dict[str, Any]]):
        """Create episodes based on temporal clustering"""
        # Group by week
        weekly_groups = defaultdict(list)
        
        for memory in memories:
            week_key = memory['created_at'].strftime('%Y-W%U')
            weekly_groups[week_key].append(memory)
        
        for week_key, week_memories in weekly_groups.items():
            if len(week_memories) >= 5:
                episode_name = f"user_{user_id}_weekly_{week_key}"
                episode_content = "\n".join([
                    f"Memory {i+1}: {m['content']}" 
                    for i, m in enumerate(week_memories[:20])  # Limit to 20 memories per episode
                ])
                
                await self.graphiti_client.add_episode(
                    name=episode_name,
                    episode_body=episode_content,
                    source=EpisodeType.text,
                    source_description=f"Weekly summary for {week_key}",
                    reference_time=week_memories[0]['created_at']
                )
    
    async def _create_semantic_episodes(self, user_id: str, memories: List[Dict[str, Any]]):
        """Create episodes based on semantic clustering"""
        # Define topic keywords
        topic_keywords = {
            'fitness': ['gym', 'workout', 'exercise', 'fitness', 'training', 'run', 'lift'],
            'work': ['work', 'project', 'meeting', 'code', 'development', 'task'],
            'social': ['friend', 'family', 'meet', 'party', 'event', 'dinner'],
            'travel': ['travel', 'trip', 'flight', 'hotel', 'visit', 'vacation']
        }
        
        topic_groups = defaultdict(list)
        
        for memory in memories:
            content_lower = memory['content'].lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    topic_groups[topic].append(memory)
                    break
        
        for topic, topic_memories in topic_groups.items():
            if len(topic_memories) >= 5:
                episode_name = f"user_{user_id}_topic_{topic}"
                episode_content = "\n".join([
                    f"Memory {i+1}: {m['content']}" 
                    for i, m in enumerate(topic_memories[:30])  # Limit to 30 memories per topic
                ])
                
                await self.graphiti_client.add_episode(
                    name=episode_name,
                    episode_body=episode_content,
                    source=EpisodeType.text,
                    source_description=f"{topic.capitalize()} related memories",
                    reference_time=datetime.now(timezone.utc)
                )
    
    async def close(self):
        """Clean up connections"""
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        
        if self.pg_connection:
            self.pg_connection.close()
        
        if self.graphiti_client:
            await self.graphiti_client.close()


# Utility function to determine if a user should use the new system
def should_use_unified_memory(user_id: str) -> bool:
    """
    Determine if user should use new unified memory system.
    
    This function safely routes users based on environment variables
    without exposing sensitive data in the codebase.
    """
    
    # PRODUCTION TESTING: Check if test user routing is enabled
    enable_test_user = os.getenv("ENABLE_UNIFIED_MEMORY_TEST_USER", "false").lower() == "true"
    test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "")
    
    # Only route test user if both conditions are met:
    # 1. Test user routing is explicitly enabled
    # 2. Test user ID is configured
    # 3. Current user matches test user ID
    if enable_test_user and test_user_id and user_id == test_user_id:
        logger.info(f"🧪 Routing test user to NEW unified memory system (production test)")
        return True
    
    # Check environment override for development
    if os.getenv("FORCE_UNIFIED_MEMORY", "false").lower() == "true":
        logger.info(f"🔧 Force routing user {user_id[:8]}... to NEW system (dev override)")
        return True
    
    # Option 1: Percentage rollout (for future gradual rollout)
    rollout_percentage = os.getenv("UNIFIED_MEMORY_ROLLOUT_PERCENTAGE")
    if rollout_percentage:
        try:
            percentage = int(rollout_percentage)
            import hashlib
            user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            if (user_hash % 100) < percentage:
                logger.info(f"📊 Routing user {user_id[:8]}... to NEW system (rollout: {percentage}%)")
                return True
        except (ValueError, TypeError):
            logger.warning(f"Invalid rollout percentage: {rollout_percentage}")
    
    # Option 2: Explicit user allowlist (for future targeted testing)
    allowlist_users = os.getenv("UNIFIED_MEMORY_USER_ALLOWLIST", "")
    if allowlist_users and user_id in allowlist_users.split(','):
        logger.info(f"✅ Routing allowlisted user {user_id[:8]}... to NEW system")
        return True
    
    # Default to old system for all other users
    # No logging of user ID for privacy in production
    return False


# Factory function to get appropriate memory client
def get_unified_memory_client(user_id: Optional[str] = None) -> UnifiedMemoryClient:
    """Get memory client based on user configuration"""
    use_new_system = False
    
    if user_id:
        use_new_system = should_use_unified_memory(user_id)
    elif config.USE_UNIFIED_MEMORY:
        use_new_system = True
    
    return UnifiedMemoryClient(use_new_system=use_new_system, user_id=user_id) 