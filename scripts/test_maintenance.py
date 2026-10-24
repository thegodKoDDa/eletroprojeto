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


def test_compaction_preserves_all_restore_points_and_latest_pointer():
    import test_continuity

    fixture = test_continuity.ContinuityTests()
    fixture.setUp()
    try:
        import continuity

        first = Path(continuity.checkpoint(fixture.root)["checkpoint"])
        second = Path(continuity.checkpoint(fixture.root, force_new=True)["checkpoint"])
        # Simulate legacy independent copies, even on filesystems supporting hardlinks.
        original = second / "data.sqlite3"
        content = original.read_bytes()
        original.unlink()
        original.write_bytes(content)
        pointer = (fixture.root / ".checkpoints/latest.json").read_bytes()
        preview = m.compact(fixture.root)
        assert preview["verified_checkpoints"] == 2
        assert preview["reclaimable_bytes"] > 0
        result = m.compact(fixture.root, apply=True)
        assert result["historical_points_removed"] == 0
        assert (fixture.root / ".checkpoints/latest.json").read_bytes() == pointer
        assert continuity.verify(first)["verified"] and continuity.verify(second)["verified"]
        assert m.compact(fixture.root)["reclaimable_bytes"] == 0 or result["shared"] == 0
    finally:
        fixture.doCleanups()


def test_cleanup_removes_inactive_qa_builds_but_keeps_live_dev_and_installations():
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for name in [
            "frontend/.next/qa-build/output",
            "frontend/.next/qa-simple/output",
            "frontend/.next/dev/live",
            "backend/.venv/installed",
            "backend/.venv-windows/installed",
            ".pytest_cache/cache",
            ".aws",
        ]:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == ".aws":
                path.mkdir()
            else:
                path.write_text("fixture")
        with patch.object(m.socket.socket, "connect_ex", return_value=1):
            m.cleanup(root, apply=True, qa_builds=True)
        assert not (root / "frontend/.next/qa-build").exists()
        assert not (root / "frontend/.next/qa-simple").exists()
        assert not (root / ".pytest_cache").exists()
        assert not (root / ".aws").exists()
        assert (root / "frontend/.next/dev/live").exists()
        assert (root / "backend/.venv/installed").exists()
        assert (root / "backend/.venv-windows/installed").exists()


def test_corrupt_restore_point_stops_compaction_before_replacing_any_copy():
    import continuity
    import test_continuity

    fixture = test_continuity.ContinuityTests()
    fixture.setUp()
    try:
        first = Path(continuity.checkpoint(fixture.root)["checkpoint"])
        second = Path(continuity.checkpoint(fixture.root, force_new=True)["checkpoint"])
        before = (first / "data.sqlite3").stat().st_ino
        pointer = (fixture.root / ".checkpoints/latest.json").read_bytes()
        (second / "source.zip").write_bytes(b"corrupt")
        with pytest.raises(ValueError):
            m.compact(fixture.root, apply=True)
        assert (first / "data.sqlite3").stat().st_ino == before
        assert (fixture.root / ".checkpoints/latest.json").read_bytes() == pointer
        assert continuity.verify(first)["verified"]
    finally:
        fixture.doCleanups()
