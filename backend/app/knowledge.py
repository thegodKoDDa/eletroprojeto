"""Local reference reading; ingestion never enables a calculation rule."""

import os
import re
import unicodedata
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .database import KnowledgeDocumentRow, KnowledgePageRow, KnowledgeSourceRow, get_session

router = APIRouter(prefix="/api/v1/knowledge", tags=["Biblioteca técnica"])
NOTICE = "Acervo de consulta. Importação não valida vigência, aplicabilidade territorial ou regras de cálculo."


def normalize(value: str) -> str:
    return " ".join(
        "".join(
            c
            for c in unicodedata.normalize("NFKD", value.casefold())
            if not unicodedata.combining(c)
        ).split()
    )


def object_root() -> Path:
    return Path(
        os.getenv(
            "KNOWLEDGE_ROOT",
            str(Path(__file__).resolve().parents[2] / "references/library/objects"),
        )
    ).resolve()


class KnowledgeProvenance(BaseModel):
    origins: list[str]
    urls: list[str]
    groups: list[str]
    states_catalogued: list[str]
    editions_candidates: list[str]
    validation: str
    territory: str


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    kind: str
    collection: str
    review_state: str
    media_type: str
    byte_size: int
    page_count: int
    text_pages: int
    provenance: KnowledgeProvenance


class KnowledgePage(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    number: int
    body: str


class KnowledgeSearch(BaseModel):
    items: list[KnowledgeDocument]
    next_offset: int | None
    notice: str = NOTICE


class KnowledgeStats(BaseModel):
    documents: int
    pages: int
    text_pages: int
    sources: int
    kinds: dict[str, int]
    review_states: dict[str, int]
    notice: str = NOTICE


class KnowledgeSource(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    document_id: str | None
    title: str
    url: str
    outcome: str
    provenance: dict


SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/stats", response_model=KnowledgeStats)
def stats(session: SessionDep):
    return dict(
        documents=session.scalar(select(func.count()).select_from(KnowledgeDocumentRow)),
        pages=session.scalar(select(func.coalesce(func.sum(KnowledgeDocumentRow.page_count), 0))),
        text_pages=session.scalar(
            select(func.coalesce(func.sum(KnowledgeDocumentRow.text_pages), 0))
        ),
        sources=session.scalar(select(func.count()).select_from(KnowledgeSourceRow)),
        kinds=dict(
            session.execute(
                select(KnowledgeDocumentRow.kind, func.count()).group_by(KnowledgeDocumentRow.kind)
            ).all()
        ),
        review_states=dict(
            session.execute(
                select(KnowledgeDocumentRow.review_state, func.count()).group_by(
                    KnowledgeDocumentRow.review_state
                )
            ).all()
        ),
    )


@router.get("/documents", response_model=KnowledgeSearch)
def documents(
    session: SessionDep,
    q: str = Query("", max_length=160),
    kind: str = Query("", max_length=32),
    state: str = Query("", max_length=40),
    offset: int = Query(0, ge=0, le=100000),
    limit: int = Query(20, ge=1, le=50),
):
    statement = select(KnowledgeDocumentRow)
    if kind:
        statement = statement.where(KnowledgeDocumentRow.kind == kind)
    if state:
        statement = statement.where(KnowledgeDocumentRow.review_state == state)
    query = normalize(q)
    if query:
        # Literal matching, including % and _, works on SQLite and PostgreSQL.
        pages = select(KnowledgePageRow.document_id).where(
            KnowledgePageRow.search_text.contains(query, autoescape=True)
        )
        statement = statement.where(
            or_(
                KnowledgeDocumentRow.search_text.contains(query, autoescape=True),
                KnowledgeDocumentRow.id.in_(pages),
            )
        )
    rows = session.scalars(
        statement.order_by(
            KnowledgeDocumentRow.kind, KnowledgeDocumentRow.title, KnowledgeDocumentRow.id
        )
        .offset(offset)
        .limit(limit + 1)
    ).all()
    return dict(items=rows[:limit], next_offset=offset + limit if len(rows) > limit else None)


def find_document(session, document_id):
    if not re.fullmatch(r"[a-f0-9]{64}", document_id):
        raise HTTPException(404, "Documento não encontrado.")
    row = session.get(KnowledgeDocumentRow, document_id)
    if row is None:
        raise HTTPException(404, "Documento não encontrado.")
    return row


@router.get("/documents/{document_id}", response_model=KnowledgeDocument)
def document(document_id: str, session: SessionDep):
    return find_document(session, document_id)


@router.get("/documents/{document_id}/pages", response_model=list[KnowledgePage])
def pages(
    document_id: str,
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=20),
    q: str = Query("", max_length=160),
):
    find_document(session, document_id)
    statement = select(KnowledgePageRow).where(KnowledgePageRow.document_id == document_id)
    if normalize(q):
        statement = statement.where(
            KnowledgePageRow.search_text.contains(normalize(q), autoescape=True)
        )
    return session.scalars(
        statement.order_by(KnowledgePageRow.number).offset(offset).limit(limit)
    ).all()


@router.get("/documents/{document_id}/file")
def file(document_id: str, session: SessionDep):
    row = find_document(session, document_id)
    allowed = {"application/pdf": ".pdf", "text/markdown": ".md", "image/svg+xml": ".svg"}
    extension = allowed.get(row.media_type)
    if extension is None:
        raise HTTPException(415, "Formato disponível somente como texto de consulta.")
    path = object_root() / row.id
    if path.is_symlink() or not path.is_file() or path.resolve().parent != object_root():
        raise HTTPException(404, "Arquivo local indisponível; restaure os objetos da biblioteca.")
    return FileResponse(
        path,
        media_type=row.media_type,
        filename=f"referencia-{row.id[:12]}{extension}",
        content_disposition_type="inline" if extension in {".pdf", ".svg"} else "attachment",
        headers={
            "Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'",
        },
    )


@router.get("/sources", response_model=list[KnowledgeSource])
def sources(
    session: SessionDep,
    document_id: str = Query("", max_length=64),
    outcome: str = Query("", max_length=80),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
):
    statement = select(KnowledgeSourceRow)
    if document_id:
        statement = statement.where(KnowledgeSourceRow.document_id == document_id)
    if outcome:
        statement = statement.where(KnowledgeSourceRow.outcome == outcome)
    return session.scalars(
        statement.order_by(KnowledgeSourceRow.id).offset(offset).limit(limit)
    ).all()
