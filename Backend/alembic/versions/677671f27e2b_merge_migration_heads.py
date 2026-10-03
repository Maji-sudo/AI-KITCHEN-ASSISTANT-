"""Merge migration heads

Revision ID: 677671f27e2b
Revises: 20fc3eb6190a, c1d2e3f4a5b6
Create Date: 2026-10-02 21:32:24.682530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '677671f27e2b'
down_revision: Union[str, Sequence[str], None] = ('20fc3eb6190a', 'c1d2e3f4a5b6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
