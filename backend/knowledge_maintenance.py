"""Reviewed discard and offline OCR. Original technical PDFs stay immutable."""

import argparse
import csv
import hashlib
import io
import json
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from app.database import KnowledgeDocumentRow, KnowledgePageRow, KnowledgeSourceRow, SessionLocal
from app.knowledge import normalize
from knowledge_admin import LIBRARY, digest_file, load_json
from sqlalchemy import delete, func, select

AUDIT = LIBRARY / "maintenance.json"


def counts(session):
    return dict(
        documents=session.scalar(select(func.count()).select_from(KnowledgeDocumentRow)),
        pages=session.scalar(select(func.count()).select_from(KnowledgePageRow)),
        sources=session.scalar(select(func.count()).select_from(KnowledgeSourceRow)),
    )


def write_audit(audit):
    audit["updated_at"] = datetime.now(timezone.utc).isoformat()
    temporary = AUDIT.with_suffix(".pending.json")
    temporary.write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    temporary.chmod(0o600)
    os.replace(temporary, AUDIT)


def discard():
    audit = load_json(AUDIT) if AUDIT.exists() else dict(discarded=[], ocr=[])
    if audit["discarded"]:
        if audit.get("status") == "discarding":
            raise ValueError(
                "Descarte interrompido: confira transação e inventário antes de prosseguir."
            )
        print("Descarte já aplicado; mantendo registro imutável.")
        return
    with SessionLocal() as session:
        rows = session.scalars(
            select(KnowledgeDocumentRow).where(KnowledgeDocumentRow.review_state == "out_of_scope")
        ).all()
        # Only objectively unrelated books and interruption/expurgo reports.
        if any(
            not (
                "book_" in normalize(row.title)
                or (
                    "relatorio" in normalize(row.title)
                    and any(term in normalize(row.title) for term in ("expurgo", "interrupcao"))
                )
            )
            for row in rows
        ):
            raise ValueError("Classificação sem justificativa específica; recusa exclusão.")
        records = []
        for row in rows:
            path = LIBRARY / "objects" / row.id
            if digest_file(path) != row.id:
                raise ValueError("Objeto divergente; recusa exclusão")
            records.append(
                dict(
                    id=row.id,
                    title=row.title,
                    byte_size=row.byte_size,
                    reason="Livro sem conteúdo elétrico ou relatório de interrupção/expurgo, sem aplicação no estudo residencial.",
                )
            )
        # Persist the deletion intent before touching either DB or objects.
        audit["discarded"] = records
        audit["status"] = "discarding"
        write_audit(audit)
        for row in rows:
            for source in session.scalars(
                select(KnowledgeSourceRow).where(KnowledgeSourceRow.document_id == row.id)
            ):
                source.document_id = None
                source.outcome = "discarded_out_of_scope"
                source.provenance = {
                    **source.provenance,
                    "discard_reason": records[[r.id for r in rows].index(row.id)]["reason"],
                }
            session.flush()
            session.execute(delete(KnowledgePageRow).where(KnowledgePageRow.document_id == row.id))
            session.delete(row)
        session.commit()
        audit["expected_counts"] = counts(session)
    for record in records:
        (LIBRARY / "objects" / record["id"]).unlink()
    audit["status"] = "complete"
    write_audit(audit)
    print(
        json.dumps(
            dict(
                discarded=len(records),
                bytes_removed=sum(r["byte_size"] for r in records),
                counts=audit["expected_counts"],
            )
        ),
        flush=True,
    )


