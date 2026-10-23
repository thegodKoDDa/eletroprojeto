import importlib.util
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

spec = importlib.util.spec_from_file_location(
    "maintenance", Path(__file__).with_name("maintenance.py")
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_cleanup_only_removes_allowlisted_generated_data():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for name in [
            "backend/app/__pycache__/a.pyc",
            "backend/eletroprojeto.db",
            ".checkpoints/data.sqlite3",
            "frontend/node_modules/keep",
            "frontend/.next/dev/keep",
            "references/keep.pdf",
            "backend/app/keep.py",
        ]:
            p = root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("keep-or-regenerate")
        with patch.object(m.socket.socket, "connect_ex", return_value=1):
            preview = m.cleanup(root)
            assert preview["bytes"] and not preview["applied"]
            assert (root / "backend/app/__pycache__/a.pyc").exists()
            result = m.cleanup(root, apply=True)
        assert result["applied"]
        assert not (root / "backend/app/__pycache__").exists()
        for name in [
            "backend/eletroprojeto.db",
            ".checkpoints/data.sqlite3",
            "frontend/node_modules/keep",
            "frontend/.next/dev/keep",
            "references/keep.pdf",
            "backend/app/keep.py",
        ]:
            assert (root / name).exists()


def test_cleanup_refuses_symlink_and_preserves_busy_test_output():
    with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as other:
        root = Path(folder)
        (root / "frontend/test-results").mkdir(parents=True)
        (root / "frontend/test-results/keep").write_text("running")
        with patch.object(m.socket.socket, "connect_ex", return_value=0):
            assert m.cleanup(root, apply=True)["qa_outputs_skipped"]
        assert (root / "frontend/test-results/keep").exists()
        try:
            (root / ".ruff_cache").symlink_to(other, target_is_directory=True)
        except OSError:
            pytest.skip("Symlinks unavailable")
        with pytest.raises(ValueError):
            m.cleanup(root, apply=True)
        assert Path(other).exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX modes; not Windows ACLs")
def test_private_permissions_fixed_without_touching_source():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        (root / "backend").mkdir()
        db = root / "backend/eletroprojeto.db"
        db.write_text("private")
        db.chmod(0o644)
        source = root / "code.py"
        source.write_text("source")
        source.chmod(0o644)
        assert m.permissions(root)["private_modes"]
        result = m.permissions(root, fix=True)
        assert result["private_modes"][0]["fixed"]
        assert db.stat().st_mode & 0o777 == 0o600
        assert source.stat().st_mode & 0o777 == 0o644
