#!/usr/bin/env python3
"""
Setup Local PostgreSQL with pgvector for R&D Testing

This script sets up a local PostgreSQL database for testing pgvector ingestion.
This does NOT modify production data - it creates a local test environment.
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

async def setup_local_pgvector():
    """Set up local PostgreSQL database with pgvector for testing"""
    try:
        import asyncpg
        
        # First, connect to default postgres database to create test database
        logger.info("🔧 Connecting to local PostgreSQL...")
        conn = await asyncpg.connect(
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            database='postgres',  # Connect to default database first
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        
        logger.info("✅ Connected to local PostgreSQL")
        
        # Create test database
        test_db_name = os.getenv('PG_DBNAME', 'mem0_rd_test')
        logger.info(f"🔧 Creating test database: {test_db_name}")
        
        try:
            await conn.execute(f'CREATE DATABASE "{test_db_name}";')
            logger.info(f"✅ Created database: {test_db_name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"✅ Database {test_db_name} already exists")
            else:
                raise e
        
        await conn.close()
        
        # Now connect to the test database
        conn = await asyncpg.connect(
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            database=test_db_name,
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        
        # Enable pgvector extension
        logger.info("🔧 Enabling pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✅ pgvector extension enabled")
        
        # Create test memories table (simplified version for testing)
        logger.info("🔧 Creating test memories table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                content TEXT NOT NULL,
                vector vector(1536),
                mem0_id TEXT,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        logger.info("✅ Test memories table created")
        
        # Create index for vector similarity search
        logger.info("🔧 Creating vector similarity index...")
        try:
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS memories_vector_idx 
                ON memories 
                USING ivfflat (vector vector_cosine_ops)
                WITH (lists = 100);
            """)
            logger.info("✅ Vector similarity index created")
        except Exception as e:
            logger.warning(f"⚠️  Could not create vector index: {e}")
        
        # Create user_id index for filtering
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS memories_user_id_idx 
            ON memories (user_id);
        """)
        logger.info("✅ User ID index created")
        
        await conn.close()
        logger.info("🎉 Local pgvector setup complete!")
        
        return True
        
    except ImportError:
        logger.error("❌ asyncpg not installed. Run: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        logger.info("💡 Make sure you have PostgreSQL running locally")
        logger.info("   macOS: brew install postgresql && brew services start postgresql")
        logger.info("   Ubuntu: sudo apt install postgresql postgresql-contrib")
        return False

async def main():
    """Main setup function"""
    print("🚀 Local PostgreSQL + pgvector Setup")
    print("=" * 50)
    print("This creates a LOCAL test database - does NOT modify production!")
    print()
    
    # Check environment variables
    required_vars = ['PG_USER', 'PG_PASSWORD', 'PG_HOST', 'PG_PORT', 'PG_DBNAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("❌ Missing environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        logger.info("Please make sure your .env file is configured correctly")
        return
    
    success = await setup_local_pgvector()
    
    if success:
        print("\n🎉 Setup complete! Your local pgvector database is ready.")
        print("\nNext steps:")
        print("1. python validate_pgvector_setup.py")
        print("2. python rd_development_pipeline.py --interactive")
        print("\nThe pipeline will:")
        print("- Download memories from Supabase (read-only)")
        print("- Test ingestion into local pgvector database")
        print("- Test retrieval from local database")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 