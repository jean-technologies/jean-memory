#!/usr/bin/env python3
"""
Simple Memory Migration Script

This script re-ingests test user memories through the new unified memory system.
Focuses on core functionality without complex episode generation.
"""

import os
import sys
import asyncio
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv("openmemory/.env.local")

# Simple memory client that uses just mem0 with pgvector
from mem0 import Memory

class SimpleMemoryMigrator:
    def __init__(self):
        self.test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
        
        # Production database connection (to read memories)
        self.prod_db_url = "postgresql://postgres.masapxpxcwvsjpuymbmd:jeanmemorytypefasho@aws-0-us-east-1.pooler.supabase.com:5432/postgres?gssencmode=disable"
        
        # Initialize mem0 with test pgvector
        self.mem0_client = self._init_mem0_client()
        
        print(f"🧪 Simple Memory Migrator Initialized")
        print(f"   Test User ID: {self.test_user_id}")
        print(f"   Target: pgvector (localhost:5433)")
    
    def _init_mem0_client(self) -> Memory:
        """Initialize mem0 with test pgvector only"""
        config = {
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "user": "postgres",
                    "password": "secure_postgres_test_2024",
                    "host": "localhost",
                    "port": "5433",
                    "dbname": "mem0_unified",
                    "collection_name": "test_user_memories"
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
                    "model": "text-embedding-3-small",
                    "api_key": os.getenv("OPENAI_API_KEY")
                }
            },
            "version": "v1.1"
        }
        
        return Memory.from_config(config_dict=config)
    
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
    
    def clear_test_data(self):
        """Clear existing test data"""
        print("🧹 Clearing existing test data...")
        
        try:
            # Delete all memories for test user
            self.mem0_client.delete_all(user_id=self.test_user_id)
            print("   ✅ Cleared existing memories")
        except Exception as e:
            print(f"   ⚠️  Clear warning: {e}")
    
    def add_memories_batch(self, memories: List[Dict[str, Any]], batch_size: int = 5) -> tuple:
        """Add memories in batches to avoid overwhelming the system"""
        print(f"🔄 Adding {len(memories)} memories in batches of {batch_size}...")
        
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
                        "migration_source": "production_test_clone"
                    })
                    
                    # Add through mem0 - using messages format
                    result = self.mem0_client.add(
                        messages=[{"role": "user", "content": memory["content"]}],
                        user_id=self.test_user_id,
                        metadata=metadata
                    )
                    
                    successful += 1
                    
                    if successful % 10 == 0:
                        print(f"   ✅ Processed {successful} memories...")
                        
                except Exception as e:
                    print(f"   ❌ Failed to add memory: {str(e)[:100]}")
                    failed += 1
            
            # Small delay between batches
            import time
            time.sleep(1)
        
        print(f"📊 Migration complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def test_search(self):
        """Test search functionality"""
        print("🔍 Testing search functionality...")
        
        test_queries = [
            "What activities do I do?",
            "Tell me about travel",
            "What places have I been to?",
            "What do I like to do?",
            "Who do I spend time with?"
        ]
        
        for query in test_queries:
            try:
                results = self.mem0_client.search(
                    query=query,
                    user_id=self.test_user_id,
                    limit=3
                )
                
                print(f"   Query: '{query}'")
                print(f"   Results: {len(results)} memories found")
                
                for i, result in enumerate(results, 1):
                    memory_text = result.get('memory', result.get('text', ''))[:80]
                    score = result.get('score', 0)
                    print(f"     {i}. [{score:.3f}] {memory_text}...")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
    
    def run_migration(self):
        """Run the complete migration process"""
        print("🚀 Starting Simple Memory Migration")
        print("=" * 50)
        
        # Step 1: Fetch memories
        memories = self.get_test_user_memories()
        if not memories:
            print("❌ No memories found. Exiting.")
            return
        
        # Step 2: Clear existing test data
        self.clear_test_data()
        
        # Step 3: Add memories
        successful, failed = self.add_memories_batch(memories)
        
        if successful == 0:
            print("❌ No memories successfully added. Exiting.")
            return
        
        # Step 4: Test search
        self.test_search()
        
        print(f"\n🎉 Simple Migration Complete!")
        print(f"📊 Successfully migrated {successful} memories")
        print(f"🧪 Test user routing should now work")
        print(f"🌐 Try logging in at https://jeanmemory.com")

def main():
    migrator = SimpleMemoryMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main() 