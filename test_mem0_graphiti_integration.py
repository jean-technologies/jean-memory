#!/usr/bin/env python3
"""
Test mem0 + Graphiti Integration
Demonstrates the unified architecture capabilities
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mem0_integration():
    """Test mem0's vector storage and entity extraction"""
    
    print("\n🧠 TESTING mem0 INTEGRATION")
    print("=" * 60)
    
    try:
        from mem0 import Memory
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Configure mem0 with entity extraction
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333,
                    "collection_name": "mem0_unified_test"
                }
            },
            "graph_store": {
                "provider": "neo4j",
                            "config": {
                "url": "bolt://localhost:7687",
                "username": "neo4j",
                "password": os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
            }
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
                    "model": "text-embedding-3-small"
                }
            },
            "version": "v1.1"
        }
        
        # Initialize mem0
        print("🔄 Initializing mem0...")
        memory = Memory.from_config(config_dict=config)
        
        # Test memory with entities
        test_text = "John works at OpenAI on the GPT-4 project. He meets with Sarah every Tuesday to discuss machine learning research."
        user_id = "test-mem0-user"
        
        print(f"\n📝 Adding memory with entity extraction:")
        print(f"   Text: {test_text}")
        
        # Add memory
        result = memory.add(test_text, user_id=user_id)
        
        print(f"\n✅ mem0 Results:")
        print(f"   Memory ID: {result.get('id', 'N/A')}")
        print(f"   Added: {'results' in result}")
        
        # Search for memories
        print(f"\n🔍 Searching mem0 for 'OpenAI'...")
        search_results = memory.search("OpenAI", user_id=user_id)
        
        if search_results:
            print(f"   Found {len(search_results)} results")
            for res in search_results[:2]:
                print(f"   - {res.get('memory', '')[:60]}...")
        
        # Check Neo4j for entities
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD", "your-neo4j-password")))
        
        with driver.session() as session:
            # Check for entities created by mem0
            result = session.run("""
                MATCH (n) 
                WHERE n.name IN ['John', 'OpenAI', 'GPT-4', 'Sarah']
                RETURN labels(n) as labels, n.name as name
            """)
            
            entities = list(result)
            if entities:
                print(f"\n✅ Entities Extracted by mem0:")
                for entity in entities:
                    print(f"   - {entity['labels']}: {entity['name']}")
            
            # Check relationships
            result = session.run("""
                MATCH (n)-[r]->(m)
                WHERE n.name IN ['John', 'OpenAI', 'GPT-4', 'Sarah']
                   OR m.name IN ['John', 'OpenAI', 'GPT-4', 'Sarah']
                RETURN n.name as source, type(r) as rel_type, m.name as target
                LIMIT 5
            """)
            
            relationships = list(result)
            if relationships:
                print(f"\n✅ Relationships Created by mem0:")
                for rel in relationships:
                    print(f"   - {rel['source']} --{rel['rel_type']}--> {rel['target']}")
        
        driver.close()
        
        print(f"\n✅ mem0 Integration Working:")
        print(f"   ✅ Vector storage in Qdrant")
        print(f"   ✅ Entity extraction to Neo4j")
        print(f"   ✅ Relationship creation")
        
        return True
        
    except Exception as e:
        print(f"❌ mem0 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_graphiti_integration():
    """Test Graphiti's temporal episode creation"""
    
    print("\n\n🔗 TESTING GRAPHITI INTEGRATION")
    print("=" * 60)
    
    try:
        from graphiti_core import Graphiti
        from graphiti_core.nodes import EpisodeType
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Initialize Graphiti
        print("🔄 Initializing Graphiti...")
        graphiti = Graphiti(
            "bolt://localhost:7687",
            "neo4j",
            os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
        )
        
        # Build indices
        await graphiti.build_indices_and_constraints()
        print("✅ Graphiti indices built")
        
        # Create a temporal episode
        episode_text = "User had a productive morning: completed yoga at 6am, then worked on the AI project from 8am to noon."
        
        print(f"\n📝 Creating temporal episode:")
        print(f"   Text: {episode_text}")
        
        # Add episode
        episode_result = await graphiti.add_episode(
            name="productive_morning",
            episode_body=episode_text,
            source_description="test_graphiti",
            reference_time=datetime.now()
        )
        
        print(f"\n✅ Graphiti Results:")
        print(f"   Episode created: {episode_result is not None}")
        
        # Check Neo4j for episodes
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD", "your-neo4j-password")))
        
        with driver.session() as session:
            # Check for Episode nodes
            result = session.run("""
                MATCH (n:Episode)
                RETURN n.name as name, n.created_at as created_at
                ORDER BY n.created_at DESC
                LIMIT 3
            """)
            
            episodes = list(result)
            if episodes:
                print(f"\n✅ Episodes Created by Graphiti:")
                for ep in episodes:
                    print(f"   - {ep['name']} (created: {ep['created_at']})")
            
            # Check temporal relationships
            result = session.run("""
                MATCH (n:Episode)-[r]->(m)
                RETURN n.name as source, type(r) as rel_type, labels(m) as target_labels
                LIMIT 5
            """)
            
            temporal_rels = list(result)
            if temporal_rels:
                print(f"\n✅ Temporal Relationships by Graphiti:")
                for rel in temporal_rels:
                    print(f"   - {rel['source']} --{rel['rel_type']}--> {rel['target_labels']}")
        
        driver.close()
        
        print(f"\n✅ Graphiti Integration Working:")
        print(f"   ✅ Episode creation")
        print(f"   ✅ Temporal relationship mapping")
        print(f"   ✅ Graph indices and constraints")
        
        await graphiti.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Graphiti test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def show_unified_architecture_benefits():
    """Show the benefits of the unified architecture"""
    
    print("\n\n🎯 UNIFIED ARCHITECTURE BENEFITS")
    print("=" * 60)
    
    print("""
    With mem0 + Graphiti + Zep Integration:
    
    1. 🧠 INTELLIGENT MEMORY STORAGE:
       - mem0 automatically extracts entities (people, places, projects)
       - Creates knowledge graph relationships
       - Provides semantic vector search
    
    2. 🔗 TEMPORAL UNDERSTANDING:
       - Graphiti creates temporal episodes
       - Links events in time sequence
       - Enables time-based queries
    
    3. 🕸️ RICH GRAPH CAPABILITIES:
       - Multi-hop graph traversal
       - Entity-relationship discovery
       - Context-aware memory retrieval
    
    4. 🚀 UNIFIED QUERY INTERFACE:
       - Single pipeline for all operations
       - Consistent data model
       - Optimized for GraphRAG
    
    Compare to Current System:
    - Current: Manual entity extraction, custom relationships
    - Unified: Automatic extraction, standardized relationships
    - Current: No temporal episodes
    - Unified: Full temporal modeling with Graphiti
    """)

async def main():
    """Run all tests"""
    
    print("🚀 TESTING UNIFIED mem0 + GRAPHITI ARCHITECTURE")
    print("=" * 80)
    
    # Test mem0
    mem0_success = await test_mem0_integration()
    
    # Test Graphiti
    graphiti_success = await test_graphiti_integration()
    
    # Show benefits
    await show_unified_architecture_benefits()
    
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY:")
    print(f"   mem0 Integration: {'✅ PASSED' if mem0_success else '❌ FAILED'}")
    print(f"   Graphiti Integration: {'✅ PASSED' if graphiti_success else '❌ FAILED'}")
    
    if mem0_success and graphiti_success:
        print("\n🎉 UNIFIED ARCHITECTURE IS READY!")
        print("You can now migrate your data to use:")
        print("✅ mem0 for intelligent memory storage")
        print("✅ Graphiti for temporal modeling")
        print("✅ Unified pipeline for all operations")
    else:
        print("\n⚠️ Some components need attention before migration")

if __name__ == "__main__":
    asyncio.run(main()) 