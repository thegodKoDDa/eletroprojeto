"""Create a source ZIP and checksums exclusively from a reviewed Git commit."""

import argparse
import hashlib
import io
import json
import re
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def forbidden(path):
    parts = Path(path).parts
    name = Path(path).name.lower()
    return (
        any(
            part
            in {".git", ".checkpoints", ".venv", ".venv-windows", "node_modules", "__pycache__"}
            for part in parts
        )
        or path.startswith(("references/library/", "references/territory/", "data/", "dist/"))
        or (name.startswith(".env") and name != ".env.example")
        or name.endswith(
            (".db", ".db-wal", ".db-shm", ".sqlite", ".sqlite3", ".pdf", ".pem", ".key", ".bundle")
        )
    )


def write_once(path, content):
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(
                f"{path.name} já existe com conteúdo diferente; use outro diretório de saída."
            )
        return
    path.write_bytes(content)


def package(root, destination, ref="HEAD"):
    commit = (
        git(root, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    )
    version = json.loads(git(root, "show", commit + ":frontend/package.json"))["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", version):
        raise ValueError("Versão de distribuição inválida.")
    for entry in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
        if not entry:
            continue
        metadata, path = entry.split(b"\t", 1)
        path = path.decode()
        if forbidden(path) or metadata.startswith(b"120000 "):
            raise ValueError(f"Arquivo privado ou symlink não permitido na distribuição: {path}")
    prefix = f"EletroProjeto-v{version}/"
    archive = git(root, "archive", "--format=zip", "--prefix=" + prefix, commit)
    content = io.BytesIO(archive)
    hashes = {}
    with zipfile.ZipFile(content, "a", compression=zipfile.ZIP_DEFLATED) as output:
        for item in output.infolist():
            if not item.is_dir():
                relative = item.filename.removeprefix(prefix)
                if forbidden(relative) or relative.startswith("/") or ".." in Path(relative).parts:
                    raise ValueError("Caminho inválido no ZIP.")
                hashes[relative] = hashlib.sha256(output.read(item.filename)).hexdigest()
        manifest = dict(
            version=version,
            commit=commit,
            kind="source",
            bundled_runtimes=False,
            requirements={"python": ">=3.11", "node": ">=20.9"},
            files=hashes,
        )
        manifest_data = (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode()
        date = datetime.fromisoformat(
            git(root, "show", "-s", "--format=%cI", commit).decode().strip()
        )
        info = zipfile.ZipInfo(prefix + "build-manifest.json", date.timetuple()[:6])
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        output.writestr(info, manifest_data)
    destination.mkdir(parents=True, exist_ok=True)
    files = {"EletroProjeto-source.zip": content.getvalue(), "build-manifest.json": manifest_data}
    checksums = "".join(
        hashlib.sha256(data).hexdigest() + "  " + name + "\n" for name, data in files.items()
    ).encode()
    files["SHA256SUMS.txt"] = checksums
    for name, data in files.items():
        write_once(destination / name, data)
    return dict(version=version, commit=commit, files=len(hashes), output=str(destination))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--ref", default="HEAD")
    args = parser.parse_args()
    print(json.dumps(package(ROOT, args.output, args.ref), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
