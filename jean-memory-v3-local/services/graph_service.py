"""
Graph Service for Jean Memory V3 Local
Handles Neo4j directly for entity relationships and temporal patterns
(Future: Can be upgraded to use Graphiti when available)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Use py2neo for direct Neo4j integration
try:
    from py2neo import Graph, Node, Relationship
    from py2neo.errors import ClientError
except ImportError as e:
    logging.error(f"py2neo not installed: {e}")
    logging.error("Please run: pip install py2neo")
    raise

from config import get_config, get_neo4j_config

logger = logging.getLogger(__name__)

class GraphService:
    """Graph service using py2neo with local Neo4j for entity relationships"""
    
    def __init__(self):
        self.config = get_config()
        self.neo4j_config = get_neo4j_config()
        
        # Core components
        self.graph: Optional[Graph] = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the graph service"""
        try:
            if not self.config.enable_neo4j:
                logger.info("⚠️  Neo4j disabled - skipping graph service initialization")
                return
                
            logger.info("🕸️  Initializing Neo4j graph service...")
            
            # Initialize Neo4j connection
            await self._initialize_neo4j_graph()
            
            # Create indexes and constraints
            await self._setup_graph_schema()
            
            self.is_initialized = True
            logger.info("✅ Graph service initialized with Neo4j")
            
        except Exception as e:
            logger.error(f"❌ Graph service initialization failed: {e}")
            # Don't raise - allow service to continue without graph features
            
    async def _initialize_neo4j_graph(self):
        """Initialize Neo4j graph connection"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.graph = await loop.run_in_executor(
                None,
                Graph,
                self.neo4j_config["uri"],
                auth=(self.neo4j_config["user"], self.neo4j_config["password"])
            )
            
            # Test connection
            await loop.run_in_executor(None, self.graph.run, "RETURN 1")
            
            logger.info("✅ Neo4j graph connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise
    
    async def _setup_graph_schema(self):
        """Set up Neo4j indexes and constraints"""
        try:
            loop = asyncio.get_event_loop()
            
            # Create indexes for better performance
            schema_queries = [
                "CREATE INDEX memory_id_index IF NOT EXISTS FOR (m:Memory) ON (m.memory_id)",
                "CREATE INDEX user_id_index IF NOT EXISTS FOR (m:Memory) ON (m.user_id)",
                "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX timestamp_index IF NOT EXISTS FOR (m:Memory) ON (m.timestamp)"
            ]
            
            for query in schema_queries:
                await loop.run_in_executor(None, self.graph.run, query)
            
            logger.info("✅ Graph schema setup complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup graph schema: {e}")
            # Don't raise - continue without schema optimizations
    
    async def add_memory_to_graph(self, 
                                 memory_id: str,
                                 content: str, 
                                 user_id: str,
                                 timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """Add memory to graph as a node"""
        if not self.is_initialized or not self.graph:
            logger.warning("Graph service not initialized - skipping graph operations")
            return {}
            
        try:
            timestamp = timestamp or datetime.now()
            
            # Create memory node
            loop = asyncio.get_event_loop()
            
            def create_memory_node():
                # Create memory node
                memory_node = Node(
                    "Memory",
                    memory_id=memory_id,
                    content=content,
                    user_id=user_id,
                    timestamp=timestamp.isoformat(),
                    created_at=datetime.now().isoformat()
                )
                
                # Merge (create or update) the memory node
                self.graph.merge(memory_node, "Memory", "memory_id")
                
                return {"memory_id": memory_id, "status": "created"}
            
            result = await loop.run_in_executor(None, create_memory_node)
            
            logger.info(f"✅ Added memory to graph: {memory_id[:20]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to add memory to graph: {e}")
            return {}
    
    async def search_graph_context(self, 
                                  query: str,
                                  user_id: str,
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """Search graph for memories by user"""
        if not self.is_initialized or not self.graph:
            return []
            
        try:
            loop = asyncio.get_event_loop()
            
            def search_memories():
                # Simple text search in graph
                cypher_query = """
                MATCH (m:Memory)
                WHERE m.user_id = $user_id
                AND (m.content CONTAINS $query OR m.memory_id CONTAINS $query)
                RETURN m.memory_id as memory_id, m.content as content, 
                       m.timestamp as timestamp, m.created_at as created_at
                ORDER BY m.timestamp DESC
                LIMIT $limit
                """
                
                result = self.graph.run(cypher_query, 
                                      user_id=user_id, 
                                      query=query, 
                                      limit=limit)
                
                return [dict(record) for record in result]
            
            results = await loop.run_in_executor(None, search_memories)
            
            logger.info(f"🕸️  Found {len(results)} graph memories for query: {query[:30]}...")
            return results
            
        except Exception as e:
            logger.error(f"❌ Graph search failed: {e}")
            return []
    
    async def get_user_memories(self, 
                               user_id: str,
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get all memories for a user from graph"""
        if not self.is_initialized or not self.graph:
            return []
            
        try:
            loop = asyncio.get_event_loop()
            
            def get_memories():
                cypher_query = """
                MATCH (m:Memory)
                WHERE m.user_id = $user_id
                RETURN m.memory_id as memory_id, m.content as content, 
                       m.timestamp as timestamp, m.created_at as created_at
                ORDER BY m.timestamp DESC
                LIMIT $limit
                """
                
                result = self.graph.run(cypher_query, user_id=user_id, limit=limit)
                return [dict(record) for record in result]
            
            memories = await loop.run_in_executor(None, get_memories)
            
            logger.info(f"📅 Retrieved {len(memories)} memories for user: {user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to get user memories: {e}")
            return []
    
    async def delete_memory_from_graph(self, memory_id: str) -> bool:
        """Delete memory from graph"""
        if not self.is_initialized or not self.graph:
            return True  # Return success if graph not enabled
            
        try:
            loop = asyncio.get_event_loop()
            
            def delete_memory():
                cypher_query = """
                MATCH (m:Memory {memory_id: $memory_id})
                DELETE m
                RETURN count(m) as deleted_count
                """
                
                result = self.graph.run(cypher_query, memory_id=memory_id)
                return result.single()["deleted_count"] > 0
            
            success = await loop.run_in_executor(None, delete_memory)
            
            if success:
                logger.info(f"✅ Deleted memory from graph: {memory_id[:20]}...")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to delete memory from graph: {e}")
            return False
    
    async def get_graph_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get graph statistics"""
        if not self.is_initialized or not self.graph:
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "total_memories": 0,
                "graph_enabled": False
            }
            
        try:
            loop = asyncio.get_event_loop()
            
            def get_stats():
                if user_id:
                    # User-specific stats
                    query = """
                    MATCH (m:Memory {user_id: $user_id})
                    RETURN count(m) as memory_count
                    """
                    result = self.graph.run(query, user_id=user_id)
                    memory_count = result.single()["memory_count"]
                else:
                    # Global stats
                    query = """
                    MATCH (m:Memory)
                    RETURN count(m) as memory_count
                    """
                    result = self.graph.run(query)
                    memory_count = result.single()["memory_count"]
                
                return {
                    "total_memories": memory_count,
                    "total_nodes": memory_count,  # For now, one node per memory
                    "total_relationships": 0,  # Future: add relationships
                    "graph_enabled": True
                }
            
            stats = await loop.run_in_executor(None, get_stats)
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get graph stats: {e}")
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "total_memories": 0,
                "graph_enabled": False
            }
    
    def is_ready(self) -> bool:
        """Check if graph service is ready"""
        return self.is_initialized and (not self.config.enable_neo4j or self.graph is not None)
    
    async def cleanup(self):
        """Cleanup graph service resources"""
        logger.info("🧹 Cleaning up graph service...")
        
        if self.graph:
            try:
                # Close Neo4j connection
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    getattr,
                    self.graph,
                    'close',
                    lambda: None
                )
            except Exception as e:
                logger.error(f"❌ Error during graph cleanup: {e}")
        
        self.graph = None
        logger.info("✅ Graph service cleanup complete")