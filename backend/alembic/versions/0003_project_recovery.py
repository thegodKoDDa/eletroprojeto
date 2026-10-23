"""Reversible project deletion; payloads and calculation histories stay intact."""
from alembic import op
import sqlalchemy as sa
revision = '0003'
down_revision = '0002'


def upgrade():
    op.add_column('projects', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_projects_deleted_at', 'projects', ['deleted_at'])


def downgrade():
    op.drop_index('ix_projects_deleted_at', table_name='projects')
    op.drop_column('projects', 'deleted_at')
