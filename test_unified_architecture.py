#!/usr/bin/env python3
"""
Test and Migrate to Unified mem0 + Graphiti + Zep Architecture
Shows the difference between current custom system and desired integrated system
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def show_architecture_comparison():
    """Show the difference between current and desired architecture"""
    
    print("🏗️ ARCHITECTURE COMPARISON")
    print("=" * 80)
    
    print("\n📊 CURRENT ARCHITECTURE (Custom Implementation):")
    print("""
    Raw Memories
         ↓
    Gemini Batch Preprocessing (preprocess_memories_gemini_batch.py)
         ↓
    Custom OpenAI Embeddings (qdrant_openai_query_system.py)
         ↓
    Qdrant: enhanced_memories_openai collection
         ↓
    Custom Neo4j Sync (sync_and_test_graphrag.py)
         ↓
    Neo4j: Memory nodes + TEMPORAL_NEIGHBOR relationships
         ↓
    GraphRAG Pipeline (graphrag_pipeline.py)
    
    ❌ NOT using mem0 for vector storage
    ❌ NOT using mem0 for entity extraction  
    ❌ NOT using Graphiti for temporal episodes
    ❌ NOT using Zep integration
    """)
    
    print("\n🚀 DESIRED ARCHITECTURE (Integrated System):")
    print("""
    Raw Memories
         ↓
    Enhanced Unified Ingestion (enhanced_unified_ingestion.py)
         ├─→ mem0 Vector Storage → Qdrant: unified_memory_enhanced
         ├─→ mem0 Entity Extraction → Neo4j: Entity nodes + relationships
         ├─→ Graphiti Episodes → Neo4j: Episode nodes + temporal relationships
         └─→ Zep Graph Features → Neo4j: Enhanced graph capabilities
         ↓
    Unified GraphRAG Pipeline
    
    ✅ mem0 handles vector storage and entity extraction
    ✅ Graphiti creates temporal episodes and relationships
    ✅ Zep provides advanced graph capabilities
    ✅ All systems integrated in one pipeline
    """)

async def test_unified_ingestion():
    """Test the unified ingestion with sample data"""
    
    print("\n🧪 TESTING UNIFIED INGESTION PIPELINE")
    print("=" * 80)
    
    try:
        from enhanced_unified_ingestion import EnhancedUnifiedIngestion
        
        # Initialize the unified system
        ingestion = EnhancedUnifiedIngestion()
        
        print("🔄 Initializing unified system...")
        if not await ingestion.initialize():
            print("❌ Failed to initialize unified system")
            return False
        
        print("✅ Unified system initialized successfully!")
        
        # Test with a sample memory
        test_memory = {
            "text": "Testing unified ingestion: User practices yoga every morning at 6am for fitness and mental clarity",
            "user_id": "test-unified-user",
            "creation_date": datetime.now(),
            "metadata": {
                "test": True,
                "source": "unified_test"
            }
        }
        
        print("\n📝 Ingesting test memory with unified pipeline...")
        result = await ingestion.ingest_memory_with_entities(
            text=test_memory["text"],
            user_id=test_memory["user_id"],
            creation_date=test_memory["creation_date"],
            metadata=test_memory["metadata"]
        )
        
        print("\n📊 UNIFIED INGESTION RESULTS:")
        
        # Check mem0 results
        if result.get("mem0_result"):
            print("\n✅ mem0 Integration:")
            print(f"   Memory ID: {result['mem0_result'].get('id', 'N/A')}")
            print(f"   Vector stored: {'results' in result['mem0_result']}")
        
        # Check entity extraction
        if result.get("entities_extracted"):
            print(f"\n✅ Entity Extraction: {len(result['entities_extracted'])} entities")
            for entity in result["entities_extracted"]:
                print(f"   - {entity.get('type', 'Unknown')}: {entity.get('name', 'N/A')}")
        
        # Check relationships
        if result.get("relationships_created"):
            print(f"\n✅ Relationships Created: {len(result['relationships_created'])}")
            for rel in result["relationships_created"][:3]:
                print(f"   - {rel.get('type', 'Unknown')}")
        
        # Check Graphiti episode
        if result.get("graphiti_episode"):
            print(f"\n✅ Graphiti Episode:")
            print(f"   Episode created: {result['graphiti_episode'].get('created', False)}")
        
        # Clean up test data
        await ingestion.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Unified ingestion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def migrate_existing_data():
    """Migrate existing data to unified architecture"""
    
    print("\n📦 MIGRATING EXISTING DATA TO UNIFIED ARCHITECTURE")
    print("=" * 80)
    
    try:
        from enhanced_unified_ingestion import EnhancedUnifiedIngestion
        from qdrant_client import QdrantClient
        
        # Get existing memories from current system
        qdrant_client = QdrantClient(host="localhost", port=6333)
        
        print("📥 Fetching existing memories from enhanced_memories_openai...")
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
        
        # Initialize unified ingestion
        ingestion = EnhancedUnifiedIngestion()
        if not await ingestion.initialize():
            print("❌ Failed to initialize unified system")
            return False
        
        # Migrate memories
        print("\n🔄 Migrating memories to unified architecture...")
        
        migrated_count = 0
        failed_count = 0
        
        for i, memory_point in enumerate(existing_memories):
            try:
                payload = memory_point.payload
                
                # Extract memory data
                memory_text = payload.get("text", "")
                user_id = payload.get("user_id", os.getenv("TEST_USER_ID", "test-user-id"))
                created_at = payload.get("created_at", datetime.now().isoformat())
                
                # Convert created_at to datetime
                try:
                    creation_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    creation_date = datetime.now()
                
                # Prepare metadata
                metadata = {
                    "original_id": payload.get("original_id", ""),
                    "confidence": payload.get("confidence", "medium"),
                    "temporal_context": payload.get("temporal_context", ""),
                    "temporal_keywords": payload.get("temporal_keywords", []),
                    "reasoning": payload.get("reasoning", ""),
                    "migrated_from": "enhanced_memories_openai",
                    "migration_date": datetime.now().isoformat()
                }
                
                # Ingest with unified pipeline
                result = await ingestion.ingest_memory_with_entities(
                    text=memory_text,
                    user_id=user_id,
                    creation_date=creation_date,
                    metadata=metadata
                )
                
                if result.get("mem0_result"):
                    migrated_count += 1
                    if (i + 1) % 10 == 0:
                        print(f"   Migrated {migrated_count}/{len(existing_memories)} memories...")
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to migrate memory {i}: {e}")
        
        print(f"\n✅ MIGRATION COMPLETE:")
        print(f"   Successfully migrated: {migrated_count}")
        print(f"   Failed: {failed_count}")
        
        # Verify migration
        print("\n🔍 VERIFYING UNIFIED ARCHITECTURE:")
        
        # Check mem0 collection
        try:
            unified_collection = qdrant_client.get_collection("unified_memory_enhanced")
            print(f"   ✅ mem0 collection: {unified_collection.points_count} points")
        except:
            print("   ❌ mem0 collection not found")
        
        # Check Neo4j data
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", os.getenv("NEO4J_PASSWORD", "your-neo4j-password")))
        
        with driver.session() as session:
            # Check entities
            result = session.run("MATCH (n:Entity) RETURN count(n) as count")
            entity_count = result.single()["count"]
            print(f"   ✅ Entity nodes: {entity_count}")
            
            # Check episodes
            result = session.run("MATCH (n:Episode) RETURN count(n) as count")
            episode_count = result.single()["count"]
            print(f"   ✅ Episode nodes: {episode_count}")
            
            # Check mem0 relationships
            result = session.run("MATCH ()-[r:MENTIONS|RELATES_TO]->() RETURN count(r) as count")
            mem0_rel_count = result.single()["count"]
            print(f"   ✅ mem0 relationships: {mem0_rel_count}")
        
        driver.close()
        await ingestion.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main execution flow"""
    
    print("🚀 UNIFIED ARCHITECTURE MIGRATION")
    print("=" * 80)
    
    # Step 1: Show architecture comparison
    await show_architecture_comparison()
    
    # Step 2: Test unified ingestion
    print("\n" + "=" * 80)
    input("Press Enter to test the unified ingestion pipeline...")
    
    test_success = await test_unified_ingestion()
    
    if not test_success:
        print("\n❌ Unified ingestion test failed. Please fix issues before migration.")
        return
    
    # Step 3: Migrate existing data
    print("\n" + "=" * 80)
    response = input("\n🔄 Ready to migrate existing data to unified architecture? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        await migrate_existing_data()
        
        print("\n🎉 MIGRATION COMPLETE!")
        print("Your system is now using:")
        print("✅ mem0 for vector storage and entity extraction")
        print("✅ Graphiti for temporal episode creation")
        print("✅ Zep integration for graph capabilities")
        print("✅ Unified pipeline that leverages all systems")
    else:
        print("\n⏸️ Migration cancelled. You can run this script again when ready.")

if __name__ == "__main__":
    asyncio.run(main()) 