"""Add FES-related fields (is_featured to modalities, badge to packages)

Revision ID: f5a9c7b8d123
Revises: 4afe69b3d779
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5a9c7b8d123'
down_revision = '4afe69b3d779'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_featured to modalities table
    with op.batch_alter_table('modalities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_featured', sa.Boolean(), nullable=True, default=False))

    # Add badge to packages table
    with op.batch_alter_table('packages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('badge', sa.String(length=50), nullable=True))

    # Set default value for existing rows
    op.execute("UPDATE modalities SET is_featured = 0 WHERE is_featured IS NULL")


def downgrade():
    with op.batch_alter_table('packages', schema=None) as batch_op:
        batch_op.drop_column('badge')

    with op.batch_alter_table('modalities', schema=None) as batch_op:
        batch_op.drop_column('is_featured')
