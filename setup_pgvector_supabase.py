#!/usr/bin/env python3
"""
Setup pgvector in Supabase

This script helps set up pgvector extension and vector column in your Supabase database.
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

async def setup_pgvector():
    """Set up pgvector extension and vector column"""
    try:
        import asyncpg
        
        # Connect to Supabase
        conn = await asyncpg.connect(
            user=os.getenv('PG_USER'),
            password=os.getenv('PG_PASSWORD'),
            database=os.getenv('PG_DBNAME'),
            host=os.getenv('PG_HOST'),
            port=os.getenv('PG_PORT')
        )
        
        logger.info("✅ Connected to Supabase database")
        
        # 1. Enable pgvector extension
        logger.info("🔧 Enabling pgvector extension...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("✅ pgvector extension enabled")
        
        # 2. Check if memories table exists
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'memories'
            );
        """)
        
        if not table_exists:
            logger.error("❌ memories table not found. Please make sure your Supabase database has the memories table.")
            await conn.close()
            return False
        
        logger.info("✅ memories table found")
        
        # 3. Check if vector column exists
        vector_column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'memories'
                AND column_name = 'vector'
            );
        """)
        
        if vector_column_exists:
            logger.info("✅ vector column already exists")
        else:
            # Add vector column
            logger.info("🔧 Adding vector column to memories table...")
            await conn.execute("""
                ALTER TABLE memories 
                ADD COLUMN vector vector(1536);
            """)
            logger.info("✅ vector column added (1536 dimensions for OpenAI embeddings)")
        
        # 4. Create index for vector similarity search
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
            logger.warning(f"⚠️  Could not create vector index (this is optional): {e}")
        
        # 5. Show some statistics
        memory_count = await conn.fetchval("SELECT COUNT(*) FROM memories;")
        logger.info(f"📊 Total memories in database: {memory_count}")
        
        if memory_count > 0:
            vectors_count = await conn.fetchval("SELECT COUNT(*) FROM memories WHERE vector IS NOT NULL;")
            logger.info(f"📊 Memories with vectors: {vectors_count}")
            logger.info(f"📊 Memories without vectors: {memory_count - vectors_count}")
        
        await conn.close()
        logger.info("🎉 pgvector setup complete!")
        
        return True
        
    except ImportError:
        logger.error("❌ asyncpg not installed. Run: pip install asyncpg")
        return False
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

async def main():
    """Main setup function"""
    print("🚀 Supabase pgvector Setup")
    print("=" * 40)
    
    # Check environment variables first
    required_vars = ['PG_USER', 'PG_PASSWORD', 'PG_HOST', 'PG_PORT', 'PG_DBNAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error("❌ Missing environment variables:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        logger.info("Please edit your .env file with the correct Supabase credentials")
        return
    
    success = await setup_pgvector()
    
    if success:
        print("\n🎉 Setup complete! You can now run:")
        print("python validate_pgvector_setup.py")
    else:
        print("\n❌ Setup failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 