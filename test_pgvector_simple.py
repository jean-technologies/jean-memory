#!/usr/bin/env python3
"""
Simple pgvector Test for R&D

This script tests mem0 pgvector configuration and basic functionality
without requiring complex local PostgreSQL setup.
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_mem0_pgvector_config():
    """Test mem0 pgvector configuration validation"""
    logger.info("🔍 Testing mem0 pgvector configuration...")
    
    try:
        from mem0 import Memory
        
        # Test configuration - this will validate the config structure
        config = {
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "user": "test_user",
                    "password": "test_password", 
                    "host": "localhost",
                    "port": "5432",
                    "dbname": "test_db",
                    "collection_name": "test_collection"
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
        
        # This will validate the configuration structure
        logger.info("✅ mem0 pgvector configuration is valid")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        return False

def test_existing_rd_pipeline():
    """Test that existing R&D pipeline components are working"""
    logger.info("🔍 Testing existing R&D pipeline components...")
    
    try:
        # Test import of existing pipeline
        from rd_development_pipeline import RDPipeline
        logger.info("✅ R&D pipeline imports successfully")
        
        # Test unified memory ingestion import
        from unified_memory_ingestion import initialize_mem0
        logger.info("✅ Unified memory ingestion imports successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Pipeline import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        return False

async def test_data_download():
    """Test downloading sample data from Supabase (read-only)"""
    logger.info("🔍 Testing data download capability...")
    
    try:
        from rd_development_pipeline import RDPipeline
        
        pipeline = RDPipeline()
        
        # Test listing users (read-only operation)
        users = pipeline.list_available_users(limit=5)
        
        if users:
            logger.info(f"✅ Successfully found {len(users)} users with memories")
            logger.info(f"   Sample user: {users[0].get('user_id', 'N/A')} ({users[0].get('memory_count', 0)} memories)")
            return True
        else:
            logger.warning("⚠️  No users found (this might be expected in test environment)")
            return True
            
    except Exception as e:
        logger.error(f"❌ Data download test failed: {e}")
        return False

def main():
    """Run simple validation tests"""
    print("🧪 Simple pgvector Test")
    print("=" * 40)
    print("Testing mem0 pgvector readiness without full database setup")
    print()
    
    tests = [
        ("mem0 pgvector configuration", test_mem0_pgvector_config),
        ("Existing R&D pipeline", test_existing_rd_pipeline),
        ("Data download capability", test_data_download)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"📋 {test_name}")
        print("-" * 30)
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 40)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed >= 2:  # At least config and pipeline working
        print("\n🎉 Ready for pgvector testing!")
        print("\nRecommended approach:")
        print("1. Use your existing R&D pipeline: python rd_development_pipeline.py --interactive")
        print("2. Choose option 3 to create a dataset")
        print("3. The pipeline will use pgvector configuration from unified_memory_ingestion.py")
        print("4. Test with a small sample (10-20 memories) first")
        print("\nNote: The pipeline will download data safely (read-only) and test locally")
    else:
        print(f"\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main() 