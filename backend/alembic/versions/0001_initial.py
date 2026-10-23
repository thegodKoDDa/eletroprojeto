"""Initial project snapshots and calculation history."""
from alembic import op
import sqlalchemy as sa
revision = "0001"
down_revision = None


def upgrade():
    op.create_table("projects", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("payload", sa.JSON(), nullable=False), sa.Column("version", sa.Integer(), nullable=False),
                    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
                    sa.Column("standards_version", sa.String(100), nullable=False))
    op.create_table("calculation_history", sa.Column("id", sa.String(36), primary_key=True),
                    sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
                    sa.Column("project_version", sa.Integer(), nullable=False), sa.Column("inputs", sa.JSON(), nullable=False),
                    sa.Column("result", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_calculation_history_project_id", "calculation_history", ["project_id"])


def downgrade():
    op.drop_table("calculation_history")
    op.drop_table("projects")
