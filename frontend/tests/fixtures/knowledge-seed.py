"""Fictitious library for isolated browser QA, never application data."""

import hashlib
import os
from pathlib import Path

from app.database import KnowledgeDocumentRow, KnowledgePageRow, KnowledgeSourceRow, SessionLocal
from app.knowledge import normalize

folder = Path(os.environ["KNOWLEDGE_ROOT"])
folder.mkdir(parents=True, exist_ok=True)
with SessionLocal() as session:
    for kind, name, body, media in [
        (
            "guide",
            "Guia QA de chuveiro",
            "# Guia fictício\nPotência **não dimensiona sozinha** cabos ou proteções.",
            "text/markdown",
        ),
        (
            "diagram",
            "Diagrama QA conceitual",
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><rect width="400" height="200" fill="white"/><text x="20" y="100">Diagrama ficticio</text></svg>',
            "image/svg+xml",
        ),
    ]:
        key = hashlib.sha256(body.encode()).hexdigest()
        (folder / key).write_text(body)
        session.add(
            KnowledgeDocumentRow(
                id=key,
                title=name,
                kind=kind,
                collection="residencial",
                review_state="educational",
                media_type=media,
                byte_size=len(body.encode()),
                page_count=1,
                text_pages=1,
                search_text=normalize(name),
                provenance=dict(
                    origins=["QA fictício"],
                    urls=["https://example.org/qa"],
                    groups=[],
                    states_catalogued=[],
                    editions_candidates=[],
                    validation="Exemplo fictício, sem regra habilitada.",
                    territory="Sem associação territorial.",
                ),
            )
        )
        session.flush()
        session.add(
            KnowledgePageRow(
                document_id=key,
                number=1,
                body=body if kind == "guide" else "Diagrama fictício",
                search_text=normalize(body),
            )
        )
    session.add(
        KnowledgeSourceRow(
            id="c" * 64,
            document_id=None,
            title="Fonte QA indisponível",
            url="https://example.org/missing",
            outcome="falha_download",
            provenance={},
        )
    )
    session.commit()
