"""Immutable published catalog revisions and a singleton active pointer."""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'


def upgrade():
    op.create_table('catalog_revisions', sa.Column('id', sa.String(64), primary_key=True),
                    sa.Column('payload', sa.JSON(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('catalog_state', sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('revision_id', sa.String(64), sa.ForeignKey('catalog_revisions.id'), nullable=False))


def downgrade():
    op.drop_table('catalog_state')
    op.drop_table('catalog_revisions')
