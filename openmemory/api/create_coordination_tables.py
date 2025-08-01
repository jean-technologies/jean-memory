#!/usr/bin/env python3
"""
Create coordination tables directly in SQLite database.
This is a simple approach that bypasses Alembic for now.
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_coordination_tables():
    """Create coordination tables in SQLite database."""
    try:
        # SQLite database path from alembic.ini
        db_path = "./openmemory.db"
        
        logger.info(f"Creating coordination tables in: {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create claude_code_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claude_code_sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                user_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create claude_code_agents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claude_code_agents (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                connection_url TEXT,
                status TEXT DEFAULT 'connected',
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES claude_code_sessions(id)
            )
        ''')
        
        # Create file_locks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_locks (
                id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                operation TEXT NOT NULL CHECK (operation IN ('read', 'write', 'delete')),
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES claude_code_sessions(id)
            )
        ''')
        
        # Create task_progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_progress (
                id TEXT PRIMARY KEY DEFAULT (hex(randomblob(16))),
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'blocked')),
                progress_percentage INTEGER CHECK (progress_percentage IS NULL OR (progress_percentage >= 0 AND progress_percentage <= 100)),
                message TEXT,
                affected_files TEXT, -- JSON as TEXT in SQLite
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES claude_code_sessions(id),
                UNIQUE(session_id, agent_id, task_id)
            )
        ''')
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_claude_sessions_user_id ON claude_code_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_claude_sessions_status ON claude_code_sessions(status)",
            "CREATE INDEX IF NOT EXISTS idx_claude_agents_session_id ON claude_code_agents(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_claude_agents_status ON claude_code_agents(status)",
            "CREATE INDEX IF NOT EXISTS idx_claude_agents_last_activity ON claude_code_agents(last_activity)",
            "CREATE INDEX IF NOT EXISTS idx_file_locks_session_id ON file_locks(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_file_locks_agent_id ON file_locks(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_file_locks_expires_at ON file_locks(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_file_locks_file_path ON file_locks(file_path)",
            "CREATE INDEX IF NOT EXISTS idx_task_progress_session_id ON task_progress(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_progress_agent_id ON task_progress(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_progress_status ON task_progress(status)",
            "CREATE INDEX IF NOT EXISTS idx_task_progress_updated_at ON task_progress(updated_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            logger.info(f"Created index: {index_sql.split(' ON ')[0].split(' ')[-1]}")
        
        # Commit all changes
        conn.commit()
        
        # Test the tables
        tables_to_check = ['claude_code_sessions', 'claude_code_agents', 'file_locks', 'task_progress']
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"📊 Table {table}: {count} records")
        
        conn.close()
        
        logger.info("✅ Coordination database tables created successfully!")
        logger.info("🎯 Multi-agent coordination system ready for Phase 2 testing")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create coordination tables: {e}")
        return False

if __name__ == "__main__":
    success = create_coordination_tables()
    if success:
        print("\n🚀 Coordination database ready!")
        print("📋 You can now test the multi-agent coordination tools:")
        print("   1. Use analyze_task_conflicts for planning")
        print("   2. Use create_task_distribution for setup")
        print("   3. Use claim_file_lock, sync_progress, check_agent_status for coordination")
    else:
        print("\n❌ Database initialization failed!")
        exit(1)