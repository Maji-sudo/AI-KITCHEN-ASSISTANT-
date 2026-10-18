"""Replace firebase_uid with password_hash; enforce email NOT NULL

Revision ID: c1d2e3f4a5b6
Revises: b9e8f7654321
Create Date: 2026-09-23 20:48:00.000000

Changes:
- Drop ix_users_firebase_uid index (if exists)
- Drop firebase_uid column (if exists)
- Add password_hash column (VARCHAR 255, nullable initially)
- Make email NOT NULL with unique index (already unique; enforce not-null)
- Note: NULL-email dev users were manually deleted before this migration runs
"""
from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b9e8f7654321'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if context.is_offline_mode():
        op.drop_index('ix_users_firebase_uid', table_name='users')
        op.drop_column('users', 'firebase_uid')
        op.add_column(
            'users',
            sa.Column('password_hash', sa.String(length=255), nullable=True)
        )
        op.alter_column(
            'users',
            'email',
            existing_type=sa.String(length=255),
            nullable=False,
        )
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    indexes = [idx['name'] for idx in inspector.get_indexes('users')]

    # 1. Drop firebase_uid index if it exists
    if 'ix_users_firebase_uid' in indexes:
        op.drop_index('ix_users_firebase_uid', table_name='users')

    # 2. Drop firebase_uid column if it exists
    if 'firebase_uid' in columns:
        op.drop_column('users', 'firebase_uid')

    # 3. Add password_hash column if it does not exist yet
    if 'password_hash' not in columns:
        op.add_column(
            'users',
            sa.Column('password_hash', sa.String(length=255), nullable=True)
        )

    # 4. Enforce email NOT NULL
    #    (All NULL-email rows were manually removed before this migration)
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'email',
            existing_type=sa.String(length=255),
            nullable=False,
        )

    # 5. Ensure email unique index exists (may already exist from initial migration)
    if 'ix_users_email' not in indexes:
        op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade() -> None:
    if context.is_offline_mode():
        with op.batch_alter_table('users') as batch_op:
            batch_op.alter_column(
                'email',
                existing_type=sa.String(length=255),
                nullable=True,
            )
        op.drop_column('users', 'password_hash')
        op.add_column(
            'users',
            sa.Column('firebase_uid', sa.String(length=128), nullable=True)
        )
        op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'], unique=True)
        return

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    indexes = [idx['name'] for idx in inspector.get_indexes('users')]

    # Reverse email NOT NULL
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'email',
            existing_type=sa.String(length=255),
            nullable=True,
        )

    # Drop password_hash
    if 'password_hash' in columns:
        op.drop_column('users', 'password_hash')

    # Restore firebase_uid
    if 'firebase_uid' not in columns:
        op.add_column(
            'users',
            sa.Column('firebase_uid', sa.String(length=128), nullable=True)
        )
        op.create_index('ix_users_firebase_uid', 'users', ['firebase_uid'], unique=True)
