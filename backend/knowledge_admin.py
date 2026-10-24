"""Import local references; never enable calculation rules or edit projects."""

import argparse
import hashlib
import json
import os
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

from app.database import KnowledgeDocumentRow, KnowledgePageRow, KnowledgeSourceRow, SessionLocal
from app.knowledge import normalize
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "references/library"
INPUTS = [ROOT / "references/elétrica", ROOT / "references/normas"]


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect():
    LIBRARY.mkdir(parents=True, exist_ok=True, mode=0o700)
    objects = LIBRARY / "objects"
    objects.mkdir(parents=True, exist_ok=True, mode=0o700)
    entries, unique = [], {}

    def preserve(stream, origin):
        temporary = objects / ".ingesting"
        digest, size = hashlib.sha256(), 0
        with temporary.open("wb") as target:
            while block := stream.read(1024 * 1024):
                digest.update(block)
                size += len(block)
                target.write(block)
        key = digest.hexdigest()
        destination = objects / key
        if destination.exists():
            temporary.unlink()
        else:
            os.replace(temporary, destination)
        destination.chmod(0o600)
        record = dict(origin=origin, sha256=key, bytes=size)
        entries.append(record)
        unique.setdefault(key, record)

    for folder in INPUTS:
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError("Pasta de entrada ausente ou simbólica")
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():
                raise ValueError("Link simbólico na entrada")
            if not path.is_file():
                continue
            origin = path.relative_to(ROOT).as_posix()
            if path.suffix.lower() == ".zip":
                entries.append(
                    dict(
                        origin=origin,
                        sha256=digest_file(path),
                        bytes=path.stat().st_size,
                        archive=True,
                    )
                )
                with zipfile.ZipFile(path) as archive:
                    for member in archive.infolist():
                        if not member.is_dir():
                            with archive.open(member) as stream:
                                preserve(stream, origin + "!/" + member.filename)
            else:
                with path.open("rb") as stream:
                    preserve(stream, origin)
    temporary = LIBRARY / "inventory.pending.json"
    temporary.write_text(
        json.dumps(
            dict(schema=1, entries=entries, objects=list(unique.values())),
            ensure_ascii=False,
            indent=2,
        )
    )
    os.replace(temporary, LIBRARY / "inventory.json")
    print(json.dumps(dict(entries=len(entries), objects=len(unique))))


def imported_sources(inventory):
    rows = []
    for item in inventory["objects"]:
        name = item["origin"].split("!/")[-1]
        if name.endswith("manifesto_completo.json") or name.endswith(
            "05_Fontes_e_atualizacoes/fontes.json"
        ):
            rows.extend(load_json(LIBRARY / "objects" / item["sha256"]))
    return rows


def describe(paths, sources):
    name = next((p for p in paths if "!/" not in p), paths[0])
    basename = Path(name).name
    if basename.lower().endswith(".pdf"):
        kind, media, collection = "pdf", "application/pdf", "distribuidoras"
        if "elétrica/" in name:
            collection = "residencial"
        title = next((s.get("titulo") for s in sources if s.get("titulo")), basename)
    elif "/01_Guias_de_estudo/" in name:
        kind, media, collection, title = "guide", "text/markdown", "residencial", basename
    elif "/03_Modelos_e_checklists/" in name:
        kind, media, collection, title = "template", "text/markdown", "residencial", basename
    elif basename.endswith(".svg"):
        kind, media, collection, title = "diagram", "image/svg+xml", "residencial", basename
    else:
        return None
    state = "educational" if kind != "pdf" else "pending_review"
    lower = normalize(" ".join(paths))
    if "historico" in lower:
        state = "historical"
    elif "vigencia_2027" in lower or "vigencia_futura" in lower:
        state = "future_effective_candidate"
    elif any(s.get("minuta_identificada_no_titulo_ou_url") is True for s in sources):
        state = "draft"
    elif any(s.get("status") == "excluido_fora_escopo" for s in sources) or any(
        word in lower for word in ("book_", "expurgo", "relatorio de interrupcao")
    ):
        state = "out_of_scope"
    provenance = {
        "origins": paths,
        "urls": sorted(
            {
                s.get("url_final") or s.get("url")
                for s in sources
                if s.get("url_final") or s.get("url")
            }
        ),
        "groups": sorted({s["grupo"] for s in sources if s.get("grupo")}),
        "states_catalogued": sorted({s["ufs"] for s in sources if s.get("ufs")}),
        "editions_candidates": sorted({str(s["versao"]) for s in sources if s.get("versao")}),
        "validation": "Importado; revisão técnica, vigência e aplicabilidade não certificadas. Nenhuma regra habilitada.",
        "territory": "UF de catalogação ou referência de grupo não comprova cobertura municipal.",
    }
    return kind, media, collection, str(title)[:1000], state, provenance


