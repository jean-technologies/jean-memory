-- Multi-Agent Coordination Tables for Claude Code
-- These tables support cross-session coordination for 2-5 agent development

-- Sessions table (already exists from mcp.py but ensure it has correct schema)
CREATE TABLE IF NOT EXISTS claude_code_sessions (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    user_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agents table (already exists from mcp.py but ensure it has correct schema)  
CREATE TABLE IF NOT EXISTS claude_code_agents (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES claude_code_sessions(id),
    name VARCHAR NOT NULL,
    connection_url VARCHAR,
    status VARCHAR DEFAULT 'connected',
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- File locks table for preventing conflicts
CREATE TABLE IF NOT EXISTS file_locks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES claude_code_sessions(id),
    agent_id VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    operation VARCHAR NOT NULL CHECK (operation IN ('read', 'write', 'delete')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one agent can lock a file at a time per session
    UNIQUE(session_id, file_path, expires_at)
);

-- Task progress table for cross-session coordination
CREATE TABLE IF NOT EXISTS task_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES claude_code_sessions(id),
    agent_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'blocked')),
    progress_percentage INTEGER CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    message TEXT,
    affected_files JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one progress record per task per agent
    UNIQUE(session_id, agent_id, task_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_claude_sessions_user_id ON claude_code_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_claude_sessions_status ON claude_code_sessions(status);

CREATE INDEX IF NOT EXISTS idx_claude_agents_session_id ON claude_code_agents(session_id);
CREATE INDEX IF NOT EXISTS idx_claude_agents_status ON claude_code_agents(status);
CREATE INDEX IF NOT EXISTS idx_claude_agents_last_activity ON claude_code_agents(last_activity);

CREATE INDEX IF NOT EXISTS idx_file_locks_session_id ON file_locks(session_id);
CREATE INDEX IF NOT EXISTS idx_file_locks_agent_id ON file_locks(agent_id);
CREATE INDEX IF NOT EXISTS idx_file_locks_expires_at ON file_locks(expires_at);
CREATE INDEX IF NOT EXISTS idx_file_locks_file_path ON file_locks(file_path);

CREATE INDEX IF NOT EXISTS idx_task_progress_session_id ON task_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_task_progress_agent_id ON task_progress(agent_id);
CREATE INDEX IF NOT EXISTS idx_task_progress_status ON task_progress(status);
CREATE INDEX IF NOT EXISTS idx_task_progress_updated_at ON task_progress(updated_at);

-- Comments for documentation
COMMENT ON TABLE file_locks IS 'Cross-session file locking for multi-agent coordination';
COMMENT ON TABLE task_progress IS 'Task progress tracking across multiple agents';
COMMENT ON COLUMN file_locks.expires_at IS 'Lock expires automatically for safety';
COMMENT ON COLUMN task_progress.affected_files IS 'JSON array of files modified in this task update';