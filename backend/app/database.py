import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, create_engine, event
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
    with_loader_criteria,
)


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    standards_version: Mapped[str] = mapped_column(
        String(100), default="registry-2026-10-21-pending"
    )
    __mapper_args__ = {"version_id_col": version}


class HistoryRow(Base):
    __tablename__ = "calculation_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    project_version: Mapped[int] = mapped_column(Integer)
    inputs: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def utcnow():
    return datetime.now(timezone.utc)


def make_engine(url: str):
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
        pool_pre_ping=True,
    )
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def sqlite_foreign_keys(connection, _):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


DEFAULT_DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parents[1] / 'eletroprojeto.db'}"
engine = make_engine(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_session(request: Request):
    with SessionLocal() as session:
        session.info["owner_id"] = getattr(request.state, "owner_id", None)
        session.info["scoped"] = True
        yield session


@event.listens_for(Session, "do_orm_execute")
def scope_projects(execute_state):
    if execute_state.is_select and execute_state.session.info.get("scoped"):
        owner = execute_state.session.info.get("owner_id")
        criterion = ProjectRow.owner_id.is_(None) if owner is None else ProjectRow.owner_id == owner
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(ProjectRow, criterion, include_aliases=True)
        )


@event.listens_for(Session, "before_flush")
def assign_owner(session, flush_context, instances):
    if session.info.get("scoped"):
        for row in session.new:
            if isinstance(row, ProjectRow):
                row.owner_id = session.info.get("owner_id")


class UserRow(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    active: Mapped[bool] = mapped_column(default=True)


class LoginSessionRow(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LoginAttemptRow(Base):
    __tablename__ = "login_attempts"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CatalogRevisionRow(Base):
    __tablename__ = "catalog_revisions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CatalogStateRow(Base):
    __tablename__ = "catalog_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revision_id: Mapped[str] = mapped_column(ForeignKey("catalog_revisions.id"))


class TechnicalRevisionRow(Base):
    __tablename__ = "technical_revisions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    review_status: Mapped[str] = mapped_column(String(50))


class KnowledgeDocumentRow(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(1000))
    kind: Mapped[str] = mapped_column(String(32), index=True)
    collection: Mapped[str] = mapped_column(String(40), index=True)
    review_state: Mapped[str] = mapped_column(String(40), index=True)
    media_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    text_pages: Mapped[int] = mapped_column(Integer)
    search_text: Mapped[str] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSON)


class KnowledgePageRow(Base):
    __tablename__ = "knowledge_pages"
    document_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"), primary_key=True
    )
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str] = mapped_column(Text)


class KnowledgeSourceRow(Base):
    __tablename__ = "knowledge_sources"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str | None] = mapped_column(
        ForeignKey("knowledge_documents.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(1000))
    url: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(80), index=True)
    provenance: Mapped[dict] = mapped_column(JSON)
