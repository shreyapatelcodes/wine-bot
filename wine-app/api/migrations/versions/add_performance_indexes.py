"""Add performance indexes for lookup columns.

Revision ID: add_performance_indexes
Revises: f0e8cfe4df2c
Create Date: 2026-01-29
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = 'f0e8cfe4df2c'
branch_labels = None
depends_on = None


def upgrade():
    # Indexes for saved_bottles table
    op.create_index('idx_saved_bottles_user_id', 'saved_bottles', ['user_id'])
    op.create_index('idx_saved_bottles_wine_id', 'saved_bottles', ['wine_id'])

    # Indexes for cellar_bottles table
    op.create_index('idx_cellar_user_id', 'cellar_bottles', ['user_id'])
    op.create_index('idx_cellar_wine_id', 'cellar_bottles', ['wine_id'])

    # Indexes for wines table (for search and filtering)
    op.create_index('idx_wines_name', 'wines', ['name'])
    op.create_index('idx_wines_wine_type', 'wines', ['wine_type'])
    op.create_index('idx_wines_varietal', 'wines', ['varietal'])
    op.create_index('idx_wines_producer', 'wines', ['producer'])


def downgrade():
    # Remove indexes in reverse order
    op.drop_index('idx_wines_producer', 'wines')
    op.drop_index('idx_wines_varietal', 'wines')
    op.drop_index('idx_wines_wine_type', 'wines')
    op.drop_index('idx_wines_name', 'wines')
    op.drop_index('idx_cellar_wine_id', 'cellar_bottles')
    op.drop_index('idx_cellar_user_id', 'cellar_bottles')
    op.drop_index('idx_saved_bottles_wine_id', 'saved_bottles')
    op.drop_index('idx_saved_bottles_user_id', 'saved_bottles')
