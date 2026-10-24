"""Reference ingestion/search must not enable rules or mutate projects."""

import hashlib
import json

import pytest
from app.database import KnowledgeDocumentRow, KnowledgePageRow, KnowledgeSourceRow, get_session
from app.knowledge import NOTICE, normalize
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def library_client(database_engine, tmp_path, monkeypatch):
    sessions = sessionmaker(database_engine, expire_on_commit=False)
    key = hashlib.sha256(b"%PDF-local-test").hexdigest()
    (tmp_path / key).write_bytes(b"%PDF-local-test")
    monkeypatch.setenv("KNOWLEDGE_ROOT", str(tmp_path))
    with sessions() as session:
        provenance = dict(
            origins=["original.pdf"],
            urls=["https://example.org/manual.pdf"],
            groups=["Grupo de referência"],
            states_catalogued=["SP"],
            editions_candidates=["histórica"],
            validation=NOTICE,
            territory="Sem associação municipal validada.",
        )
        session.add(
            KnowledgeDocumentRow(
                id=key,
                title="Manual de instalação",
                kind="pdf",
                collection="distribuidoras",
                review_state="pending_review",
                media_type="application/pdf",
                byte_size=15,
                page_count=2,
                text_pages=1,
                search_text=normalize("Manual de instalação"),
                provenance=provenance,
            )
        )
        session.flush()
        session.add_all(
            [
                KnowledgePageRow(
                    document_id=key,
                    number=1,
                    body="Proteção do chuveiro: 100% não significa validação.",
                    search_text=normalize("Proteção do chuveiro: 100% não significa validação."),
                ),
                KnowledgePageRow(document_id=key, number=2, body="", search_text=""),
            ]
        )
        session.add(
            KnowledgeSourceRow(
                id="a" * 64,
                document_id=None,
                title="Download indisponível",
                url="https://example.org/missing.pdf",
                outcome="falha_download",
                provenance={"status": "falha_download"},
            )
        )
        session.commit()

    def override():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, key, tmp_path
    finally:
        app.dependency_overrides.clear()


async def test_content_search_accents_literal_wildcards_and_pending_state(library_client):
    client, key, _ = library_client
    for q in ["PROTECAO", "chuveiro", "100%"]:
        result = await client.get("/api/v1/knowledge/documents", params={"q": q})
        assert result.status_code == 200
        assert [x["id"] for x in result.json()["items"]] == [key]
        assert result.json()["items"][0]["review_state"] == "pending_review"
    for q in ["%", "_", "neverfound"]:
        result = await client.get("/api/v1/knowledge/documents", params={"q": q, "kind": "guide"})
        assert result.json()["items"] == []
    assert (await client.get("/api/v1/knowledge/documents", params={"q": "_"})).json()[
        "items"
    ] == []
    assert (await client.get("/api/v1/knowledge/documents?limit=0")).status_code == 422
    assert (await client.get("/api/v1/knowledge/documents?offset=-1")).status_code == 422
    assert (await client.get("/api/v1/knowledge/documents?q=" + "a" * 161)).status_code == 422


async def test_pages_metadata_and_unavailable_sources_are_distinct(library_client):
    client, key, _ = library_client
    stats = (await client.get("/api/v1/knowledge/stats")).json()
    assert (stats["documents"], stats["pages"], stats["text_pages"], stats["sources"]) == (
        1,
        2,
        1,
        1,
    )
    assert "não valida" in stats["notice"]
    assert (await client.get(f"/api/v1/knowledge/documents/{key}/pages?q=chuveiro")).json()[0][
        "number"
    ] == 1
    assert (await client.get(f"/api/v1/knowledge/documents/{key}/pages?offset=1")).json() == [
        {
            "number": 2,
            "body": "",
            "extraction_method": "native_text",
            "extraction_note": "",
            "ocr_confidence": None,
        }
    ]
    assert (await client.get("/api/v1/knowledge/sources?outcome=falha_download")).json()[0][
        "document_id"
    ] is None
    assert (await client.get("/api/v1/knowledge/documents/" + "b" * 64)).status_code == 404
    assert (await client.get("/api/v1/knowledge/documents/invalid/file")).status_code == 404


