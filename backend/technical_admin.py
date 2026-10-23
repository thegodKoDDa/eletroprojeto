"""Local-only review staging and SQLite backup. No public mutation endpoints.

Imports are untrusted candidates: they never replace the runtime registry.
"""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from app.database import SessionLocal, TechnicalRevisionRow, utcnow
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class Candidate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_id: str = Field(min_length=1, max_length=100)
    edition: str = Field(min_length=1, max_length=100)
    source_url: HttpUrl
    consulted_on: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    changes: str = Field(min_length=1, max_length=10000)
    affected_rules: list[str] = Field(max_length=100)
    evidence: str = Field(min_length=1, max_length=10000)


def stage(path: Path):
    if path.stat().st_size > 1_000_000:
        raise ValueError("Arquivo excede 1 MB")
    candidate = Candidate.model_validate_json(path.read_text())
    payload = candidate.model_dump(mode="json")
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    with SessionLocal() as session:
        if session.get(TechnicalRevisionRow, digest) is None:
            session.add(
                TechnicalRevisionRow(
                    id=digest,
                    payload=payload,
                    created_at=utcnow(),
                    review_status="candidate_not_published",
                )
            )
            session.commit()
    return digest


def backup(source: Path, destination: Path):
    if destination.exists():
        raise ValueError("Destino já existe; backup não será sobrescrito")
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as origin:
        with closing(sqlite3.connect(destination)) as target:
            origin.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Backup falhou na verificação de integridade")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    importing = sub.add_parser("stage")
    importing.add_argument("path", type=Path)
    copying = sub.add_parser("backup")
    copying.add_argument("source", type=Path)
    copying.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "stage":
        print(stage(args.path))
    else:
        backup(args.source, args.destination)
        print("Backup íntegro criado")
