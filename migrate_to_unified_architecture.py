#!/usr/bin/env python3
"""
Migrate to Unified mem0 + Graphiti Architecture
Practical migration script that handles the current data
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def migrate_to_unified_system():
    """Migrate existing data to unified mem0 + Graphiti system"""
    
    print("🚀 MIGRATING TO UNIFIED ARCHITECTURE")
    print("=" * 80)
    
    try:
        from qdrant_client import QdrantClient
        from neo4j import GraphDatabase
        from mem0 import Memory
        from graphiti_core import Graphiti
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Step 1: Fetch existing memories
        print("\n📥 STEP 1: Fetching existing memories...")
        qdrant_client = QdrantClient(host="localhost", port=6333)
        
        existing_memories = []
        offset = None
        
        while True:
            batch, offset = qdrant_client.scroll(
                collection_name="enhanced_memories_openai",
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            if not batch:
                break
                
            existing_memories.extend(batch)
            
            if offset is None:
                break
        
        print(f"✅ Found {len(existing_memories)} memories to migrate")
        
        # Step 2: Clean up SQLite issue
        print("\n🧹 STEP 2: Cleaning up SQLite history...")
        history_db = Path(".mem0_history.db")
        if history_db.exists():
            history_db.unlink()
            print("✅ Cleaned up SQLite history")
        
        # Step 3: Initialize mem0 with proper configuration
        print("\n🧠 STEP 3: Initializing mem0...")
        mem0_config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": "localhost",
                    "port": 6333,
                    "collection_name": "unified_memory_mem0"
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": "bolt://localhost:7687",
                    "username": "neo4j",
                    "password": "fasho93fasho"
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-4o-mini"
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
        
        memory = Memory.from_config(config_dict=mem0_config)
        print("✅ mem0 initialized")
        
        # Step 4: Initialize Graphiti
        print("\n🔗 STEP 4: Initializing Graphiti...")
        graphiti = Graphiti(
            "bolt://localhost:7687",
            "neo4j",
            "fasho93fasho"
        )
        await graphiti.build_indices_and_constraints()
        print("✅ Graphiti initialized")
        
        # Step 5: Migrate memories
        print("\n📦 STEP 5: Migrating memories...")
        user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
        
        migrated_count = 0
        failed_count = 0
        
        # Group memories by temporal context for episode creation
        temporal_groups = {}
        
        for i, memory_point in enumerate(existing_memories):
            try:
                payload = memory_point.payload
                memory_text = payload.get("text", "")
                temporal_context = payload.get("temporal_context", "Unknown")
                
                # Add to mem0
                print(f"\n   Processing memory {i+1}/{len(existing_memories)}...")
                print(f"   Text: {memory_text[:60]}...")
                
                # Add memory with mem0 (entity extraction)
                mem0_result = memory.add(
                    memory_text,
                    user_id=user_id,
                    metadata={
                        "temporal_context": temporal_context,
                        "confidence": payload.get("confidence", "medium"),
                        "migrated_from": "enhanced_memories_openai"
                    }
                )
                
                print(f"   ✅ Added to mem0: {mem0_result.get('id', 'N/A')}")
                
                # Group by temporal context for episodes
                if temporal_context not in temporal_groups:
                    temporal_groups[temporal_context] = []
                temporal_groups[temporal_context].append(memory_text)
                
                migrated_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to migrate memory {i}: {e}")
        
        # Step 6: Create temporal episodes with Graphiti
        print(f"\n🎬 STEP 6: Creating temporal episodes...")
        episode_count = 0
        
        for context, memories in temporal_groups.items():
            if len(memories) > 1:  # Only create episodes for grouped memories
                try:
                    episode_text = f"{context}: " + " | ".join(memories[:3])  # First 3 memories
                    episode_name = f"episode_{context.lower().replace(' ', '_')[:30]}"
                    
                    await graphiti.add_episode(
                        name=episode_name,
                        episode_body=episode_text,
                        source_description="migrated_memories",
                        reference_time=datetime.now()
                    )
                    
                    episode_count += 1
                    print(f"   ✅ Created episode: {episode_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create episode for {context}: {e}")
        
        # Step 7: Verify migration
        print(f"\n🔍 STEP 7: Verifying migration...")
        
        # Check mem0 collection
        try:
            mem0_collection = qdrant_client.get_collection("unified_memory_mem0")
            print(f"✅ mem0 collection: {mem0_collection.points_count} memories")
        except:
            print("❌ mem0 collection not found")
        
        # Check Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "fasho93fasho"))
        
        with driver.session() as session:
            # Count entities
            result = session.run("MATCH (n:Entity) RETURN count(n) as count")
            entity_count = result.single()["count"]
            print(f"✅ Entity nodes: {entity_count}")
            
            # Count episodes
            result = session.run("MATCH (n:Episodic) RETURN count(n) as count")
            episodic_count = result.single()["count"]
            print(f"✅ Episodic nodes: {episodic_count}")
            
            # Count relationships
            result = session.run("""
                MATCH ()-[r]->() 
                WHERE type(r) IN ['MENTIONS', 'RELATES_TO', 'PART_OF', 'HAS_ENTITY']
                RETURN type(r) as type, count(r) as count
            """)
            
            print("✅ Relationships created:")
            for record in result:
                print(f"   - {record['type']}: {record['count']}")
        
        driver.close()
        await graphiti.close()
        
        # Final summary
        print(f"\n🎉 MIGRATION COMPLETE!")
        print(f"   Memories migrated: {migrated_count}")
        print(f"   Episodes created: {episode_count}")
        print(f"   Failed: {failed_count}")
        
        print(f"\n✅ YOUR SYSTEM NOW USES:")
        print(f"   ✅ mem0 for vector storage and entity extraction")
        print(f"   ✅ Graphiti for temporal episode modeling")
        print(f"   ✅ Unified architecture for GraphRAG queries")
        
        # Update GraphRAG pipeline configuration
        print(f"\n📝 Next steps:")
        print(f"   1. Update GraphRAG pipeline to use 'unified_memory_mem0' collection")
        print(f"   2. Test queries with the new unified system")
        print(f"   3. Remove old 'enhanced_memories_openai' collection when ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(migrate_to_unified_system()) 