"""add fulltext search index to document chunks

Revision ID: a1b2c3d4e5f6
Revises: 6a4b2e8f5c91
Create Date: 2025-07-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6a4b2e8f5c91'
branch_labels = None
depends_on = None
disable_ddl_transaction = True


def upgrade() -> None:
    # Create GIN index for full-text search on document chunks
    # This significantly improves performance for text searches
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_chunks_content_fts 
        ON document_chunks 
        USING gin(to_tsvector('english', content))
    """)
    
    # Also add a regular B-tree index on content length for filtering
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_chunks_content_length
        ON document_chunks
        (length(content))
    """)
    
    # Add index on document_id + chunk_index for ordered retrieval
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_document_chunks_doc_chunk
        ON document_chunks
        (document_id, chunk_index)
    """)


def downgrade() -> None:
    # Remove the indexes
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_fts")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_content_length")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_doc_chunk")