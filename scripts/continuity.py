"""Local continuity: stdlib only; never stops services or commits/pushes files."""

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    "AGENTS.md",
    "README.md",
    "CHANGELOG.md",
    "docs/PROJECT_MEMORY.md",
    "docs/CURRENT_STATE.md",
    "docs/SESSION_HISTORY.md",
    "docs/KNOWN_ISSUES.md",
    "docs/architecture.md",
    "docs/calculations.md",
    "docs/standards.md",
    "docs/roadmap.md",
]
EXCLUDED = {
    ".git",
    ".checkpoints",
    ".venv",
    ".venv-windows",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "coverage",
    "test-results",
    "playwright-report",
    ".aws",
    ".ssh",
    ".codex",
    ".agents",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_files(root):
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in EXCLUDED
            and not d.endswith((".egg-info", ".dist-info"))
            and not (Path(directory) / d).is_symlink()
        )
        for name in sorted(files):
            path = Path(directory) / name
            lower = name.lower()
            if path.is_symlink() or (lower.startswith(".env") and lower != ".env.example"):
                continue
            if lower.endswith(
                (
                    ".db",
                    ".db-wal",
                    ".db-shm",
                    ".db-journal",
                    ".sqlite",
                    ".sqlite3",
                    ".pem",
                    ".key",
                    ".p12",
                    ".pfx",
                    ".pyc",
                    ".tsbuildinfo",
                    ".log",
                    ".zip",
                    ".gpg",
                    ".tar",
                    ".tar.gz",
                    ".tgz",
                    ".7z",
                    ".bundle",
                    ".pdf",
                    ":zone.identifier",
                )
            ):
                continue
            if lower in {"credentials", "id_rsa", "id_ed25519"}:
                continue
            yield path


