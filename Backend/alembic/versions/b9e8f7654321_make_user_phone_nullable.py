"""Make users phone nullable and update length to 20

Revision ID: b9e8f7654321
Revises: a8f9e12345bc
Create Date: 2026-09-23 19:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b9e8f7654321'
down_revision: Union[str, Sequence[str], None] = 'a8f9e12345bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'phone',
            existing_type=sa.String(length=15),
            type_=sa.String(length=20),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column(
            'phone',
            existing_type=sa.String(length=20),
            type_=sa.String(length=15),
            nullable=False,
        )
