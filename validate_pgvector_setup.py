#!/usr/bin/env python3
"""
Validate pgvector Setup for R&D Testing

This script validates that your environment is ready to test the pgvector migration:
1. Checks environment variables
2. Tests PostgreSQL connection
3. Verifies pgvector extension
4. Tests mem0 pgvector configuration
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def check_environment_variables():
    """Check required environment variables"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = {
        'PG_USER': 'PostgreSQL username',
        'PG_PASSWORD': 'PostgreSQL password', 
        'PG_HOST': 'PostgreSQL host',
        'PG_PORT': 'PostgreSQL port',
        'PG_DBNAME': 'PostgreSQL database name',
        'OPENAI_API_KEY': 'OpenAI API key for embeddings',
        'NEO4J_URI': 'Neo4j URI for graph storage',
        'NEO4J_USER': 'Neo4j username',
        'NEO4J_PASSWORD': 'Neo4j password'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
            logger.error(f"❌ Missing: {var}")
        else:
            # Show partial value for security
            if 'PASSWORD' in var or 'KEY' in var:
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            logger.info(f"✅ {var}: {display_value}")
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        return False
    
    logger.info("✅ All environment variables present")
    return True

async def test_postgresql_connection():
    """Test PostgreSQL connection and pgvector extension"""
    logger.info("🔍 Testing PostgreSQL connection...")
    
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            database=os.getenv('PG_DBNAME'),
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        
        logger.info("✅ PostgreSQL connection successful")
        
        # Check if pgvector extension exists
        result = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        
        if result:
            logger.info("✅ pgvector extension is installed")
        else:
            logger.warning("⚠️  pgvector extension not found - you may need to run: CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Check if memories table exists and has vector column
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'memories'
            );
        """)
        
        if table_exists:
            logger.info("✅ memories table exists")
            
            # Check if vector column exists
            vector_column_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'memories'
                    AND column_name = 'vector'
                );
            """)
            
            if vector_column_exists:
                logger.info("✅ vector column exists in memories table")
            else:
                logger.warning("⚠️  vector column not found in memories table")
                logger.info("   You may need to add it: ALTER TABLE memories ADD COLUMN vector vector(1536);")
        else:
            logger.warning("⚠️  memories table not found")
        
        await conn.close()
        return True
        
    except ImportError:
        logger.error("❌ asyncpg not installed. Run: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False

async def test_mem0_pgvector_config():
    """Test mem0 with pgvector configuration"""
    logger.info("🔍 Testing mem0 pgvector configuration...")
    
    try:
        from mem0 import Memory
        
        config = {
            "vector_store": {
                "provider": "pgvector",
                "config": {
                    "user": os.getenv("PG_USER"),
                    "password": os.getenv("PG_PASSWORD"),
                    "host": os.getenv("PG_HOST"),
                    "port": os.getenv("PG_PORT"),
                    "dbname": os.getenv("PG_DBNAME"),
                    "collection_name": "test_pgvector_setup"
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
        
        # Initialize mem0 with pgvector
        memory = Memory.from_config(config_dict=config)
        logger.info("✅ mem0 initialized with pgvector configuration")
        
        # Test adding a simple memory
        test_user_id = "test-pgvector-setup"
        result = memory.add(
            "This is a test memory for pgvector setup validation",
            user_id=test_user_id,
            metadata={"test": True, "setup_validation": True}
        )
        
        if result:
            logger.info("✅ Test memory added successfully")
            
            # Test searching
            search_results = memory.search(
                "test memory pgvector",
                user_id=test_user_id
            )
            
            if search_results:
                logger.info(f"✅ Test search successful - found {len(search_results)} results")
                
                # Clean up test memory
                try:
                    memory.delete_all(user_id=test_user_id)
                    logger.info("✅ Test memory cleaned up")
                except:
                    logger.warning("⚠️  Could not clean up test memory (not critical)")
                
            else:
                logger.warning("⚠️  Test search returned no results")
        else:
            logger.error("❌ Failed to add test memory")
            return False
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("   Try: pip install mem0ai")
        return False
    except Exception as e:
        logger.error(f"❌ mem0 pgvector test failed: {e}")
        return False

async def test_neo4j_connection():
    """Test Neo4j connection for graph storage"""
    logger.info("🔍 Testing Neo4j connection...")
    
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
        )
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            
        driver.close()
        
        if test_value == 1:
            logger.info("✅ Neo4j connection successful")
            return True
        else:
            logger.error("❌ Neo4j connection test failed")
            return False
            
    except ImportError:
        logger.error("❌ neo4j driver not installed. Run: pip install neo4j")
        return False
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        return False

async def main():
    """Run all validation checks"""
    print("🧪 pgvector Setup Validation")
    print("=" * 50)
    
    checks = [
        ("Environment Variables", check_environment_variables()),
        ("PostgreSQL Connection", test_postgresql_connection()),
        ("Neo4j Connection", test_neo4j_connection()),
        ("mem0 pgvector Configuration", test_mem0_pgvector_config())
    ]
    
    results = []
    for check_name, check_coro in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        try:
            result = await check_coro
            results.append((check_name, result))
        except Exception as e:
            logger.error(f"❌ {check_name} failed with exception: {e}")
            results.append((check_name, False))
    
    # Summary
    print(f"\n📊 Validation Summary")
    print("=" * 50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("\n🎉 All checks passed! You're ready to test pgvector with the R&D pipeline.")
        print("\nNext steps:")
        print("1. Run: python rd_development_pipeline.py --interactive")
        print("2. Choose option 3 to create a new dataset with pgvector")
        print("3. Test ingestion and retrieval")
    else:
        print(f"\n⚠️  {len(results) - passed} checks failed. Please fix the issues above before proceeding.")

if __name__ == "__main__":
    asyncio.run(main()) 