import sqlite3

import pytest
from pydantic import ValidationError
from technical_admin import Candidate, backup


def test_backup_preserves_data_and_never_overwrites(tmp_path):
    source, target = tmp_path / "source.db", tmp_path / "backup.db"
    with sqlite3.connect(source) as db:
        db.execute("create table example(value text)")
        db.execute("insert into example values ('preserved')")
    backup(source, target)
    with sqlite3.connect(target) as db:
        assert db.execute("select value from example").fetchone()[0] == "preserved"
    with pytest.raises(ValueError):
        backup(source, target)


def test_external_candidate_requires_evidence_and_valid_url():
    data = dict(
        document_id="ndu001",
        edition="test",
        source_url="https://www.energisa.com.br/normas-tecnicas",
        consulted_on="2026-10-21",
        changes="Revisão para análise",
        affected_rules=["demand"],
        evidence="Portal oficial",
    )
    assert Candidate.model_validate(data).document_id == "ndu001"
    with pytest.raises(ValidationError):
        Candidate.model_validate({**data, "source_url": "javascript:alert(1)"})
    with pytest.raises(ValidationError):
        Candidate.model_validate({**data, "evidence": ""})
