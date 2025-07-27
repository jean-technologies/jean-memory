"""Add entities column to memories table

Revision ID: 8bf2c14a5afa
Revises: 49aad20c1d17
Create Date: 2025-07-27 13:20:15.812207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8bf2c14a5afa'
down_revision: Union[str, None] = '49aad20c1d17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('memories', sa.Column('entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index('idx_memory_entities', 'memories', ['entities'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_memory_entities', table_name='memories', postgresql_using='gin')
    op.drop_column('memories', 'entities')
