"""Add slug field to modalities for robust onboarding lookup

Revision ID: a9f1e2b3c4d5
Revises: 3858fd8b02e2
Create Date: 2026-04-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9f1e2b3c4d5'
down_revision = '3858fd8b02e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('modalities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('slug', sa.String(length=50), nullable=True))
        batch_op.create_unique_constraint('uq_modality_slug', ['slug'])

    # Populate slug from existing names: lowercase, spaces → underscores
    op.execute("""
        UPDATE modalities
        SET slug = LOWER(REPLACE(REPLACE(REPLACE(name, ' ', '_'), '/', '_'), '-', '_'))
        WHERE slug IS NULL
    """)


def downgrade():
    with op.batch_alter_table('modalities', schema=None) as batch_op:
        batch_op.drop_constraint('uq_modality_slug', type_='unique')
        batch_op.drop_column('slug')
