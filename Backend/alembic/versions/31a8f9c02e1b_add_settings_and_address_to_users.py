"""Add settings and address to users

Revision ID: 31a8f9c02e1b
Revises: 20fc3eb6190a
Create Date: 2026-10-22 22:30:00.000000

"""
from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31a8f9c02e1b'
down_revision: Union[str, Sequence[str], None] = '20fc3eb6190a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column('users', sa.Column('delivery_address', sa.JSON(), nullable=True))
        op.add_column('users', sa.Column('notification_preferences', sa.JSON(), nullable=True))
        op.add_column('users', sa.Column('safety_preferences', sa.JSON(), nullable=True))
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'delivery_address' not in columns:
        op.add_column('users', sa.Column('delivery_address', sa.JSON(), nullable=True))
    if 'notification_preferences' not in columns:
        op.add_column('users', sa.Column('notification_preferences', sa.JSON(), nullable=True))
    if 'safety_preferences' not in columns:
        op.add_column('users', sa.Column('safety_preferences', sa.JSON(), nullable=True))


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_column('users', 'safety_preferences')
        op.drop_column('users', 'notification_preferences')
        op.drop_column('users', 'delivery_address')
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'safety_preferences' in columns:
        op.drop_column('users', 'safety_preferences')
    if 'notification_preferences' in columns:
        op.drop_column('users', 'notification_preferences')
    if 'delivery_address' in columns:
        op.drop_column('users', 'delivery_address')
