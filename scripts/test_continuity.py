import importlib.util
import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "continuity", Path(__file__).with_name("continuity.py")
)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in c.DOCS:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Documento de retomada\n", encoding="utf-8")
        db = self.root / "backend/eletroprojeto.db"
        db.parent.mkdir()
        self.db = sqlite3.connect(db)
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE projects (id TEXT, deleted_at TEXT)")
        self.db.execute("CREATE TABLE alembic_version (version_num TEXT)")
        self.db.execute("INSERT INTO alembic_version VALUES ('0003')")
        self.db.execute("INSERT INTO projects VALUES ('ativo', NULL), ('lixeira', '2026-10-22')")
        self.db.commit()
        self.env = patch.dict(
            "os.environ",
            {key: os.environ[key] for key in ("PATH", "SYSTEMROOT") if key in os.environ},
            clear=True,
        )
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_checkpoint_restores_committed_wal_and_preserves_original(self):
        before = self.db.execute("SELECT * FROM projects").fetchall()
        result = c.checkpoint(self.root)
        self.assertTrue(result["verified"])
        self.assertEqual(result["database"]["counts"]["active_projects"], 1)
        self.assertEqual(self.db.execute("SELECT * FROM projects").fetchall(), before)
        self.assertTrue(c.verify(Path(result["checkpoint"]))["verified"])

    def test_secrets_dependencies_symlinks_and_database_excluded_from_source(self):
        for name in (
            ".env",
            ".env.local",
            "secret.pem",
            "private.tar.gpg",
            "reference.pdf",
            "node_modules/dep.js",
            ".venv-windows/private.txt",
            ".ruff_cache/result",
            "package.egg-info/PKG-INFO",
            "package.dist-info/METADATA",
            ".checkpoints/private.txt",
        ):
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            path.write_text("private")
        (self.root / ".env.example").write_text("PORT=8000")
        names = {p.relative_to(self.root).as_posix() for p in c.source_files(self.root)}
        self.assertIn(".env.example", names)
        self.assertFalse(
            {
                ".env",
                ".env.local",
                "secret.pem",
                "private.tar.gpg",
                "reference.pdf",
                "node_modules/dep.js",
                ".venv-windows/private.txt",
                ".ruff_cache/result",
                "package.egg-info/PKG-INFO",
                "package.dist-info/METADATA",
                ".checkpoints/private.txt",
                "link",
                "backend/eletroprojeto.db",
            }
            & names
        )

    def test_symlinks_are_excluded_when_platform_allows_them(self):
        private = self.root / ".env"
        private.write_text("private")
        try:
            (self.root / "link").symlink_to(private)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest(
                    "Windows sem privilégio de criação de symlink; demais exclusões testadas separadamente."
                )
            raise
        self.assertNotIn(
            "link", {p.relative_to(self.root).as_posix() for p in c.source_files(self.root)}
        )

    def test_corruption_is_rejected(self):
        folder = Path(c.checkpoint(self.root)["checkpoint"])
        (folder / "source.zip").write_bytes(b"corrompido")
        with self.assertRaises(ValueError):
            c.verify(folder)

    def test_missing_memory_blocks_checkpoint(self):
        (self.root / "docs/CURRENT_STATE.md").unlink()
        with self.assertRaises(ValueError):
            c.checkpoint(self.root)

    def test_distinct_checkpoints_and_resume_state(self):
        first = c.checkpoint(self.root)["checkpoint"]
        second = c.checkpoint(self.root)["checkpoint"]
        self.assertNotEqual(first, second)
        self.assertEqual(c.check(self.root)["database"]["counts"]["projects"], 2)

    @unittest.skipUnless(shutil.which("git"), "Git não disponível")
    def test_git_history_is_restored_and_corruption_rejected(self):
        def git(*args):
            return subprocess.run(
                ["git", "-C", str(self.root), *args], check=True, capture_output=True, text=True
            )

        git("init")
        git("add", "AGENTS.md")
        git(
            "-c",
            "user.name=QA",
            "-c",
            "user.email=qa@example.invalid",
            "commit",
            "-m",
            "QA baseline",
        )
        folder = Path(c.checkpoint(self.root)["checkpoint"])
        self.assertTrue((folder / "repository.bundle").is_file())
        self.assertTrue(c.verify(folder)["verified"])
        (folder / "repository.bundle").write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            c.verify(folder)


if __name__ == "__main__":
    unittest.main()
