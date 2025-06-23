#!/usr/bin/env python3
"""
Sync Qdrant data to Neo4j and test full GraphRAG pipeline
This will create proper Memory nodes in Neo4j to test graph expansion
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
from graphrag_pipeline import GraphRAGPipeline

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def sync_qdrant_to_neo4j():
    """Sync existing Qdrant memories to Neo4j as Memory nodes"""
    
    logger.info("🔄 Syncing Qdrant data to Neo4j...")
    
    # Connect to Qdrant
    qdrant_client = QdrantClient(host='localhost', port=6333)
    
    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(
        'bolt://localhost:7687', 
        auth=('neo4j', 'fasho93fasho')
    )
    
    try:
        # Get all memories from enhanced_memories_openai collection
        points = qdrant_client.scroll(
            collection_name="enhanced_memories_openai",
            limit=100,
            with_payload=True
        )
        
        memories = points[0]  # Get the actual points
        logger.info(f"📥 Found {len(memories)} memories in Qdrant")
        
        # Create Memory nodes in Neo4j
        with neo4j_driver.session() as session:
            # Clear existing Memory nodes for clean test
            session.run("MATCH (n:Memory) DELETE n")
            logger.info("🧹 Cleared existing Memory nodes")
            
            created_count = 0
            for memory in memories:
                payload = memory.payload
                
                # Create Memory node with the structure GraphRAG expects
                cypher = """
                CREATE (m:Memory {
                    id: $id,
                    user_id: $user_id,
                    text: $text,
                    temporal_context: $temporal_context,
                    temporal_keywords: $temporal_keywords,
                    confidence: $confidence,
                    created_at: $created_at,
                    source: $source
                })
                """
                
                session.run(cypher, 
                    id=str(memory.id),
                    user_id=payload.get('user_id', 'unknown'),
                    text=payload.get('text', ''),
                    temporal_context=payload.get('temporal_context', ''),
                    temporal_keywords=payload.get('temporal_keywords', []),
                    confidence=payload.get('confidence', 'medium'),
                    created_at=payload.get('created_at', datetime.now().isoformat()),
                    source=payload.get('source', 'qdrant_sync')
                )
                created_count += 1
            
            # Create some relationships based on temporal proximity and shared entities
            logger.info("🔗 Creating relationships between memories...")
            
            # Create temporal relationships (memories from same time period)
            temporal_relationship_cypher = """
            MATCH (m1:Memory), (m2:Memory)
            WHERE m1.user_id = m2.user_id 
            AND m1.id <> m2.id
            AND m1.temporal_context CONTAINS '2025-06-17'
            AND m2.temporal_context CONTAINS '2025-06-17'
            CREATE (m1)-[:TEMPORAL_NEIGHBOR]->(m2)
            """
            result = session.run(temporal_relationship_cypher)
            temporal_rels = result.consume().counters.relationships_created
            
            # Create entity-based relationships (memories mentioning similar things)
            entity_relationship_cypher = """
            MATCH (m1:Memory), (m2:Memory)
            WHERE m1.user_id = m2.user_id 
            AND m1.id <> m2.id
            AND (
                (m1.text CONTAINS 'fitness' AND m2.text CONTAINS 'fitness') OR
                (m1.text CONTAINS 'gym' AND m2.text CONTAINS 'gym') OR
                (m1.text CONTAINS 'protein' AND m2.text CONTAINS 'nutrition') OR
                (m1.text CONTAINS 'YC' AND m2.text CONTAINS 'interview')
            )
            CREATE (m1)-[:RELATED_TOPIC]->(m2)
            """
            result = session.run(entity_relationship_cypher)
            topic_rels = result.consume().counters.relationships_created
            
            logger.info(f"✅ Created {created_count} Memory nodes")
            logger.info(f"✅ Created {temporal_rels} temporal relationships")
            logger.info(f"✅ Created {topic_rels} topic relationships")
            
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        return False
    finally:
        qdrant_client.close()
        neo4j_driver.close()
    
    return True

async def test_full_graphrag_pipeline():
    """Test the GraphRAG pipeline with real synced data"""
    
    logger.info("🧪 Testing Full GraphRAG Pipeline with Real Data")
    logger.info("=" * 60)
    
    # Initialize pipeline
    pipeline = GraphRAGPipeline()
    await pipeline.initialize()
    
    # Test with real user ID from our data
    test_user_id = "test-user-id-placeholder"
    
    # Test queries that should find data in our synced memories
    test_queries = [
        "What fitness activities do I do?",
        "Tell me about my work activities",
        "What did I do on June 17th?"
    ]
    
    for query in test_queries:
        logger.info(f"\n🔍 Testing Query: '{query}'")
        logger.info("-" * 40)
        
        try:
            result = await pipeline.process_query(query, test_user_id)
            
            # Analyze the results
            logger.info(f"📊 RESULTS ANALYSIS:")
            logger.info(f"  Response length: {len(result.get('response', ''))}")
            logger.info(f"  Processing time: {result.get('processing_time', 'unknown')}")
            
            # Check if graph expansion found data
            if 'debug_info' in result:
                debug = result['debug_info']
                logger.info(f"  Vector search results: {len(debug.get('seed_memories', []))}")
                logger.info(f"  Graph nodes found: {len(debug.get('expanded_context', {}).get('nodes', []))}")
                logger.info(f"  Graph relationships: {len(debug.get('expanded_context', {}).get('relationships', []))}")
            
            # Show response preview
            response_preview = result.get('response', '')[:200]
            logger.info(f"  Response preview: {response_preview}...")
            
        except Exception as e:
            logger.error(f"  ❌ Query failed: {e}")
    
    logger.info(f"\n🎉 Full GraphRAG Pipeline Test Completed!")

async def main():
    """Main test execution"""
    
    print("🚀 GraphRAG Data Sync and Full Pipeline Test")
    print("=" * 50)
    
    # Step 1: Sync data
    sync_success = await sync_qdrant_to_neo4j()
    if not sync_success:
        print("❌ Data sync failed, aborting test")
        return 1
    
    # Step 2: Test full pipeline
    await test_full_graphrag_pipeline()
    
    print("\n✅ Test completed! Check logs above for detailed analysis.")
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 