def recognize(task):
    import pymupdf

    key, number, binary, data_root = task
    path = LIBRARY / "objects" / key
    with pymupdf.open(path, filetype="pdf") as document:
        page = document[number - 1]
        scale = min(200 / 72, (16000000 / (page.rect.width * page.rect.height)) ** 0.5)
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csGRAY, alpha=False
        )
        if min(pix.samples) >= 250:
            return (
                key,
                number,
                "blank",
                "",
                None,
                "Página visualmente vazia, sem contraste significativo.",
            )
        image = pix.tobytes("png")
    environment = {
        **os.environ,
        "OMP_THREAD_LIMIT": "1",
        "TESSDATA_PREFIX": data_root,
        "LD_LIBRARY_PATH": str(Path(binary).parent.parent / "lib/x86_64-linux-gnu"),
    }
    try:
        result = subprocess.run(
            [binary, "stdin", "stdout", "-l", "por+eng", "--psm", "11", "tsv"],
            input=image,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            timeout=100,
            check=True,
        )
        words = []
        confidence = []
        previous = None
        for row in csv.DictReader(io.StringIO(result.stdout.decode("utf-8")), delimiter="\t"):
            word = (row.get("text") or "").strip()
            if not word:
                continue
            line = (row["block_num"], row["par_num"], row["line_num"])
            if words and line != previous:
                words.append("\n")
            words.append(word)
            previous = line
            value = float(row["conf"])
            if value >= 0:
                confidence.append(value)
        body = " ".join(words).replace(" \n ", "\n")
        return (
            key,
            number,
            "ocr_unreviewed" if body else "image_no_text",
            body,
            round(sum(confidence) / len(confidence)) if confidence else None,
            "Tesseract5.5.0 por+eng,200dpi máximo; reconhecimento automático, conferir valores no original.",
        )
    except (subprocess.SubprocessError, UnicodeError, ValueError) as exc:
        return key, number, "ocr_failed", "", None, str(exc)[:1000]


def ocr(binary, data_root, workers):
    audit = load_json(AUDIT) if AUDIT.exists() else dict(discarded=[], ocr=[])
    with SessionLocal() as session:
        tasks = [
            (key, number, binary, data_root)
            for key, number in session.execute(
                select(KnowledgePageRow.document_id, KnowledgePageRow.number).where(
                    KnowledgePageRow.body == "", KnowledgePageRow.extraction_method == "native_text"
                )
            ).all()
        ]
    audit["status"] = "ocr_running"
    write_audit(audit)
    print("OCR queue", len(tasks), flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(recognize, task) for task in tasks]
        for i, future in enumerate(as_completed(futures), 1):
            key, number, method, body, confidence, note = future.result()
            with SessionLocal() as session:
                row = session.get(KnowledgePageRow, (key, number))
                if row.body:
                    raise ValueError("Página alterada durante OCR; recusa sobrescrita")
                row.body = body
                row.search_text = normalize(body)
                row.extraction_method = method
                row.extraction_note = note
                row.ocr_confidence = confidence
                if body:
                    document = session.get(KnowledgeDocumentRow, key)
                    document.text_pages += 1
                session.commit()
            audit["ocr"].append(
                dict(
                    document_id=key,
                    page=number,
                    method=method,
                    confidence=confidence,
                    body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                )
            )
            if i % 25 == 0:
                write_audit(audit)
                print("OCR", i, "/", len(tasks), flush=True)
    with SessionLocal() as session:
        audit["expected_counts"] = counts(session)
        audit["ocr"] = [
            dict(
                document_id=page.document_id,
                page=page.number,
                method=page.extraction_method,
                confidence=page.ocr_confidence,
                body_sha256=hashlib.sha256(page.body.encode()).hexdigest(),
            )
            for page in session.scalars(
                select(KnowledgePageRow).where(KnowledgePageRow.extraction_method != "native_text")
            )
        ]
    audit["status"] = "complete"
    write_audit(audit)
    print("OCR finished", len(tasks), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["discard", "ocr"])
    parser.add_argument("--binary")
    parser.add_argument("--data-root")
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9))
    args = parser.parse_args()
    if args.command == "discard":
        discard()
    else:
        if not args.binary or not args.data_root:
            parser.error("OCR requer binary e data-root explícitos.")
        ocr(args.binary, args.data_root, args.workers)
