"""merge conflicting migration heads

Revision ID: 49aad20c1d17
Revises: a1b2c3d4e5f6, dd63364e6ace
Create Date: 2025-07-18 22:44:03.819097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '49aad20c1d17'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', 'dd63364e6ace')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
