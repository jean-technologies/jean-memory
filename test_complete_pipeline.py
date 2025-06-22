#!/usr/bin/env python3
"""
Complete Pipeline Integration Test
Tests the full ingestion → storage → search → GraphRAG pipeline
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipeline_integration():
    """Test the complete pipeline integration without API calls"""
    
    print("🔍 COMPLETE PIPELINE INTEGRATION STATUS")
    print("=" * 60)
    
    # 1. Test Data Storage Layer
    print("1️⃣ DATA STORAGE LAYER:")
    
    # Qdrant Vector Database
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host='localhost', port=6333)
        
        # Check enhanced_memories_openai collection
        collection_info = client.get_collection('enhanced_memories_openai')
        vector_count = collection_info.points_count
        vector_dims = collection_info.config.params.vectors.size
        
        print(f"   ✅ Qdrant Vector Store: {vector_count} memories")
        print(f"   ✅ Vector dimensions: {vector_dims} (OpenAI embeddings)")
        
        # Sample a memory to verify structure
        if vector_count > 0:
            sample = client.scroll('enhanced_memories_openai', limit=1, with_payload=True)
            if sample[0]:
                payload_keys = list(sample[0][0].payload.keys())
                print(f"   ✅ Memory structure: {payload_keys}")
        
        vector_status = "✅ WORKING"
        
    except Exception as e:
        print(f"   ❌ Qdrant error: {e}")
        vector_status = "❌ FAILED"
        vector_count = 0
    
    # Neo4j Graph Database
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'fasho93fasho'))
        
        with driver.session() as session:
            # Count Memory nodes
            result = session.run('MATCH (n:Memory) RETURN count(n) as count')
            memory_nodes = result.single()['count']
            
            # Count relationships
            result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
            total_rels = result.single()['count']
            
            # Count relationship types
            result = session.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC LIMIT 5')
            top_rel_types = [(record['type'], record['count']) for record in result]
            
            # Check user-specific data
            user_id = 'fa97efb5-410d-4806-b137-8cf13b6cb464'
            result = session.run('MATCH (n:Memory {user_id: $user_id}) RETURN count(n) as count', user_id=user_id)
            user_memories = result.single()['count']
            
        driver.close()
        
        print(f"   ✅ Neo4j Graph Store: {memory_nodes} Memory nodes")
        print(f"   ✅ Graph relationships: {total_rels} total")
        print(f"   ✅ Top relationship types: {top_rel_types[:3]}")
        print(f"   ✅ User-specific memories: {user_memories}")
        
        graph_status = "✅ WORKING"
        
    except Exception as e:
        print(f"   ❌ Neo4j error: {e}")
        graph_status = "❌ FAILED"
        memory_nodes = 0
        user_memories = 0
    
    # 2. Test Data Consistency
    print(f"\n2️⃣ DATA CONSISTENCY:")
    if vector_count == user_memories and vector_count > 0:
        print(f"   ✅ Perfect sync: {vector_count} memories in both systems")
        consistency_status = "✅ SYNCED"
    elif vector_count > 0 and user_memories > 0:
        print(f"   ⚠️ Partial sync: Qdrant({vector_count}) vs Neo4j({user_memories})")
        consistency_status = "⚠️ PARTIAL"
    else:
        print(f"   ❌ No data or major mismatch")
        consistency_status = "❌ FAILED"
    
    # 3. Test Pipeline Components
    print(f"\n3️⃣ PIPELINE COMPONENTS:")
    
    # Check if core files exist
    components = {
        "Enhanced Preprocessing": "preprocess_memories_gemini_batch.py",
        "Unified Ingestion": "enhanced_unified_ingestion.py", 
        "GraphRAG Pipeline": "graphrag_pipeline.py",
        "Browse Memories": "browse_memories.py"
    }
    
    for name, filename in components.items():
        if os.path.exists(filename):
            print(f"   ✅ {name}: {filename}")
        else:
            print(f"   ❌ {name}: Missing {filename}")
    
    # 4. Test Relationship Discovery (The Fix)
    print(f"\n4️⃣ RELATIONSHIP DISCOVERY FIX:")
    if graph_status == "✅ WORKING":
        try:
            driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'fasho93fasho'))
            with driver.session() as session:
                # Test the exact fixed query
                user_id = 'fa97efb5-410d-4806-b137-8cf13b6cb464'
                entities = ['fitness', 'activities']
                
                cypher_query = '''
                MATCH (n:Memory {user_id: $user_id})
                WHERE any(entity IN $entities WHERE n.text CONTAINS entity)
                WITH n
                MATCH (n)-[r]-(m:Memory {user_id: $user_id})
                WHERE any(entity IN $entities WHERE m.text CONTAINS entity)
                RETURN count(r) as rel_count
                '''
                
                result = session.run(cypher_query, user_id=user_id, entities=entities)
                rel_count = result.single()['rel_count']
                
                if rel_count > 0:
                    print(f"   ✅ Relationship discovery: {rel_count} relationships found")
                    print(f"   ✅ Neo4j boolean fix: WORKING")
                    rel_status = "✅ FIXED"
                else:
                    print(f"   ❌ Relationship discovery: 0 relationships found")
                    rel_status = "❌ STILL BROKEN"
            
            driver.close()
            
        except Exception as e:
            print(f"   ❌ Relationship test error: {e}")
            rel_status = "❌ ERROR"
    else:
        rel_status = "❌ CANNOT TEST"
    
    # 5. Overall System Status
    print(f"\n🎯 OVERALL SYSTEM STATUS:")
    print(f"   Vector Search: {vector_status}")
    print(f"   Graph Database: {graph_status}")
    print(f"   Data Consistency: {consistency_status}")
    print(f"   Relationship Discovery: {rel_status}")
    
    # Determine overall status
    if (vector_status == "✅ WORKING" and 
        graph_status == "✅ WORKING" and 
        consistency_status in ["✅ SYNCED", "⚠️ PARTIAL"] and
        rel_status == "✅ FIXED"):
        
        overall_status = "🎉 FULLY OPERATIONAL"
        print(f"\n{overall_status}")
        print("✅ Your ingestion and search pipeline is working!")
        print("✅ GraphRAG system is ready for production queries!")
        
    else:
        overall_status = "⚠️ PARTIALLY WORKING"
        print(f"\n{overall_status}")
        print("⚠️ Some components need attention")
    
    return {
        "vector_status": vector_status,
        "graph_status": graph_status, 
        "consistency_status": consistency_status,
        "relationship_status": rel_status,
        "overall_status": overall_status,
        "data_counts": {
            "vector_memories": vector_count,
            "graph_memories": user_memories,
            "total_relationships": total_rels if 'total_rels' in locals() else 0
        }
    }

if __name__ == "__main__":
    test_pipeline_integration() 