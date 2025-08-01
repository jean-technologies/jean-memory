-- Multi-Agent Coordination Tables for Claude Code
-- Run this in Supabase SQL Editor to create the required tables

-- 1. Sessions table for multi-terminal projects
CREATE TABLE IF NOT EXISTS claude_code_sessions (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    user_id VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Agents table for tracking connected terminals
CREATE TABLE IF NOT EXISTS claude_code_agents (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES claude_code_sessions(id) ON DELETE CASCADE,
    name VARCHAR NOT NULL,
    connection_url VARCHAR,
    status VARCHAR DEFAULT 'connected',
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. File locks table for preventing conflicts
CREATE TABLE IF NOT EXISTS file_locks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES claude_code_sessions(id) ON DELETE CASCADE,
    agent_id VARCHAR NOT NULL,
    file_path VARCHAR NOT NULL,
    operation VARCHAR NOT NULL CHECK (operation IN ('read', 'write', 'delete')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Ensure one agent can lock a file at a time per session
    UNIQUE(session_id, file_path)
);

-- 4. Task progress table for cross-session coordination
CREATE TABLE IF NOT EXISTS task_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES claude_code_sessions(id) ON DELETE CASCADE,
    agent_id VARCHAR NOT NULL,
    task_id VARCHAR NOT NULL,
    status VARCHAR NOT NULL CHECK (status IN ('started', 'in_progress', 'completed', 'failed', 'blocked')),
    progress_percentage INTEGER CHECK (progress_percentage IS NULL OR (progress_percentage >= 0 AND progress_percentage <= 100)),
    message TEXT,
    affected_files JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Ensure one progress record per task per agent
    UNIQUE(session_id, agent_id, task_id)
);

-- Create indexes for performance
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

-- Enable Row Level Security (RLS) for security
ALTER TABLE claude_code_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE claude_code_agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_locks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_progress ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access (your API uses service role)
-- Sessions: Service role has full access
CREATE POLICY "Service role has full access to sessions" ON claude_code_sessions
    FOR ALL USING (true);

-- Agents: Service role has full access
CREATE POLICY "Service role has full access to agents" ON claude_code_agents
    FOR ALL USING (true);

-- File locks: Service role has full access
CREATE POLICY "Service role has full access to file locks" ON file_locks
    FOR ALL USING (true);

-- Task progress: Service role has full access
CREATE POLICY "Service role has full access to task progress" ON task_progress
    FOR ALL USING (true);

-- Add helpful comments
COMMENT ON TABLE claude_code_sessions IS 'Multi-agent development sessions for Claude Code';
COMMENT ON TABLE claude_code_agents IS 'Individual agent connections within a session';
COMMENT ON TABLE file_locks IS 'Cross-session file locking for conflict prevention';
COMMENT ON TABLE task_progress IS 'Task progress tracking across multiple agents';

COMMENT ON COLUMN file_locks.expires_at IS 'Lock expires automatically for safety';
COMMENT ON COLUMN task_progress.affected_files IS 'JSON array of files modified in this task update';

-- Success message
DO $$ 
BEGIN 
    RAISE NOTICE '✅ Multi-agent coordination tables created successfully!';
    RAISE NOTICE '🎯 Ready for Claude Code multi-terminal testing';
END $$;