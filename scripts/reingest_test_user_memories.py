#!/usr/bin/env python3
"""
Re-ingest test user memories through the new unified memory system.
This script takes existing memories and re-processes them through the new pipeline.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reingest_memories():
    """Re-ingest test user memories through the new system"""
    
    # Import after path setup
    from openmemory.api.app.utils.unified_memory import UnifiedMemoryClient, should_use_unified_memory
    from openmemory.api.app.database import get_db, SessionLocal
    from openmemory.api.app.models import User
    from sqlalchemy import text
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    # Test user configuration
    test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "your-test-user-id")
    
    print(f"🔄 Re-ingesting memories for test user: {test_user_id}")
    print("=" * 60)
    
    # Verify test user routing is enabled
    if not should_use_unified_memory(test_user_id):
        print("❌ Test user routing is not enabled!")
        print("Set these environment variables:")
        print("  ENABLE_UNIFIED_MEMORY_TEST_USER=true")
        print(f"  UNIFIED_MEMORY_TEST_USER_ID={test_user_id}")
        return
    
    print("✅ Test user routing is enabled")
    
    # Connect to production database to get memories
    prod_db_url = os.getenv("DATABASE_URL", "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres")
    
    try:
        # Get memories from production database
        print("\n📊 Fetching memories from production database...")
        conn = psycopg2.connect(prod_db_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all memories for test user
        cursor.execute("""
            SELECT id, user_id, content, metadata, created_at, updated_at
            FROM memories
            WHERE user_id = %s
            ORDER BY created_at ASC
        """, (test_user_id,))
        
        memories = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"✅ Found {len(memories)} memories to re-ingest")
        
        if not memories:
            print("No memories found for test user")
            return
        
        # Initialize unified memory client
        print("\n🚀 Initializing unified memory system...")
        unified_client = UnifiedMemoryClient(use_new_system=True, user_id=test_user_id)
        
        # Re-ingest memories
        print(f"\n📝 Re-ingesting {len(memories)} memories...")
        success_count = 0
        error_count = 0
        
        for i, memory in enumerate(memories, 1):
            try:
                # Extract metadata
                metadata = memory.get('metadata') or {}
                
                # Add memory through new system
                result = await unified_client.add(
                    text=memory['content'],
                    user_id=test_user_id,
                    metadata={
                        **metadata,
                        'original_id': str(memory['id']),
                        'migrated': True,
                        'migration_date': datetime.now().isoformat(),
                        'created_at': memory['created_at'].isoformat() if memory['created_at'] else None
                    }
                )
                
                success_count += 1
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(memories)} memories processed")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error re-ingesting memory {memory['id']}: {e}")
                
                if error_count > 10:
                    print(f"\n❌ Too many errors ({error_count}), stopping")
                    break
        
        print(f"\n✅ Re-ingestion complete!")
        print(f"  Successfully processed: {success_count}")
        print(f"  Errors: {error_count}")
        
        # Test search functionality
        print("\n🔍 Testing search functionality...")
        test_queries = [
            "recent memories",
            "important",
            "work",
            "personal"
        ]
        
        for query in test_queries:
            try:
                results = await unified_client.search(
                    query=query,
                    user_id=test_user_id,
                    limit=3
                )
                print(f"  Query '{query}': {len(results)} results")
            except Exception as e:
                print(f"  Query '{query}': Error - {e}")
        
        print("\n✅ Re-ingestion and testing complete!")
        
    except Exception as e:
        logger.error(f"Fatal error during re-ingestion: {e}")
        raise


if __name__ == "__main__":
    # Set environment variables for test
    os.environ["ENABLE_UNIFIED_MEMORY_TEST_USER"] = "true"
    os.environ["UNIFIED_MEMORY_TEST_USER_ID"] = "your-test-user-id"
    
    # Run the async function
    asyncio.run(reingest_memories()) 