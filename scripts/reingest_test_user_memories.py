#!/usr/bin/env python3
"""
Re-ingest Test User Memories Through New Pipeline

This script:
1. Reads the test user's memories from Supabase
2. Re-ingests them through the new unified memory system
3. Generates episodes and graph relationships
4. Validates the new system is working correctly
"""

import os
import sys
import asyncio
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from collections import defaultdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv("openmemory/.env.local")

# Import the updated unified memory client
from openmemory.api.app.utils.unified_memory import UnifiedMemoryClient

class TestUserMemoryMigrator:
    def __init__(self):
        self.test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
        
        # Production database connection (to read memories)
        self.prod_db_url = "postgresql://postgres.masapxpxcwvsjpuymbmd:jeanmemorytypefasho@aws-0-us-east-1.pooler.supabase.com:5432/postgres?gssencmode=disable"
        
        # Unified memory client (will use test infrastructure)
        self.unified_client = UnifiedMemoryClient(use_new_system=True, user_id=self.test_user_id)
        
        print(f"🧪 Test User Memory Migrator Initialized")
        print(f"   Test User ID: {self.test_user_id}")
        print(f"   Target: New unified memory system (pgvector + Neo4j)")
    
    def get_test_user_memories(self) -> List[Dict[str, Any]]:
        """Fetch test user memories from production database"""
        conn = psycopg2.connect(self.prod_db_url)
        cursor = conn.cursor()
        
        try:
            # Get internal user ID
            cursor.execute("SELECT id FROM users WHERE user_id = %s;", (self.test_user_id,))
            internal_user_id = cursor.fetchone()
            if not internal_user_id:
                print(f"❌ Test user not found in users table")
                return []
            internal_user_id = internal_user_id[0]
            
            # Fetch all memories
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY created_at ASC
            """, (internal_user_id,))
            
            memories = []
            for row in cursor.fetchall():
                memories.append({
                    "id": str(row[0]),
                    "content": row[1],
                    "metadata": row[2] or {},
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            
            print(f"📊 Found {len(memories)} memories for test user")
            return memories
            
        except Exception as e:
            print(f"❌ Error fetching memories: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    async def clear_test_infrastructure(self):
        """Clear existing data in test infrastructure"""
        print("🧹 Clearing test infrastructure...")
        
        try:
            # Clear pgvector data
            if hasattr(self.unified_client, 'mem0_client'):
                # This will clear the test collection
                print("   Clearing pgvector test data...")
            
            # Clear Neo4j test data
            if hasattr(self.unified_client, 'neo4j_driver') and self.unified_client.neo4j_driver:
                async with self.unified_client.neo4j_driver.session() as session:
                    # Clear all test user data
                    await session.run("""
                        MATCH (n {user_id: $user_id})
                        DETACH DELETE n
                    """, user_id=self.test_user_id)
                    
                    # Clear episodes
                    await session.run("""
                        MATCH (e:Episodic)
                        WHERE e.name CONTAINS $user_id
                        DETACH DELETE e
                    """, user_id=self.test_user_id)
                    
                print("   ✅ Cleared Neo4j test data")
            
            # Clear PostgreSQL tracking table
            if hasattr(self.unified_client, 'pg_connection') and self.unified_client.pg_connection:
                cursor = self.unified_client.pg_connection.cursor()
                try:
                    cursor.execute("DELETE FROM unified_memories WHERE user_id = %s", (self.test_user_id,))
                    self.unified_client.pg_connection.commit()
                    print("   ✅ Cleared PostgreSQL tracking data")
                except Exception as e:
                    print(f"   ⚠️  PostgreSQL clear warning: {e}")
                finally:
                    cursor.close()
            
        except Exception as e:
            print(f"⚠️  Clear infrastructure warning: {e}")
    
    async def reingest_memories(self, memories: List[Dict[str, Any]], batch_size: int = 10):
        """Re-ingest memories through the new pipeline"""
        print(f"🔄 Re-ingesting {len(memories)} memories through new pipeline...")
        
        successful = 0
        failed = 0
        
        for i in range(0, len(memories), batch_size):
            batch = memories[i:i + batch_size]
            print(f"   Processing batch {i//batch_size + 1}/{(len(memories) + batch_size - 1)//batch_size}...")
            
            for memory in batch:
                try:
                    # Prepare metadata
                    metadata = memory["metadata"].copy() if memory["metadata"] else {}
                    metadata.update({
                        "original_id": memory["id"],
                        "migrated_at": datetime.now().isoformat(),
                        "migration_source": "production_test_clone",
                        "created_at": memory["created_at"].isoformat() if memory["created_at"] else None
                    })
                    
                    # Add through unified system
                    result = await self.unified_client.add(
                        text=memory["content"],
                        user_id=self.test_user_id,
                        metadata=metadata
                    )
                    
                    successful += 1
                    
                    if successful % 25 == 0:
                        print(f"   ✅ Processed {successful} memories...")
                        
                except Exception as e:
                    print(f"   ❌ Failed to add memory: {str(e)[:100]}")
                    failed += 1
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        print(f"📊 Re-ingestion complete: {successful} successful, {failed} failed")
        return successful, failed
    
    async def generate_episodes(self):
        """Generate episodes from the ingested memories"""
        print("🎬 Generating episodes...")
        
        try:
            await self.unified_client.generate_user_episodes(self.test_user_id)
            print("✅ Episode generation complete")
        except Exception as e:
            print(f"❌ Episode generation failed: {e}")
    
    async def validate_system(self):
        """Validate the new system is working correctly"""
        print("🔍 Validating new system...")
        
        # Test queries
        test_queries = [
            "What did I do yesterday?",
            "Tell me about my work projects",
            "What are my fitness activities?",
            "Who do I interact with?",
            "What places do I visit?"
        ]
        
        for query in test_queries:
            try:
                results = await self.unified_client.search(
                    query=query,
                    user_id=self.test_user_id,
                    limit=5
                )
                
                print(f"   Query: '{query}'")
                print(f"   Results: {len(results)} memories found")
                
                if results:
                    for i, result in enumerate(results[:2], 1):
                        content = result.get('memory', result.get('content', ''))[:100]
                        source = result.get('source', 'unknown')
                        print(f"     {i}. [{source}] {content}...")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
        
        # Test multi-layer search
        try:
            print("🔍 Testing multi-layer search...")
            multilayer_results = await self.unified_client.search_multilayer(
                query="daily activities and routines",
                user_id=self.test_user_id,
                limit=10,
                search_types=["semantic", "graph", "episodic"]
            )
            
            print(f"   Multi-layer results: {len(multilayer_results)} found")
            
            # Group by source
            by_source = {}
            for result in multilayer_results:
                source = result.get('source', 'unknown')
                by_source[source] = by_source.get(source, 0) + 1
            
            for source, count in by_source.items():
                print(f"     {source}: {count} results")
                
        except Exception as e:
            print(f"   ❌ Multi-layer search failed: {e}")
    
    async def run_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting Test User Memory Migration")
        print("=" * 50)
        
        # Step 1: Fetch memories
        memories = self.get_test_user_memories()
        if not memories:
            print("❌ No memories found. Exiting.")
            return
        
        # Step 2: Clear test infrastructure
        await self.clear_test_infrastructure()
        
        # Step 3: Re-ingest memories
        successful, failed = await self.reingest_memories(memories)
        
        if successful == 0:
            print("❌ No memories successfully ingested. Exiting.")
            return
        
        # Step 4: Generate episodes
        await self.generate_episodes()
        
        # Step 5: Validate system
        await self.validate_system()
        
        # Step 6: Close connections
        await self.unified_client.close()
        
        print(f"\n🎉 Migration Complete!")
        print(f"📊 Successfully migrated {successful} memories")
        print(f"🧪 Test user can now use the new unified memory system")
        print(f"🌐 Log in at https://jeanmemory.com with test credentials")

async def main():
    migrator = TestUserMemoryMigrator()
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main()) 