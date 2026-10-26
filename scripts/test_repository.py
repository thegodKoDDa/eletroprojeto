import io
import json
import subprocess
from unittest.mock import patch

import pytest
import repository as r


def run(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


@pytest.fixture
def repositories(tmp_path):
    remote, local = tmp_path / "remote.git", tmp_path / "local"
    run(tmp_path, "init", "--bare", str(remote))
    run(tmp_path, "init", "--initial-branch=main", str(local))
    run(local, "config", "user.name", "QA")
    run(local, "config", "user.email", "qa@example.invalid")
    (local / "README.md").write_text("QA source")
    run(local, "add", "README.md")
    run(local, "commit", "-m", "baseline")
    run(local, "remote", "add", "origin", str(remote))
    run(local, "push", "--set-upstream", "origin", "main")
    with patch.object(r, "REMOTES", {str(remote)}), patch.object(r, "public_origin"):
        yield local, remote


def test_push_matches_remote_and_does_not_commit_files(repositories):
    local, remote = repositories
    (local / "README.md").write_text("reviewed change")
    run(local, "commit", "-am", "reviewed")
    result = r.synchronize(local)
    assert result["ok"]
    assert result["commit"] == run(remote, "rev-parse", "main")
    assert run(local, "status", "--porcelain") == ""


def test_unreviewed_files_never_get_uploaded(repositories):
    local, remote = repositories
    old = run(remote, "rev-parse", "main")
    (local / "private-unreviewed.txt").write_text("not reviewed")
    assert not r.synchronize(local)["ok"]
    assert run(remote, "rev-parse", "main") == old
    assert (local / "private-unreviewed.txt").read_text() == "not reviewed"


def test_remote_changes_are_not_merged_or_overwritten(repositories, tmp_path):
    local, remote = repositories
    other = tmp_path / "other"
    run(tmp_path, "clone", "--branch", "main", str(remote), str(other))
    run(other, "config", "user.name", "QA")
    run(other, "config", "user.email", "qa@example.invalid")
    (other / "README.md").write_text("remote change")
    run(other, "commit", "-am", "remote")
    run(other, "push", "origin", "main")
    (local / "README.md").write_text("local change")
    run(local, "commit", "-am", "local")
    before = run(local, "rev-parse", "HEAD")
    remote_before = run(remote, "rev-parse", "main")
    assert not r.synchronize(local)["ok"]
    assert run(local, "rev-parse", "HEAD") == before
    assert run(remote, "rev-parse", "main") == remote_before
    assert (local / "README.md").read_text() == "local change"


def test_private_repository_is_refused_without_exposing_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "qa-only-not-a-real-token")
    response = io.BytesIO(json.dumps({"full_name": r.REPOSITORY, "private": True}).encode())
    with (
        patch.object(
            r, "git", return_value=subprocess.CompletedProcess([], 0, next(iter(r.REMOTES)), "")
        ),
        patch.object(r, "urlopen", return_value=response),
    ):
        with pytest.raises(ValueError, match="público"):
            r.public_origin(tmp_path)


def test_unexpected_remote_never_receives_credentials(tmp_path):
    with (
        patch.object(
            r,
            "git",
            return_value=subprocess.CompletedProcess(
                [], 0, "https://example.invalid/repository.git", ""
            ),
        ),
        patch.object(r, "urlopen") as request,
    ):
        with pytest.raises(ValueError, match="origin"):
            r.public_origin(tmp_path)
        request.assert_not_called()


def test_offline_fetch_preserves_local_and_remote_commits(repositories):
    local, remote = repositories
    before = run(local, "rev-parse", "HEAD")
    original = r.git

    def offline(root, *args, **kwargs):
        if args[0] == "fetch":
            return subprocess.CompletedProcess([], 1, "", "offline")
        return original(root, *args, **kwargs)

    with patch.object(r, "git", side_effect=offline):
        assert not r.synchronize(local)["ok"]
    assert run(local, "rev-parse", "HEAD") == run(remote, "rev-parse", "main") == before


def test_public_repository_is_checked_anonymously(tmp_path, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "qa-only-never-sent")
    response = io.BytesIO(json.dumps({"full_name": r.REPOSITORY, "private": False}).encode())
    with (
        patch.object(
            r, "git", return_value=subprocess.CompletedProcess([], 0, next(iter(r.REMOTES)), "")
        ),
        patch.object(r, "urlopen", return_value=response) as request,
    ):
        r.public_origin(tmp_path)
        assert not request.call_args.args[0].has_header("Authorization")


def test_public_visibility_does_not_authorize_another_repository(tmp_path):
    response = io.BytesIO(
        json.dumps({"full_name": "other-owner/other-repo", "private": False}).encode()
    )
    with (
        patch.object(
            r, "git", return_value=subprocess.CompletedProcess([], 0, next(iter(r.REMOTES)), "")
        ),
        patch.object(r, "urlopen", return_value=response),
    ):
        with pytest.raises(ValueError, match="Destino"):
            r.public_origin(tmp_path)
