"""Add multi-agent coordination tables

Revision ID: multi_agent_coord_001
Revises: sms_conversation_manual
Create Date: 2025-07-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'multi_agent_coord_001'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'  # Use the latest migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create claude_code_sessions table
    op.create_table('claude_code_sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_claude_sessions_user_id', 'claude_code_sessions', ['user_id'])
    op.create_index('idx_claude_sessions_status', 'claude_code_sessions', ['status'])

    # Create claude_code_agents table
    op.create_table('claude_code_agents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('connection_url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True, default='connected'),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['claude_code_sessions.id'])
    )
    op.create_index('idx_claude_agents_session_id', 'claude_code_agents', ['session_id'])
    op.create_index('idx_claude_agents_status', 'claude_code_agents', ['status'])
    op.create_index('idx_claude_agents_last_activity', 'claude_code_agents', ['last_activity'])

    # Create file_locks table
    op.create_table('file_locks',
        sa.Column('id', sa.String(), nullable=False, default=sa.text('hex(randomblob(16))')),  # UUID alternative for SQLite
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False), 
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('operation', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['claude_code_sessions.id']),
        sa.CheckConstraint("operation IN ('read', 'write', 'delete')", name='check_file_lock_operation')
    )
    op.create_index('idx_file_locks_session_id', 'file_locks', ['session_id'])
    op.create_index('idx_file_locks_agent_id', 'file_locks', ['agent_id'])
    op.create_index('idx_file_locks_expires_at', 'file_locks', ['expires_at'])
    op.create_index('idx_file_locks_file_path', 'file_locks', ['file_path'])

    # Create task_progress table
    op.create_table('task_progress',
        sa.Column('id', sa.String(), nullable=False, default=sa.text('hex(randomblob(16))')),  # UUID alternative for SQLite
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('affected_files', sa.JSON(), nullable=True),  # SQLite supports JSON
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['claude_code_sessions.id']),
        sa.CheckConstraint("status IN ('started', 'in_progress', 'completed', 'failed', 'blocked')", name='check_task_status'),
        sa.CheckConstraint("progress_percentage IS NULL OR (progress_percentage >= 0 AND progress_percentage <= 100)", name='check_progress_percentage')
    )
    op.create_index('idx_task_progress_session_id', 'task_progress', ['session_id'])
    op.create_index('idx_task_progress_agent_id', 'task_progress', ['agent_id'])
    op.create_index('idx_task_progress_status', 'task_progress', ['status'])
    op.create_index('idx_task_progress_updated_at', 'task_progress', ['updated_at'])
    
    # Create unique constraint for one progress record per task per agent
    op.create_index('idx_unique_task_progress', 'task_progress', ['session_id', 'agent_id', 'task_id'], unique=True)


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('task_progress')
    op.drop_table('file_locks')
    op.drop_table('claude_code_agents')
    op.drop_table('claude_code_sessions')