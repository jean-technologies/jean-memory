-- Script to safely remove multi-agent coordination tables
-- Run this against your PostgreSQL database to clean up unused infrastructure

-- Drop tables in reverse dependency order to avoid foreign key issues
DROP TABLE IF EXISTS claude_code_tasks CASCADE;
DROP TABLE IF EXISTS claude_code_agents CASCADE;
DROP TABLE IF EXISTS claude_code_sessions CASCADE;

-- Verify removal
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'claude_code_sessions') AND
       NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'claude_code_agents') AND
       NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'claude_code_tasks') THEN
        RAISE NOTICE 'Multi-agent tables successfully removed';
    ELSE
        RAISE WARNING 'Some multi-agent tables still exist';
    END IF;
END $$;