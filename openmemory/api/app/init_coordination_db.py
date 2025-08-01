#!/usr/bin/env python3
"""
Initialize coordination database tables for Claude Code multi-agent system.
Run this script to create the necessary tables for cross-session coordination.
"""

import os
import logging
from sqlalchemy import create_engine, text
from app.settings import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_coordination_tables():
    """Initialize coordination tables in the database."""
    try:
        # Get database URL from config
        database_url = config.DATABASE_URL
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set in environment")
        
        logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
        
        # Create engine
        engine = create_engine(database_url)
        
        # Read the schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'coordination_schema.sql')
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema
        with engine.connect() as conn:
            # Split by statements and execute each one
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    try:
                        conn.execute(text(statement))
                        logger.info(f"Executed: {statement[:50]}...")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            logger.info(f"Table already exists, skipping: {statement[:50]}...")
                        else:
                            logger.error(f"Error executing statement: {e}")
                            raise
            
            conn.commit()
        
        logger.info("✅ Coordination database tables initialized successfully!")
        logger.info("🎯 Multi-agent coordination system ready for Phase 2 testing")
        
        # Test the tables
        with engine.connect() as conn:
            # Check if tables exist
            tables_to_check = ['claude_code_sessions', 'claude_code_agents', 'file_locks', 'task_progress']
            for table in tables_to_check:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"📊 Table {table}: {count} records")
                except Exception as e:
                    logger.error(f"❌ Table {table} check failed: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize coordination tables: {e}")
        return False

if __name__ == "__main__":
    success = init_coordination_tables()
    if success:
        print("\n🚀 Coordination database ready!")
        print("📋 You can now test the multi-agent coordination tools:")
        print("   1. Use analyze_task_conflicts for planning")
        print("   2. Use create_task_distribution for setup")
        print("   3. Use claim_file_lock, sync_progress, check_agent_status for coordination")
    else:
        print("\n❌ Database initialization failed!")
        exit(1)