async def test_original_file_is_hashed_contained_and_non_executable(library_client):
    client, key, folder = library_client
    result = await client.get(f"/api/v1/knowledge/documents/{key}/file")
    assert result.status_code == 200
    assert result.content == b"%PDF-local-test"
    assert result.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in result.headers["content-security-policy"]
    (folder / key).unlink()
    (folder / key).symlink_to(folder / "outside")
    assert (await client.get(f"/api/v1/knowledge/documents/{key}/file")).status_code == 404


def test_verification_refuses_changed_inputs_before_removal(database_engine, tmp_path, monkeypatch):
    import knowledge_admin as admin

    root = tmp_path
    library = root / "references/library"
    objects = library / "objects"
    objects.mkdir(parents=True)
    folder = root / "references/elétrica"
    folder.mkdir()
    original = folder / "test.md"
    original.write_text("original")
    key = hashlib.sha256(b"original").hexdigest()
    (objects / key).write_bytes(b"original")
    entry = dict(origin="references/elétrica/test.md", sha256=key, bytes=8)
    (library / "inventory.json").write_text(json.dumps(dict(objects=[entry], entries=[entry])))
    (library / "import-result.json").write_text(
        json.dumps(dict(complete=True, documents=0, pages=0))
    )
    monkeypatch.setattr(admin, "ROOT", root)
    monkeypatch.setattr(admin, "LIBRARY", library)
    monkeypatch.setattr(admin, "INPUTS", [folder])
    monkeypatch.setattr(admin, "SessionLocal", sessionmaker(database_engine))
    original.write_text("changed")
    with pytest.raises(ValueError, match="Entrada nova ou alterada"):
        admin.verify(remove_inputs=True)
    assert original.exists()
    original.write_text("original")
    (objects / key).write_bytes(b"corrupt!")
    with pytest.raises(ValueError, match="Objeto divergente"):
        admin.verify(remove_inputs=True)
    assert original.exists()


def test_collection_preserves_zip_only_members_and_deduplicates(tmp_path, monkeypatch):
    import zipfile

    import knowledge_admin as admin

    folders = [tmp_path / "references/elétrica", tmp_path / "references/normas"]
    for folder in folders:
        folder.mkdir(parents=True)
    (folders[0] / "same.txt").write_bytes(b"same")
    with zipfile.ZipFile(folders[1] / "archive.zip", "w") as archive:
        archive.writestr("nested/same.txt", b"same")
        archive.writestr("../escape.txt", b"only in archive")
    library = tmp_path / "references/library"
    monkeypatch.setattr(admin, "ROOT", tmp_path)
    monkeypatch.setattr(admin, "INPUTS", folders)
    monkeypatch.setattr(admin, "LIBRARY", library)
    admin.collect()
    inventory = json.loads((library / "inventory.json").read_text())
    assert len(inventory["entries"]) == 4
    assert len(inventory["objects"]) == 2
    assert not (tmp_path / "escape.txt").exists()
    assert all(
        admin.digest_file(library / "objects" / item["sha256"]) == item["sha256"]
        for item in inventory["objects"]
    )


def test_ingest_is_idempotent_and_retains_blank_pages(database_engine, tmp_path, monkeypatch):
    import knowledge_admin as admin

    pdf = pytest.importorskip("pymupdf")
    folder = tmp_path / "references/elétrica/Biblioteca/01_Guias_de_estudo"
    folder.mkdir(parents=True)
    (folder / "01_estudo.md").write_text(
        "# Guia de estudo\nExemplo hipotético, sem dimensionamento."
    )
    path = folder.parent / "test.pdf"
    with pdf.open() as document:
        page = document.new_page()
        page.insert_text((30, 30), "Referencia de teste")
        document.new_page()
        document.save(path)
    (folder.parent / "diagram.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><style>text{fill:red}</style><text>Diagrama didático</text></svg>'
    )
    library = tmp_path / "references/library"
    monkeypatch.setattr(admin, "ROOT", tmp_path)
    monkeypatch.setattr(admin, "INPUTS", [tmp_path / "references/elétrica"])
    monkeypatch.setattr(admin, "LIBRARY", library)
    monkeypatch.setattr(admin, "SessionLocal", sessionmaker(database_engine))
    admin.collect()
    admin.ingest()
    first = json.loads((library / "import-result.json").read_text())
    admin.ingest()
    second = json.loads((library / "import-result.json").read_text())
    assert first == second
    assert (first["documents"], first["pages"], first["text_pages"]) == (3, 4, 3)
    admin.verify(remove_inputs=True)
    assert not (tmp_path / "references/elétrica").exists()
    assert (library / "inventory.json").exists()


