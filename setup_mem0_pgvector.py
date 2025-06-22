#!/usr/bin/env python3
"""
Setup PostgreSQL for mem0 pgvector

This script sets up PostgreSQL specifically for mem0's pgvector usage.
mem0 handles its own table creation and management.
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

async def setup_mem0_pgvector():
    """Set up PostgreSQL for mem0 pgvector usage"""
    try:
        import asyncpg
        
        # Connect to default postgres database
        logger.info("🔧 Connecting to PostgreSQL...")
        conn = await asyncpg.connect(
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD', ''),  # Empty password for local
            database='postgres',
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        
        logger.info("✅ Connected to PostgreSQL")
        
        # Create mem0 database
        test_db_name = os.getenv('PG_DBNAME', 'mem0_test')
        logger.info(f"🔧 Creating mem0 database: {test_db_name}")
        
        try:
            await conn.execute(f'CREATE DATABASE "{test_db_name}";')
            logger.info(f"✅ Created database: {test_db_name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"✅ Database {test_db_name} already exists")
            else:
                raise e
        
        await conn.close()
        
        # Connect to the mem0 database
        conn = await asyncpg.connect(
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD', ''),
            database=test_db_name,
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        
        # Enable pgvector extension
        logger.info("🔧 Enabling pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✅ pgvector extension enabled")
        
        # Test vector functionality
        logger.info("🔧 Testing vector functionality...")
        await conn.execute("SELECT vector_dims(ARRAY[1,2,3]::vector);")
        logger.info("✅ Vector functionality working")
        
        await conn.close()
        logger.info("🎉 mem0 pgvector setup complete!")
        
        return True
        
    except ImportError:
        logger.error("❌ asyncpg not installed. Run: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

async def test_mem0_pgvector():
    """Test mem0 with pgvector configuration"""
    logger.info("🔍 Testing mem0 with pgvector...")
    
    try:
        from mem0 import Memory
        
        config = {
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "user": os.getenv("PG_USER"),
                    "password": os.getenv("PG_PASSWORD", ""),
                    "host": os.getenv("PG_HOST"),
                    "port": os.getenv("PG_PORT"),
                    "dbname": os.getenv("PG_DBNAME", "mem0_test"),
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
            "history_db_path": "mem0_pgvector_test.db",
            "version": "v1.1"
        }
        
        # Initialize mem0 - this will create tables automatically
        logger.info("🔧 Initializing mem0 with pgvector...")
        memory = Memory.from_config(config_dict=config)
        logger.info("✅ mem0 initialized successfully")
        
        # Test adding a memory
        test_user_id = "test-pgvector-user"
        logger.info("🔧 Testing memory addition...")
        result = memory.add(
            "This is a test memory for pgvector validation",
            user_id=test_user_id,
            metadata={"test": True}
        )
        
        if result:
            logger.info("✅ Memory added successfully")
            
            # Test searching
            logger.info("🔧 Testing memory search...")
            search_results = memory.search(
                "test memory pgvector",
                user_id=test_user_id
            )
            
            if search_results:
                logger.info(f"✅ Search successful - found {len(search_results)} results")
                
                # Clean up
                memory.delete_all(user_id=test_user_id)
                logger.info("✅ Test cleanup completed")
                
                return True
            else:
                logger.warning("⚠️  Search returned no results")
                return False
        else:
            logger.error("❌ Failed to add memory")
            return False
        
    except Exception as e:
        logger.error(f"❌ mem0 test failed: {e}")
        return False

async def main():
    """Main setup and test function"""
    print("🚀 mem0 pgvector Setup & Test")
    print("=" * 50)
    print("Setting up PostgreSQL specifically for mem0 pgvector usage")
    print()
    
    # Check environment variables
    required_vars = ['PG_USER', 'PG_HOST', 'PG_PORT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("❌ Missing environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        return
    
    # Setup database
    setup_success = await setup_mem0_pgvector()
    if not setup_success:
        print("\n❌ Database setup failed")
        return
    
    # Test mem0
    test_success = await test_mem0_pgvector()
    
    if test_success:
        print("\n🎉 Success! mem0 pgvector is working correctly.")
        print("\nYour configuration:")
        print(f"  Database: {os.getenv('PG_DBNAME', 'mem0_test')}")
        print(f"  Host: {os.getenv('PG_HOST')}")
        print(f"  Port: {os.getenv('PG_PORT')}")
        print(f"  User: {os.getenv('PG_USER')}")
        print("\nNext step: Update unified_memory_ingestion.py to use pgvector")
    else:
        print("\n❌ mem0 test failed")

if __name__ == "__main__":
    asyncio.run(main()) 