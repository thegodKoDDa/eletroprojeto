import socket
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import start_local as start


def test_occupied_port_is_refused_without_stopping_existing_listener():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(ValueError, match="ocupada"):
            start.check_ports([port])
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass


def test_explicit_data_directory_and_legacy_database_are_separate(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    assert start.database_path(tmp_path, None) == tmp_path / "data/eletroprojeto.db"
    previous = backend / "eletroprojeto.db"
    previous.write_text("preservar")
    assert start.database_path(tmp_path, None) == previous
    assert start.database_path(tmp_path, tmp_path / "other") == tmp_path / "other/eletroprojeto.db"
    assert previous.read_text() == "preservar"


def test_locked_dependencies_respect_platform_markers_and_never_guess(tmp_path):
    lock = tmp_path / "requirements.lock"
    lock.write_text("fastapi==1.0\ncolorama==2.0; sys_platform == 'win32'\n")
    result = start.pins(lock)
    assert result["fastapi"] == "1.0"
    assert ("colorama" in result) == (sys.platform == "win32")
    lock.write_text("fastapi==1.0; unknown_marker == 'anything'\n")
    with pytest.raises(ValueError, match="Condição"):
        start.pins(lock)


def test_source_and_proxy_changes_invalidate_compiled_frontend(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/page.tsx").write_text("first")
    for name in (
        "package.json",
        "package-lock.json",
        "next.config.ts",
        "tsconfig.json",
        "postcss.config.mjs",
    ):
        (tmp_path / name).write_text("source")
    first = start.fingerprint(tmp_path, "http://127.0.0.1:8000")
    assert first != start.fingerprint(tmp_path, "http://127.0.0.1:8001")
    (tmp_path / "src/page.tsx").write_text("changed")
    assert first != start.fingerprint(tmp_path, "http://127.0.0.1:8000")


def test_migration_preserves_previous_database_before_upgrade(tmp_path):
    db = tmp_path / "project.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE alembic_version(version_num TEXT)")
        conn.execute("INSERT INTO alembic_version VALUES ('old')")
        conn.execute("CREATE TABLE projects(name TEXT)")
        conn.execute("INSERT INTO projects VALUES ('preserved')")
    with (
        patch.object(start.subprocess, "check_output", return_value="new (head)\n"),
        patch.object(start, "run") as upgrade,
    ):
        start.migrate(Path(sys.executable), tmp_path, db, {})
        upgrade.assert_called_once()
    backup = next((tmp_path / "backups").glob("*.sqlite3"))
    with sqlite3.connect(backup) as conn:
        assert conn.execute("SELECT name FROM projects").fetchall() == [("preserved",)]
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT name FROM projects").fetchall() == [("preserved",)]


def test_current_schema_does_not_migrate_or_duplicate_backups(tmp_path):
    db = tmp_path / "project.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE alembic_version(version_num TEXT)")
        conn.execute("INSERT INTO alembic_version VALUES ('current')")
    with (
        patch.object(start.subprocess, "check_output", return_value="current (head)\n"),
        patch.object(start, "run") as upgrade,
    ):
        start.migrate(Path(sys.executable), tmp_path, db, {})
        upgrade.assert_not_called()
    assert not (tmp_path / "backups").exists()


@pytest.mark.parametrize("fails", [False, True])
def test_build_preserves_tracked_configuration_even_on_failure(tmp_path, fails):
    originals = {"tsconfig.json": b'{"include": ["src"]}\n', "next-env.d.ts": b"// original\n"}
    for name, content in originals.items():
        (tmp_path / name).write_bytes(content)

    def build(*args):
        for name in originals:
            (tmp_path / name).write_text("generated QA paths")
        if fails:
            raise RuntimeError("build failed")

    with patch.object(start, "run", side_effect=build):
        if fails:
            with pytest.raises(RuntimeError, match="build failed"):
                start.build_frontend("node", tmp_path, {})
        else:
            start.build_frontend("node", tmp_path, {})
    for name, content in originals.items():
        assert (tmp_path / name).read_bytes() == content
