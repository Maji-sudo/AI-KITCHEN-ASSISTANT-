"""Add priority and created_at to recommendations

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-10-09 17:47:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add priority (int, default 3) and created_at (timestamptz) columns."""
    # priority: 1=critical | 2=high | 3=medium | 4=low
    op.add_column(
        'recommendations',
        sa.Column('priority', sa.Integer(), nullable=False, server_default='3'),
    )
    # created_at — back-fill existing rows with the current timestamp
    op.add_column(
        'recommendations',
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW()'),
        ),
    )


def downgrade() -> None:
    """Remove priority and created_at columns."""
    op.drop_column('recommendations', 'created_at')
    op.drop_column('recommendations', 'priority')
