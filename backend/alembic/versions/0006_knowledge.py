"""Searchable reference library, independent of validated calculation rules."""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"


def upgrade():
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("collection", sa.String(40), nullable=False),
        sa.Column("review_state", sa.String(40), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("text_pages", sa.Integer(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )
    for field in ("kind", "collection", "review_state"):
        op.create_index(f"ix_knowledge_documents_{field}", "knowledge_documents", [field])
    op.create_table(
        "knowledge_pages",
        sa.Column(
            "document_id",
            sa.String(64),
            sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("number", sa.Integer(), primary_key=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
    )
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("document_id", sa.String(64), sa.ForeignKey("knowledge_documents.id")),
        sa.Column("title", sa.String(1000), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("outcome", sa.String(80), nullable=False),
        sa.Column("provenance", sa.JSON(), nullable=False),
    )
    for field in ("document_id", "outcome"):
        op.create_index(f"ix_knowledge_sources_{field}", "knowledge_sources", [field])


def downgrade():
    op.drop_table("knowledge_sources")
    op.drop_table("knowledge_pages")
    op.drop_table("knowledge_documents")
