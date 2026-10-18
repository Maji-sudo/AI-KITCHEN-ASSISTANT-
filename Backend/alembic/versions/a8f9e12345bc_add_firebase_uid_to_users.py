"""Add firebase_uid to users table

Revision ID: a8f9e12345bc
Revises: 146e85c5ffa4
Create Date: 2026-09-22 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a8f9e12345bc'
down_revision: Union[str, Sequence[str], None] = '146e85c5ffa4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column('users', sa.Column('firebase_uid', sa.String(length=128), nullable=True))
        op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)
        return

    # Add firebase_uid to users table if it doesn't already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'firebase_uid' not in columns:
        op.add_column('users', sa.Column('firebase_uid', sa.String(length=128), nullable=True))
        op.create_index(op.f('ix_users_firebase_uid'), 'users', ['firebase_uid'], unique=True)


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
        op.drop_column('users', 'firebase_uid')
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'firebase_uid' in columns:
        op.drop_index(op.f('ix_users_firebase_uid'), table_name='users')
        op.drop_column('users', 'firebase_uid')