def git_state(root):
    def read(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
        return result.returncode, result.stdout.strip()

    try:
        code, status = read("status", "--short", "--branch", "--untracked-files=all")
        if code:
            return {
                "available": False,
                "reason": "Git não reconhece um repositório neste diretório.",
            }
        return {
            "available": True,
            "status": status,
            "branch": read("branch", "--show-current")[1],
            "commit": read("rev-parse", "--verify", "HEAD")[1] or None,
        }
    except FileNotFoundError:
        return {"available": False, "reason": "Git não instalado."}


def database_path(root):
    url = os.environ.get("DATABASE_URL")
    if not url:
        return root / "backend/eletroprojeto.db"
    if not url.startswith("sqlite:///") or "?" in url or url.endswith(":memory:"):
        raise ValueError(
            "DATABASE_URL não é um arquivo SQLite simples; use backup específico do banco configurado."
        )
    path = Path(url[len("sqlite:///") :])
    if not path.is_absolute():
        raise ValueError(
            "DATABASE_URL relativo: informe um caminho absoluto para evitar copiar outro banco."
        )
    return path


def database_info(connection):
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite com falha de integridade")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("SQLite com falha de integridade referencial")
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    counts = {
        name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        for name in ("projects", "calculation_history", "technical_revisions")
        if name in tables
    }
    if "projects" in tables:
        counts["active_projects"] = connection.execute(
            "SELECT COUNT(*) FROM projects WHERE deleted_at IS NULL"
        ).fetchone()[0]
        counts["deleted_projects"] = counts["projects"] - counts["active_projects"]
    return {
        "integrity": "ok",
        "counts": counts,
        "migration": [r[0] for r in connection.execute("SELECT version_num FROM alembic_version")]
        if "alembic_version" in tables
        else [],
    }


def check(root):
    missing = [name for name in DOCS if not (root / name).is_file()]
    if missing:
        raise ValueError("Documentos ausentes: " + ", ".join(missing))
    db = database_path(root)
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        info = database_info(connection)
    return {
        "git": git_state(root),
        "database": info,
        "frontend_dependencies": (root / "frontend/node_modules").is_dir(),
        "backend_environment": (root / "backend/.venv").is_dir(),
        "documents": DOCS,
    }


def verify(folder):
    manifest = json.loads((folder / "manifest.json").read_text())
    archive = folder / "source.zip"
    if digest(archive.read_bytes()) != manifest["archive_sha256"]:
        raise ValueError("Hash do arquivo de código divergente")
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        with zipfile.ZipFile(archive) as zipped:
            if set(zipped.namelist()) != set(manifest["files"]):
                raise ValueError("Lista de arquivos divergente")
            for name in zipped.namelist():
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    raise ValueError("Caminho inseguro no arquivo")
                data = zipped.read(name)
                if digest(data) != manifest["files"][name]:
                    raise ValueError("Hash divergente: " + name)
                destination = target / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
        for name in DOCS:
            (target / name).read_text(encoding="utf-8")
        db = folder / "data.sqlite3"
        if digest(db.read_bytes()) != manifest["database_sha256"]:
            raise ValueError("Hash do backup SQLite divergente")
        # Restore through the SQLite API to an isolated file, then read all rows.
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as origin:
            with closing(sqlite3.connect(target / "restored.sqlite3")) as restored:
                origin.backup(restored)
                if database_info(restored) != manifest["state"]["database"]:
                    raise ValueError("Estado restaurado divergente")
                list(restored.iterdump())
        if manifest.get("git_bundle_sha256"):
            bundle = folder / "repository.bundle"
            if digest(bundle.read_bytes()) != manifest["git_bundle_sha256"]:
                raise ValueError("Hash do histórico Git divergente")
            clone = target / "git-restore"
            subprocess.run(
                ["git", "clone", "--bare", str(bundle.resolve()), str(clone)],
                check=True,
                capture_output=True,
            )
            head = subprocess.run(
                ["git", "-C", str(clone), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            if head != manifest["state"]["git"]["commit"]:
                raise ValueError("Commit restaurado divergente")
    return {
        "verified": True,
        "files": len(manifest["files"]),
        "database": manifest["state"]["database"],
    }


def checkpoint(root):
    state = check(root)
    store = root / ".checkpoints"
    store.mkdir(mode=0o700, exist_ok=True)
    os.chmod(store, 0o700)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = store / stamp
    folder.mkdir(mode=0o700)
    files = {}
    with zipfile.ZipFile(folder / "source.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in source_files(root):
            name = path.relative_to(root).as_posix()
            data = path.read_bytes()
            files[name] = digest(data)
            archive.writestr(name, data)
    current_files = {
        p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in source_files(root)
    }
    if current_files != files:
        raise ValueError(
            "Arquivos alterados durante a captura. Repita o checkpoint sem edição concorrente."
        )
    db = folder / "data.sqlite3"
    with closing(
        sqlite3.connect(database_path(root).resolve().as_uri() + "?mode=ro", uri=True)
    ) as origin:
        with closing(sqlite3.connect(db)) as target:
            origin.backup(target)
            state["database"] = database_info(target)
    manifest = {
        "created_at": stamp,
        "state": state,
        "files": files,
        "archive_sha256": digest((folder / "source.zip").read_bytes()),
        "database_sha256": digest(db.read_bytes()),
        "limitations": [
            "Não captura buffers não salvos do editor.",
            "Não substitui cópia externa.",
            "Fonte exclui dependências e arquivos privados conhecidos; revisar também segredos no histórico Git.",
        ],
    }
    if state["git"].get("available") and state["git"].get("commit"):
        bundle = folder / "repository.bundle"
        subprocess.run(
            ["git", "-C", str(root), "bundle", "create", str(bundle.resolve()), "--all"],
            check=True,
            capture_output=True,
        )
        manifest["git_bundle_sha256"] = digest(bundle.read_bytes())
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    for path in folder.iterdir():
        os.chmod(path, 0o600)
    result = verify(folder)
    (folder / "VERIFIED.json").write_text(json.dumps(result, indent=2) + "\n")
    os.chmod(folder / "VERIFIED.json", 0o600)
    # Retention is deliberately explicit: never delete old recovery points automatically.
    return {
        "checkpoint": str(folder),
        **result,
        "retention_review": len(list(store.glob("*/VERIFIED.json"))) > 14,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["encerrar", "retomar", "verificar"])
    parser.add_argument("--checkpoint", type=Path)
    args = parser.parse_args()
    if args.command == "encerrar":
        result = checkpoint(ROOT)
    elif args.command == "verificar":
        if args.checkpoint is None:
            parser.error("--checkpoint é obrigatório")
        result = verify(args.checkpoint)
    else:
        result = check(ROOT)
        for name in ("docs/CURRENT_STATE.md", "docs/KNOWN_ISSUES.md"):
            print((ROOT / name).read_text())
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
