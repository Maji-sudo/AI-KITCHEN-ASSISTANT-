"""Add session_token to cooking_history for idempotency

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-12 16:22:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add session_token column to cooking_history to support idempotent session deduction."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('cooking_history')]
    if 'session_token' not in columns:
        op.add_column(
            'cooking_history',
            sa.Column('session_token', sa.String(length=100), nullable=True),
        )
    indexes = [idx['name'] for idx in inspector.get_indexes('cooking_history')]
    if 'ix_cooking_history_session_token' not in indexes:
        op.create_index(
            op.f('ix_cooking_history_session_token'),
            'cooking_history',
            ['session_token'],
            unique=True,
        )


def downgrade() -> None:
    """Remove session_token column from cooking_history."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx['name'] for idx in inspector.get_indexes('cooking_history')]
    if 'ix_cooking_history_session_token' in indexes:
        op.drop_index(op.f('ix_cooking_history_session_token'), table_name='cooking_history')
    columns = [col['name'] for col in inspector.get_columns('cooking_history')]
    if 'session_token' in columns:
        op.drop_column('cooking_history', 'session_token')
