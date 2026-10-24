"""Trace page extraction separately from normative verification."""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"


def upgrade():
    op.add_column(
        "knowledge_pages",
        sa.Column("extraction_method", sa.String(32), nullable=False, server_default="native_text"),
    )
    op.add_column(
        "knowledge_pages",
        sa.Column("extraction_note", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column("knowledge_pages", sa.Column("ocr_confidence", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("knowledge_pages") as batch:
        batch.drop_column("ocr_confidence")
        batch.drop_column("extraction_note")
        batch.drop_column("extraction_method")
