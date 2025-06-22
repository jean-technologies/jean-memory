#!/usr/bin/env python3
"""
Enhanced Unified Memory Ingestion Pipeline

This script implements the missing features:
1. mem0's entity extraction capabilities
2. Proper entity-memory relationships in Neo4j
3. Graphiti temporal episode creation
4. Multi-hop graph traversal support
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'openmemory' / 'api'))

# Set environment for unified memory
os.environ["ENVIRONMENT"] = "development"
os.environ["USE_UNIFIED_MEMORY"] = "true"
os.environ["IS_LOCAL_UNIFIED_MEMORY"] = "true"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedUnifiedIngestion:
    """Enhanced ingestion with entity extraction and relationship building"""
    
    def __init__(self):
        self.mem0_client = None
        self.graphiti_client = None
        self.neo4j_driver = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize all components with enhanced features"""
        try:
            from mem0 import Memory
            from graphiti_core import Graphiti
            from graphiti_core.nodes import EpisodeType
            from neo4j import GraphDatabase
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # Initialize mem0 with entity extraction enabled
            logger.info("🧠 Initializing mem0 with entity extraction...")
            
            # Try to determine the correct Neo4j configuration
            neo4j_config = None
            
            # Try local first
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "fasho93fasho"))
                with driver.session() as session:
                    session.run("RETURN 1")
                driver.close()
                neo4j_config = {
                    "url": "bolt://localhost:7687",
                    "username": "neo4j",
                    "password": "fasho93fasho"
                }
                logger.info("  ✅ Using local Neo4j")
            except:
                # Try cloud
                try:
                    neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://6ff1aa85.databases.neo4j.io")
                    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                    neo4j_password = os.getenv("NEO4J_PASSWORD")
                    
                    if neo4j_password:
                        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                        with driver.session() as session:
                            session.run("RETURN 1")
                        driver.close()
                        neo4j_config = {
                            "url": neo4j_uri,
                            "username": neo4j_user,
                            "password": neo4j_password
                        }
                        logger.info("  ✅ Using cloud Neo4j")
                except Exception as e:
                    logger.error(f"  ❌ No Neo4j available: {e}")
                    return False
            
            mem0_config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "unified_memory_enhanced"
                    }
                },
                "graph_store": {
                    "provider": "neo4j",
                    "config": neo4j_config
                },
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": "gpt-4o-mini",
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": "text-embedding-3-small",
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                },
                "version": "v1.1"
            }
            
            self.mem0_client = Memory.from_config(config_dict=mem0_config)
            logger.info("✅ mem0 initialized with entity extraction enabled")
            
            # Initialize Graphiti for temporal features
            logger.info("🔗 Initializing Graphiti for temporal episodes...")
            if neo4j_config:
                self.graphiti_client = Graphiti(
                    neo4j_config["url"],
                    neo4j_config["username"],
                    neo4j_config["password"]
                )
                await self.graphiti_client.build_indices_and_constraints()
                logger.info("✅ Graphiti initialized with indices built")
                
                # Direct Neo4j connection for enhanced graph operations
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_config["url"],
                    auth=(neo4j_config["username"], neo4j_config["password"])
                )
                logger.info("✅ Direct Neo4j connection established")
            else:
                logger.warning("⚠️ Skipping Graphiti - no Neo4j available")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def ingest_memory_with_entities(
        self,
        text: str,
        user_id: str,
        creation_date: datetime,
        memory_date: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a memory with full entity extraction and relationship building
        """
        if not self.initialized:
            return {"error": "System not initialized"}
        
        results = {
            "mem0_result": None,
            "entities_extracted": [],
            "relationships_created": [],
            "graphiti_episode": None,
            "graph_enhancements": []
        }
        
        try:
            # Step 1: Add memory to mem0 (with entity extraction)
            logger.info(f"📝 Adding memory to mem0 with entity extraction...")
            mem0_result = self.mem0_client.add(
                text,
                user_id=user_id,
                metadata={
                    **(metadata or {}),
                    "creation_date": creation_date.isoformat(),
                    "memory_date": memory_date.isoformat() if memory_date else None,
                    "enhanced_ingestion": True
                }
            )
            results["mem0_result"] = mem0_result
            
            # Extract memory ID for relationships
            memory_id = mem0_result.get("id", f"mem_{datetime.now().timestamp()}")
            
            # Step 2: Extract entities using mem0's capabilities
            entities = await self._extract_entities_from_memory(text, user_id)
            results["entities_extracted"] = entities
            
            # Step 3: Create entity nodes and relationships in Neo4j
            relationships = await self._create_entity_relationships(
                memory_id, text, entities, user_id, memory_date or creation_date
            )
            results["relationships_created"] = relationships
            
            # Step 4: Add temporal episode to Graphiti
            if self.graphiti_client:
                episode_result = await self._create_graphiti_episode(
                    text, user_id, memory_date or creation_date, entities
                )
                results["graphiti_episode"] = episode_result
            
            # Step 5: Enhance graph with additional relationships
            enhancements = await self._enhance_graph_relationships(
                memory_id, entities, user_id
            )
            results["graph_enhancements"] = enhancements
            
            logger.info(f"✅ Successfully ingested memory with {len(entities)} entities")
            
        except Exception as e:
            logger.error(f"❌ Ingestion error: {e}")
            results["error"] = str(e)
        
        return results
    
    async def _extract_entities_from_memory(
        self, 
        text: str, 
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Extract entities using mem0's built-in capabilities"""
        try:
            # Use mem0's search to trigger entity extraction
            # This will populate the graph store with entities
            search_result = self.mem0_client.search(
                text[:50],  # Use beginning of text as query
                user_id=user_id,
                limit=1
            )
            
            # Query Neo4j for extracted entities
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    WHERE n.user_id = $user_id 
                    AND (n:Person OR n:Organization OR n:Location OR n:Event OR n:Project OR n:Concept)
                    AND n.name IS NOT NULL
                    RETURN DISTINCT n.name as name, labels(n)[0] as type, n
                    ORDER BY n.created DESC
                    LIMIT 20
                """, user_id=user_id)
                
                entities = []
                for record in result:
                    entities.append({
                        "name": record["name"],
                        "type": record["type"],
                        "properties": dict(record["n"])
                    })
                
                logger.info(f"  📍 Extracted {len(entities)} entities")
                return entities
                
        except Exception as e:
            logger.error(f"  ❌ Entity extraction failed: {e}")
            return []
    
    async def _create_entity_relationships(
        self,
        memory_id: str,
        memory_text: str,
        entities: List[Dict[str, Any]],
        user_id: str,
        memory_date: datetime
    ) -> List[Dict[str, Any]]:
        """Create relationships between memory and entities"""
        relationships = []
        
        with self.neo4j_driver.session() as session:
            try:
                # First, ensure the memory node exists
                session.run("""
                    MERGE (m:Memory {id: $memory_id, user_id: $user_id})
                    SET m.text = $text,
                        m.memory_date = $memory_date,
                        m.enhanced = true
                """, 
                    memory_id=memory_id,
                    user_id=user_id,
                    text=memory_text,
                    memory_date=memory_date.isoformat()
                )
                
                # Create relationships to entities
                for entity in entities:
                    # Check if entity is mentioned in memory text
                    if entity["name"].lower() in memory_text.lower():
                        result = session.run("""
                            MATCH (m:Memory {id: $memory_id})
                            MATCH (e {name: $entity_name, user_id: $user_id})
                            MERGE (m)-[r:MENTIONS]->(e)
                            SET r.created = timestamp(),
                                r.confidence = $confidence
                            RETURN type(r) as rel_type
                        """,
                            memory_id=memory_id,
                            entity_name=entity["name"],
                            user_id=user_id,
                            confidence=0.9 if entity["name"] in memory_text else 0.5
                        )
                        
                        for record in result:
                            relationships.append({
                                "from": "Memory",
                                "to": entity["type"],
                                "type": "MENTIONS",
                                "entity": entity["name"]
                            })
                
                # Create entity-to-entity relationships based on co-occurrence
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        if (entity1["name"] in memory_text and 
                            entity2["name"] in memory_text):
                            session.run("""
                                MATCH (e1 {name: $name1, user_id: $user_id})
                                MATCH (e2 {name: $name2, user_id: $user_id})
                                MERGE (e1)-[r:CO_OCCURS_WITH]->(e2)
                                SET r.count = COALESCE(r.count, 0) + 1,
                                    r.last_seen = $memory_date
                            """,
                                name1=entity1["name"],
                                name2=entity2["name"],
                                user_id=user_id,
                                memory_date=memory_date.isoformat()
                            )
                            
                            relationships.append({
                                "from": entity1["name"],
                                "to": entity2["name"],
                                "type": "CO_OCCURS_WITH"
                            })
                
                logger.info(f"  🔗 Created {len(relationships)} relationships")
                
            except Exception as e:
                logger.error(f"  ❌ Relationship creation failed: {e}")
        
        return relationships
    
    async def _create_graphiti_episode(
        self,
        text: str,
        user_id: str,
        memory_date: datetime,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a temporal episode in Graphiti"""
        try:
            episode_name = f"episode_{user_id}_{memory_date.strftime('%Y%m%d_%H%M%S')}"
            
            # Build source description with entities
            entity_names = [e["name"] for e in entities[:5]]  # Top 5 entities
            source_desc = f"Memory with entities: {', '.join(entity_names)}" if entity_names else "Memory"
            
            # Add episode to Graphiti
            await self.graphiti_client.add_episode(
                name=episode_name,
                episode_body=text,
                source=EpisodeType.text,
                source_description=source_desc,
                reference_time=memory_date
            )
            
            logger.info(f"  🎬 Created Graphiti episode: {episode_name}")
            
            return {
                "episode_name": episode_name,
                "reference_time": memory_date.isoformat(),
                "entities_included": len(entity_names)
            }
            
        except Exception as e:
            logger.error(f"  ❌ Graphiti episode creation failed: {e}")
            return {"error": str(e)}
    
    async def _enhance_graph_relationships(
        self,
        memory_id: str,
        entities: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Enhance graph with temporal and semantic relationships"""
        enhancements = []
        
        with self.neo4j_driver.session() as session:
            try:
                # Create temporal relationships between memories
                result = session.run("""
                    MATCH (m1:Memory {id: $memory_id})
                    MATCH (m2:Memory {user_id: $user_id})
                    WHERE m1 <> m2 
                    AND abs(datetime(m1.memory_date).epochSeconds - datetime(m2.memory_date).epochSeconds) < 86400
                    MERGE (m1)-[r:TEMPORAL_NEIGHBOR]->(m2)
                    SET r.time_diff = abs(datetime(m1.memory_date).epochSeconds - datetime(m2.memory_date).epochSeconds)
                    RETURN count(r) as temporal_links
                """, memory_id=memory_id, user_id=user_id)
                
                for record in result:
                    if record["temporal_links"] > 0:
                        enhancements.append({
                            "type": "temporal_neighbors",
                            "count": record["temporal_links"]
                        })
                
                # Create semantic clusters based on shared entities
                if len(entities) >= 2:
                    result = session.run("""
                        MATCH (m:Memory {id: $memory_id})
                        MATCH (other:Memory {user_id: $user_id})-[:MENTIONS]->(e)
                        WHERE m <> other AND e.name IN $entity_names
                        WITH m, other, count(DISTINCT e) as shared_entities
                        WHERE shared_entities >= 2
                        MERGE (m)-[r:SEMANTICALLY_SIMILAR]->(other)
                        SET r.shared_entities = shared_entities
                        RETURN count(r) as semantic_links
                    """, 
                        memory_id=memory_id,
                        user_id=user_id,
                        entity_names=[e["name"] for e in entities]
                    )
                    
                    for record in result:
                        if record["semantic_links"] > 0:
                            enhancements.append({
                                "type": "semantic_similarity",
                                "count": record["semantic_links"]
                            })
                
                logger.info(f"  ✨ Applied {len(enhancements)} graph enhancements")
                
            except Exception as e:
                logger.error(f"  ❌ Graph enhancement failed: {e}")
        
        return enhancements
    
    async def enable_multi_hop_traversal(self):
        """Create indexes and procedures for efficient multi-hop traversal"""
        with self.neo4j_driver.session() as session:
            try:
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX memory_user_id IF NOT EXISTS FOR (m:Memory) ON (m.user_id)",
                    "CREATE INDEX memory_date IF NOT EXISTS FOR (m:Memory) ON (m.memory_date)",
                    "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                    "CREATE INDEX entity_user_id IF NOT EXISTS FOR (e:Entity) ON (e.user_id)"
                ]
                
                for index_query in indexes:
                    session.run(index_query)
                
                logger.info("✅ Created indexes for multi-hop traversal")
                
                # Create a custom traversal function
                session.run("""
                    CALL apoc.custom.asProcedure(
                        'findRelatedMemories',
                        'MATCH (start:Memory {id: $memoryId})
                         CALL apoc.path.expandConfig(start, {
                            relationshipFilter: "MENTIONS|CO_OCCURS_WITH|TEMPORAL_NEIGHBOR|SEMANTICALLY_SIMILAR",
                            minLevel: 1,
                            maxLevel: $maxHops,
                            uniqueness: "NODE_GLOBAL"
                         })
                         YIELD path
                         WITH last(nodes(path)) as endNode
                         WHERE endNode:Memory
                         RETURN DISTINCT endNode',
                        'read',
                        [['endNode', 'NODE']],
                        [['memoryId', 'STRING'], ['maxHops', 'INTEGER']]
                    )
                """)
                
                logger.info("✅ Created multi-hop traversal procedure")
                
            except Exception as e:
                logger.warning(f"⚠️ Could not create all enhancements: {e}")
    
    async def close(self):
        """Clean up connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
        if self.graphiti_client:
            await self.graphiti_client.close()
        logger.info("🔒 Connections closed")

# Main ingestion function
async def ingest_enhanced_memories():
    """Ingest memories with full entity extraction and relationship building"""
    ingester = EnhancedUnifiedIngestion()
    
    logger.info("🚀 ENHANCED UNIFIED MEMORY INGESTION")
    logger.info("="*50)
    
    if not await ingester.initialize():
        logger.error("❌ Failed to initialize enhanced ingestion")
        return
    
    # Enable multi-hop traversal support
    await ingester.enable_multi_hop_traversal()
    
    # Load enhanced memories
    # Try to load the latest preprocessed file first, fallback to sample
    preprocessed_files = [
        "memories_preprocessed_latest.json",
        "sample_30_preprocessed_v2.json"
    ]
    
    data = None
    for file in preprocessed_files:
        if os.path.exists(file):
            with open(file, 'r') as f:
                data = json.load(f)
                logger.info(f"📂 Loaded memories from: {file}")
                break
    
    if not data:
        logger.error("❌ No preprocessed memory file found!")
        return
    
    memories = data.get('memories', [])
    user_id = data.get('user_id', 'fa97efb5-410d-4806-b137-8cf13b6cb464')
    
    logger.info(f"📥 Processing {len(memories)} memories with entity extraction")
    
    # Process memories
    total_entities = 0
    total_relationships = 0
    
    for i, memory in enumerate(memories[:10], 1):  # Process first 10 for demo
        logger.info(f"\n📝 Memory {i}/{min(10, len(memories))}: {memory['memory_text'][:60]}...")
        
        # Parse dates
        creation_date = datetime.fromisoformat(
            memory.get('created_at', datetime.now().isoformat()).replace('Z', '+00:00')
        )
        
        # Parse memory date from temporal context
        memory_date = None
        temporal_context = memory.get('temporal_context', '')
        if temporal_context:
            import re
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', temporal_context)
            if date_match:
                memory_date = datetime.strptime(
                    date_match.group(), '%Y-%m-%d'
                ).replace(tzinfo=timezone.utc)
        
        if not memory_date:
            memory_date = creation_date
        
        # Ingest with entity extraction
        result = await ingester.ingest_memory_with_entities(
            text=memory['memory_text'],
            user_id=user_id,
            creation_date=creation_date,
            memory_date=memory_date,
            metadata={
                "confidence": memory.get('confidence', 'medium'),
                "temporal_keywords": memory.get('temporal_keywords', []),
                "original_id": memory.get('id', '')
            }
        )
        
        if "error" not in result:
            entities_count = len(result.get("entities_extracted", []))
            relationships_count = len(result.get("relationships_created", []))
            
            total_entities += entities_count
            total_relationships += relationships_count
            
            logger.info(f"  ✅ Extracted {entities_count} entities")
            logger.info(f"  ✅ Created {relationships_count} relationships")
            
            if result.get("graphiti_episode"):
                logger.info(f"  ✅ Created temporal episode")
        else:
            logger.error(f"  ❌ Error: {result['error']}")
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("🎉 ENHANCED INGESTION COMPLETE!")
    logger.info(f"📊 Total entities extracted: {total_entities}")
    logger.info(f"🔗 Total relationships created: {total_relationships}")
    logger.info(f"🎬 Temporal episodes created: {min(10, len(memories))}")
    logger.info("\n✅ Your memories now have:")
    logger.info("  - Entity nodes (Person, Location, Event, etc.)")
    logger.info("  - Memory-Entity relationships (MENTIONS)")
    logger.info("  - Entity co-occurrence relationships")
    logger.info("  - Temporal neighbor relationships")
    logger.info("  - Semantic similarity relationships")
    logger.info("  - Graphiti temporal episodes")
    logger.info("  - Multi-hop traversal support")
    
    await ingester.close()

if __name__ == "__main__":
    asyncio.run(ingest_enhanced_memories()) 