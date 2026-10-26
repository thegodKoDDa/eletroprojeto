import hashlib
import json
import subprocess
import zipfile

import package_release as release
import pytest


def command(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    command(root, "init", "--initial-branch=main")
    command(root, "config", "user.name", "QA")
    command(root, "config", "user.email", "qa@example.invalid")
    (root / "frontend").mkdir()
    (root / "frontend/package.json").write_text('{"version":"1.2.3"}')
    (root / "README.md").write_text("public source")
    command(root, "add", ".")
    command(root, "commit", "-m", "reviewed")
    return root


def test_archive_has_only_committed_files_with_manifest_and_matching_hashes(source, tmp_path):
    (source / "private.db").write_text("not for release")
    (source / "README.md").write_text("unreviewed modification")
    destination = tmp_path / "output"
    release.package(source, destination)
    with zipfile.ZipFile(destination / "EletroProjeto-source.zip") as archive:
        assert all("private.db" not in path for path in archive.namelist())
        assert archive.read("EletroProjeto-v1.2.3/README.md") == b"public source"
        manifest = json.loads(archive.read("EletroProjeto-v1.2.3/build-manifest.json"))
        for path, digest in manifest["files"].items():
            assert (
                hashlib.sha256(archive.read("EletroProjeto-v1.2.3/" + path)).hexdigest() == digest
            )
    for line in (destination / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split("  ")
        assert hashlib.sha256((destination / name).read_bytes()).hexdigest() == digest
    release.package(
        source, destination
    )  # identical regeneration is allowed without replacing recovery points
    (destination / "build-manifest.json").write_text("different")
    with pytest.raises(ValueError, match="diferente"):
        release.package(source, destination)


@pytest.mark.parametrize(
    "name", [".env", "data/project.db", "references/territory/raw.json", "private.key"]
)
def test_tracked_private_files_are_refused_instead_of_distributed(source, tmp_path, name):
    path = source / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("private fixture")
    command(source, "add", name)
    command(source, "commit", "-m", "invalid fixture")
    with pytest.raises(ValueError, match="privado"):
        release.package(source, tmp_path / "output")
    assert not (tmp_path / "output/EletroProjeto-source.zip").exists()
