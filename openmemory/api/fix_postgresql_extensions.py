#!/usr/bin/env python3
"""
Emergency fix for PostgreSQL full-text search extensions in production.
Run this once to enable the required PostgreSQL extensions.
"""

import logging
import os
import sys
from sqlalchemy import create_engine, text

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_postgresql_extensions():
    """Enable required PostgreSQL extensions for full-text search."""
    try:
        engine = create_engine(config.DATABASE_URL)
        
        with engine.connect() as conn:
            logger.info("Checking PostgreSQL extensions...")
            
            # Check if full-text search functions are available
            try:
                result = conn.execute(text("SELECT to_tsvector('english', 'test')"))
                result.fetchone()
                logger.info("✅ Full-text search functions are already available")
                return True
            except Exception as e:
                logger.warning(f"Full-text search functions not available: {e}")
            
            # Try to enable extensions that might help
            extensions_to_try = [
                "CREATE EXTENSION IF NOT EXISTS pg_trgm",  # Trigram extension for better text search
                "CREATE EXTENSION IF NOT EXISTS btree_gin",  # Better GIN index support
                "CREATE EXTENSION IF NOT EXISTS unaccent",  # Accent removal for text search
            ]
            
            for ext_sql in extensions_to_try:
                try:
                    conn.execute(text(ext_sql))
                    logger.info(f"✅ Executed: {ext_sql}")
                except Exception as e:
                    logger.warning(f"❌ Failed to execute {ext_sql}: {e}")
            
            # Test again
            try:
                result = conn.execute(text("SELECT to_tsvector('english', 'test')"))
                result.fetchone()
                logger.info("✅ Full-text search functions are now working!")
                return True
            except Exception as e:
                logger.error(f"❌ Full-text search still not working: {e}")
                logger.error("Your PostgreSQL instance may not support full-text search")
                logger.error("The app will fall back to ILIKE search (slower but functional)")
                return False
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔧 Attempting to fix PostgreSQL extensions...")
    success = fix_postgresql_extensions()
    
    if success:
        logger.info("✅ PostgreSQL extensions fixed successfully!")
    else:
        logger.warning("⚠️  PostgreSQL extensions could not be fully fixed")
        logger.warning("App will use ILIKE fallback (functional but slower)")
    
    sys.exit(0 if success else 1)