def test_discard_is_audited_and_refuses_technical_documents(database_engine, tmp_path, monkeypatch):
    import knowledge_maintenance as maintenance

    library = tmp_path / "library"
    objects = library / "objects"
    objects.mkdir(parents=True)
    key = hashlib.sha256(b"irrelevant book").hexdigest()
    (objects / key).write_bytes(b"irrelevant book")
    sessions = sessionmaker(database_engine)
    with sessions() as session:
        session.add(
            KnowledgeDocumentRow(
                id=key,
                title="book_conto.pdf",
                kind="pdf",
                collection="distribuidoras",
                review_state="out_of_scope",
                media_type="application/pdf",
                byte_size=15,
                page_count=1,
                text_pages=1,
                search_text="book",
                provenance={},
            )
        )
        session.flush()
        session.add(
            KnowledgePageRow(document_id=key, number=1, body="ficção", search_text="ficcao")
        )
        session.add(
            KnowledgeSourceRow(
                id="d" * 64,
                document_id=key,
                title="Book",
                url="https://example.org/book",
                outcome="pdf_validado",
                provenance={},
            )
        )
        session.commit()
    monkeypatch.setattr(maintenance, "LIBRARY", library)
    monkeypatch.setattr(maintenance, "AUDIT", library / "maintenance.json")
    monkeypatch.setattr(maintenance, "SessionLocal", sessions)
    maintenance.discard()
    assert not (objects / key).exists()
    audit = json.loads((library / "maintenance.json").read_text())
    assert audit["discarded"][0]["id"] == key
    with sessions() as session:
        assert session.get(KnowledgeDocumentRow, key) is None
        assert session.get(KnowledgeSourceRow, "d" * 64).outcome == "discarded_out_of_scope"
        assert session.get(KnowledgeSourceRow, "d" * 64).document_id is None
    maintenance.discard()  # Safe repetition.


def test_ocr_blank_page_does_not_require_recognizer(database_engine, tmp_path, monkeypatch):
    import knowledge_maintenance as maintenance

    pdf = pytest.importorskip("pymupdf")
    objects = tmp_path / "objects"
    objects.mkdir()
    path = objects / ("e" * 64)
    with pdf.open() as document:
        document.new_page()
        document.save(path)
    monkeypatch.setattr(maintenance, "LIBRARY", tmp_path)
    result = maintenance.recognize(("e" * 64, 1, "unavailable", "unavailable"))
    assert result[2] == "blank"
    assert result[3] == ""


@pytest.mark.parametrize(
    "title", ["Manual técnico de cabos", "Proteção e interrupção de circuitos"]
)
def test_discard_refuses_technical_document_without_specific_reason(
    database_engine, tmp_path, monkeypatch, title
):
    import knowledge_maintenance as maintenance

    sessions = sessionmaker(database_engine)
    with sessions() as session:
        session.add(
            KnowledgeDocumentRow(
                id="f" * 64,
                title=title,
                kind="pdf",
                collection="residencial",
                review_state="out_of_scope",
                media_type="application/pdf",
                byte_size=1,
                page_count=1,
                text_pages=1,
                search_text="cabos",
                provenance={},
            )
        )
        session.commit()
    monkeypatch.setattr(maintenance, "LIBRARY", tmp_path)
    monkeypatch.setattr(maintenance, "AUDIT", tmp_path / "maintenance.json")
    monkeypatch.setattr(maintenance, "SessionLocal", sessions)
    with pytest.raises(ValueError, match="justificativa específica"):
        maintenance.discard()
    with sessions() as session:
        assert session.get(KnowledgeDocumentRow, "f" * 64) is not None