def ingest():
    import pymupdf

    if (LIBRARY / "maintenance.json").exists():
        raise ValueError("Acervo revisado por manutenção; não reimporte o inventário histórico.")
    inventory = load_json(LIBRARY / "inventory.json")
    sources = imported_sources(inventory)
    by_hash, paths = defaultdict(list), defaultdict(list)
    for entry in sources:
        if entry.get("sha256"):
            by_hash[entry["sha256"]].append(entry)
    for entry in inventory["entries"]:
        if not entry.get("archive"):
            paths[entry["sha256"]].append(entry["origin"])
    stats = dict(documents=0, pages=0, text_pages=0, errors=[], objects=len(inventory["objects"]))
    for item in inventory["objects"]:
        key = item["sha256"]
        description = describe(paths[key], by_hash[key])
        if description is None:
            continue
        with SessionLocal() as session:
            existing = session.get(KnowledgeDocumentRow, key)
            if existing:
                stats["documents"] += 1
                stats["pages"] += existing.page_count
                stats["text_pages"] += existing.text_pages
                continue
            kind, media, collection, title, state, provenance = description
            path = LIBRARY / "objects" / key
            pages = []
            try:
                if media == "application/pdf":
                    with pymupdf.open(path, filetype="pdf") as pdf:
                        if pdf.needs_pass:
                            raise ValueError("PDF cifrado sem senha")
                        for number, page in enumerate(pdf, 1):
                            body = page.get_text(sort=True)
                            pages.append(
                                dict(
                                    document_id=key,
                                    number=number,
                                    body=body,
                                    search_text=normalize(body),
                                )
                            )
                elif media == "text/markdown":
                    body = path.read_text(encoding="utf-8-sig")
                    title = next(
                        (line.lstrip("# ") for line in body.splitlines() if line.startswith("# ")),
                        title,
                    )[:1000]
                    pages.append(
                        dict(document_id=key, number=1, body=body, search_text=normalize(body))
                    )
                else:
                    import xml.etree.ElementTree as ET

                    tree = ET.fromstring(path.read_bytes())
                    labels = [
                        " ".join(element.itertext()).strip()
                        for element in tree.iter()
                        if element.tag.rsplit("}", 1)[-1] in {"text", "title", "desc"}
                    ]
                    body = "\n".join(label for label in labels if label)
                    title = next((label for label in labels if label), title)[:1000]
                    pages.append(
                        dict(document_id=key, number=1, body=body, search_text=normalize(body))
                    )
            except Exception as exc:
                stats["errors"].append(dict(id=key, origin=paths[key][0], error=str(exc)))
                continue
            extracted = sum(bool(p["search_text"]) for p in pages)
            row = KnowledgeDocumentRow(
                id=key,
                title=title,
                kind=kind,
                collection=collection,
                review_state=state,
                media_type=media,
                byte_size=item["bytes"],
                page_count=len(pages),
                text_pages=extracted,
                search_text=normalize(title + " " + json.dumps(provenance, ensure_ascii=False)),
                provenance=provenance,
            )
            session.add(row)
            session.flush()
            session.execute(KnowledgePageRow.__table__.insert(), pages)
            session.commit()
            stats["documents"] += 1
            stats["pages"] += len(pages)
            stats["text_pages"] += extracted
            if stats["documents"] % 100 == 0:
                print(json.dumps({k: v for k, v in stats.items() if k != "errors"}), flush=True)
    with SessionLocal() as session:
        for entry in sources:
            key = hashlib.sha256(
                json.dumps(entry, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            if session.get(KnowledgeSourceRow, key):
                continue
            doc_id = entry.get("sha256")
            if not doc_id or not session.get(KnowledgeDocumentRow, doc_id):
                doc_id = None
            session.add(
                KnowledgeSourceRow(
                    id=key,
                    document_id=doc_id,
                    title=str(entry.get("titulo", "Referência"))[:1000],
                    url=entry.get("url_final") or entry.get("url") or "",
                    outcome=entry.get("status", "unknown")[:80],
                    provenance=entry,
                )
            )
        session.commit()
        stats["sources"] = session.scalar(select(func.count()).select_from(KnowledgeSourceRow))
    stats["complete"] = not stats["errors"]
    (LIBRARY / "import-result.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(json.dumps(stats, ensure_ascii=False), flush=True)
    if stats["errors"]:
        raise SystemExit("Importação incompleta; entradas preservadas.")


def verify(remove_inputs=False):
    inventory = load_json(LIBRARY / "inventory.json")
    result = load_json(LIBRARY / "import-result.json")
    if not result.get("complete"):
        raise ValueError("Importação não concluída.")
    maintenance_path = LIBRARY / "maintenance.json"
    maintenance = load_json(maintenance_path) if maintenance_path.exists() else {}
    if maintenance and maintenance.get("status") != "complete":
        raise ValueError("Manutenção do acervo em andamento ou incompleta.")
    discarded = {item["id"] for item in maintenance.get("discarded", [])}
    for entry in inventory["objects"]:
        path = LIBRARY / "objects" / entry["sha256"]
        if entry["sha256"] in discarded:
            if path.exists():
                raise ValueError("Objeto descartado ainda presente: " + entry["sha256"])
            continue
        if (
            path.is_symlink()
            or not path.is_file()
            or path.stat().st_size != entry["bytes"]
            or digest_file(path) != entry["sha256"]
        ):
            raise ValueError("Objeto divergente: " + entry["sha256"])
    expected_counts = maintenance.get("expected_counts", result)
    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(KnowledgeDocumentRow))
        pages = session.scalar(select(func.count()).select_from(KnowledgePageRow))
        sources = session.scalar(select(func.count()).select_from(KnowledgeSourceRow))
        if (
            count != expected_counts["documents"]
            or pages != expected_counts["pages"]
            or sources != expected_counts.get("sources", 0)
        ):
            raise ValueError("Banco divergente do relatório de importação.")
    if not discarded.issubset({item["sha256"] for item in inventory["objects"]}):
        raise ValueError("Descarte sem origem no inventário histórico")
    with SessionLocal() as session:
        for item in maintenance.get("ocr", []):
            page = session.get(KnowledgePageRow, (item["document_id"], item["page"]))
            if (
                page is None
                or hashlib.sha256(page.body.encode()).hexdigest() != item["body_sha256"]
                or page.extraction_method != item["method"]
                or page.search_text != normalize(page.body)
            ):
                raise ValueError("Texto OCR divergente do registro de manutenção")
    expected = {e["origin"]: e for e in inventory["entries"] if "!/" not in e["origin"]}
    for folder in INPUTS:
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if path.is_symlink():
                raise ValueError("Link simbólico nas entradas")
            if path.is_file():
                entry = expected.get(path.relative_to(ROOT).as_posix())
                if (
                    entry is None
                    or path.stat().st_size != entry["bytes"]
                    or digest_file(path) != entry["sha256"]
                ):
                    raise ValueError("Entrada nova ou alterada: " + str(path))
    if remove_inputs:
        for folder in INPUTS:
            if folder.exists():
                shutil.rmtree(folder)
    (LIBRARY / "verification.json").write_text(
        json.dumps(
            dict(
                verified=True,
                objects=len(inventory["objects"]) - len(discarded),
                discarded_objects=len(discarded),
                documents=count,
                pages=pages,
                inputs_removed=remove_inputs,
            ),
            indent=2,
        )
    )
    print((LIBRARY / "verification.json").read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["collect", "import", "verify"])
    parser.add_argument("--remove-inputs", action="store_true")
    args = parser.parse_args()
    if args.command == "collect":
        if args.remove_inputs:
            parser.error("Exclusão somente em verify após os testes.")
        collect()
    elif args.command == "import":
        if args.remove_inputs:
            parser.error("Exclusão somente em verify após os testes.")
        ingest()
    else:
        verify(args.remove_inputs)
