"""Immutable snapshots of the technical registry; existing projects untouched."""
from alembic import op
import sqlalchemy as sa
revision = '0002'
down_revision = '0001'


def upgrade():
    op.create_table('technical_revisions',
                    sa.Column('id', sa.String(64), primary_key=True),
                    sa.Column('payload', sa.JSON(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('review_status', sa.String(50), nullable=False))


def downgrade():
    op.drop_table('technical_revisions')
