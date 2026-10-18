"""Create initial base tables

Revision ID: 0001_initial_base_tables
Revises: 
Create Date: 2026-08-01 00:00:00.000000

Creates the foundational application tables (users, devices, cylinders, dish_library,
notifications, gas_readings, cooking_history, leak_events, efficiency_scores, bookings)
required by subsequent migrations and foreign keys. Supports both fresh empty databases
and existing pre-initialized setups idempotently.
"""
from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_base_tables'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = []
    if not context.is_offline_mode():
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = inspector.get_table_names()

    # 1. users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('phone', sa.String(length=15), nullable=False),
            sa.Column('language_pref', sa.String(length=10), server_default='en', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
        op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)

    # 2. devices
    if 'devices' not in existing_tables:
        op.create_table(
            'devices',
            sa.Column('id', sa.String(length=100), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('firmware_version', sa.String(length=50), nullable=True),
            sa.Column('status', sa.String(length=50), server_default='inactive', nullable=False),
            sa.Column('paired_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )

    # 3. dish_library
    if 'dish_library' not in existing_tables:
        op.create_table(
            'dish_library',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('dish_name', sa.String(length=255), nullable=False),
            sa.Column('cuisine_tag', sa.String(length=100), nullable=False),
            sa.Column('base_gas_g', sa.Float(), nullable=False),
            sa.Column('base_duration_min', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_dish_library_dish_name'), 'dish_library', ['dish_name'], unique=True)

    # 4. cylinders
    if 'cylinders' not in existing_tables:
        op.create_table(
            'cylinders',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('device_id', sa.String(length=100), nullable=False),
            sa.Column('tare_weight_g', sa.Float(), nullable=False),
            sa.Column('full_weight_g', sa.Float(), nullable=False),
            sa.Column('install_date', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('cylinder_type', sa.String(length=50), server_default='14.2kg', nullable=False),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    # 5. notifications
    if 'notifications' not in existing_tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('payload', sa.JSON(), nullable=True),
            sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('delivery_status', sa.String(length=50), server_default='pending', nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    # 6. gas_readings
    if 'gas_readings' not in existing_tables:
        op.create_table(
            'gas_readings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('device_id', sa.String(length=100), nullable=False),
            sa.Column('ppm_value', sa.Float(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.Column('source', sa.String(length=20), server_default='IOT', nullable=True),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_gas_readings_timestamp'), 'gas_readings', ['timestamp'], unique=False)

    # 7. cooking_history
    if 'cooking_history' not in existing_tables:
        op.create_table(
            'cooking_history',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_id', sa.String(length=100), nullable=False),
            sa.Column('dish_id', sa.Integer(), nullable=True),
            sa.Column('logged_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('actual_gas_g', sa.Float(), nullable=True),
            sa.Column('actual_duration_min', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['dish_id'], ['dish_library.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_cooking_history_device_id'), 'cooking_history', ['device_id'], unique=False)
        op.create_index(op.f('ix_cooking_history_user_id'), 'cooking_history', ['user_id'], unique=False)

    # 8. leak_events
    if 'leak_events' not in existing_tables:
        op.create_table(
            'leak_events',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('device_id', sa.String(length=100), nullable=False),
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
            sa.Column('peak_ppm', sa.Float(), nullable=False),
            sa.Column('auto_shutoff_triggered', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('false_alarm', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_leak_events_device_id'), 'leak_events', ['device_id'], unique=False)

    # 9. efficiency_scores
    if 'efficiency_scores' not in existing_tables:
        op.create_table(
            'efficiency_scores',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('device_id', sa.String(length=100), nullable=False),
            sa.Column('period_type', sa.String(length=20), nullable=False),
            sa.Column('overall_score', sa.Float(), nullable=False),
            sa.Column('component_scores_json', sa.JSON(), nullable=True),
            sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_efficiency_scores_device_id'), 'efficiency_scores', ['device_id'], unique=False)

    # 10. bookings
    if 'bookings' not in existing_tables:
        op.create_table(
            'bookings',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_id', sa.String(length=100), nullable=False),
            sa.Column('booking_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('distributor', sa.String(length=255), nullable=False),
            sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
            sa.Column('source', sa.String(length=50), server_default='app', nullable=False),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_bookings_device_id'), 'bookings', ['device_id'], unique=False)
        op.create_index(op.f('ix_bookings_user_id'), 'bookings', ['user_id'], unique=False)


def downgrade() -> None:
    existing_tables = []
    if not context.is_offline_mode():
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        existing_tables = inspector.get_table_names()

    tables_to_drop = [
        'bookings',
        'efficiency_scores',
        'leak_events',
        'cooking_history',
        'gas_readings',
        'notifications',
        'cylinders',
        'dish_library',
        'devices',
        'users',
    ]

    for table in tables_to_drop:
        if context.is_offline_mode() or table in existing_tables:
            op.drop_table(table)
