"""Add user taste profile table

Revision ID: a1b2c3d4e5f6
Revises: f0e8cfe4df2c
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f0e8cfe4df2c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_taste_profiles table
    op.create_table(
        'user_taste_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('preferred_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_regions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_countries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_varietals', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('price_range_min', sa.Float(), nullable=True),
        sa.Column('price_range_max', sa.Float(), nullable=True),
        sa.Column('flavor_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create index for faster lookups
    op.create_index('idx_taste_profile_user', 'user_taste_profiles', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_taste_profile_user', table_name='user_taste_profiles')
    op.drop_table('user_taste_profiles')
