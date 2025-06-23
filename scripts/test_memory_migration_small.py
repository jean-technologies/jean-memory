#!/usr/bin/env python3
"""
Test Memory Migration Script - Small Batch

This script tests the migration with just a few memories to validate
the process before running the full migration.
"""

import os
import sys
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

class TestMemoryMigrator:
    def __init__(self, test_limit: int = 5):
        self.test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
        self.test_limit = test_limit
        
        # Production database connection (to read memories)
        self.prod_db_url = "postgresql://postgres.masapxpxcwvsjpuymbmd:jeanmemorytypefasho@aws-0-us-east-1.pooler.supabase.com:5432/postgres?gssencmode=disable"
        
        # Initialize mem0 with test pgvector
        self.mem0_client = self._init_mem0_client()
        
        print(f"🧪 Test Memory Migrator Initialized")
        print(f"   Test User ID: {self.test_user_id}")
        print(f"   Test Limit: {self.test_limit} memories")
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
    
    def get_test_memories(self) -> List[Dict[str, Any]]:
        """Fetch a small batch of test user memories"""
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
            
            # Fetch limited memories
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY created_at ASC
                LIMIT %s
            """, (internal_user_id, self.test_limit))
            
            memories = []
            for row in cursor.fetchall():
                memories.append({
                    "id": str(row[0]),
                    "content": row[1],
                    "metadata": row[2] or {},
                    "created_at": row[3],
                    "updated_at": row[4]
                })
            
            print(f"📊 Found {len(memories)} memories for testing")
            
            # Show sample memories
            print("\n📝 Sample memories to migrate:")
            for i, memory in enumerate(memories, 1):
                print(f"   {i}. {memory['content'][:60]}...")
            
            return memories
            
        except Exception as e:
            print(f"❌ Error fetching memories: {e}")
            return []
        finally:
            cursor.close()
            conn.close()
    
    def clear_test_data(self):
        """Clear existing test data"""
        print("\n🧹 Clearing existing test data...")
        
        try:
            # Delete all memories for test user
            self.mem0_client.delete_all(user_id=self.test_user_id)
            print("   ✅ Cleared existing memories")
        except Exception as e:
            print(f"   ⚠️  Clear warning: {e}")
    
    def add_memories_individually(self, memories: List[Dict[str, Any]]) -> tuple:
        """Add memories one by one with detailed logging"""
        print(f"\n🔄 Adding {len(memories)} memories individually...")
        
        successful = 0
        failed = 0
        
        for i, memory in enumerate(memories, 1):
            print(f"\n   Memory {i}/{len(memories)}:")
            print(f"   Content: {memory['content'][:80]}...")
            
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
                
                print(f"   ✅ Success! Result: {result}")
                successful += 1
                
            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")
                failed += 1
        
        print(f"\n📊 Test migration complete: {successful} successful, {failed} failed")
        return successful, failed
    
    def test_search(self):
        """Test search functionality with detailed results"""
        print("\n🔍 Testing search functionality...")
        
        test_queries = [
            "What activities do I do?",
            "Tell me about my recent activities",
            "What have I been up to?"
        ]
        
        for query in test_queries:
            try:
                print(f"\n   Query: '{query}'")
                results = self.mem0_client.search(
                    query=query,
                    user_id=self.test_user_id,
                    limit=3
                )
                
                print(f"   Results: {len(results)} memories found")
                
                for i, result in enumerate(results, 1):
                    # Handle different result formats
                    if isinstance(result, dict):
                        memory_text = result.get('memory', result.get('text', ''))[:80]
                        score = result.get('score', 0)
                    else:
                        memory_text = str(result)[:80]
                        score = 0
                    print(f"     {i}. [{score:.3f}] {memory_text}...")
                
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
    
    def verify_storage(self):
        """Verify memories are stored in pgvector"""
        print("\n🔍 Verifying pgvector storage...")
        
        try:
            # Get all memories for user
            all_memories = self.mem0_client.get_all(user_id=self.test_user_id, limit=100)
            print(f"   Total memories in pgvector: {len(all_memories)}")
            
            if all_memories:
                print("   Sample stored memories:")
                for i, memory in enumerate(list(all_memories)[:3], 1):
                    if isinstance(memory, dict):
                        memory_text = memory.get('memory', memory.get('text', ''))[:80]
                    else:
                        memory_text = str(memory)[:80]
                    print(f"     {i}. {memory_text}...")
            
        except Exception as e:
            print(f"   ❌ Verification failed: {e}")
    
    def run_test(self):
        """Run the test migration process"""
        print("🚀 Starting Test Memory Migration")
        print("=" * 50)
        
        # Step 1: Fetch test memories
        memories = self.get_test_memories()
        if not memories:
            print("❌ No memories found. Exiting.")
            return
        
        # Step 2: Clear existing test data
        self.clear_test_data()
        
        # Step 3: Add memories individually with logging
        successful, failed = self.add_memories_individually(memories)
        
        if successful == 0:
            print("❌ No memories successfully added. Exiting.")
            return
        
        # Step 4: Verify storage
        self.verify_storage()
        
        # Step 5: Test search
        self.test_search()
        
        print(f"\n🎉 Test Complete!")
        print(f"📊 Successfully migrated {successful}/{len(memories)} memories")
        
        if successful == len(memories):
            print(f"✅ All test memories migrated successfully!")
            print(f"🚀 Ready to run full migration of 260 memories")
        else:
            print(f"⚠️  Some memories failed. Review errors before full migration")

def main():
    # Test with just 5 memories first
    migrator = TestMemoryMigrator(test_limit=5)
    migrator.run_test()

if __name__ == "__main__":
    main() 