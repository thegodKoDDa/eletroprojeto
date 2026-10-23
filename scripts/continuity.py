"""Local continuity: stdlib only; never stops services or commits/pushes files."""

import argparse
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from contextlib import closing, contextmanager
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


@contextmanager
def checkpoint_lock(store):
    path = store / ".checkpoint.lock"
    for attempt in range(2):
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            break
        except FileExistsError:
            if path.is_symlink():
                raise ValueError("Lock de checkpoint não pode ser symlink.")
            recover = False
            try:
                before = path.stat()
                owner = json.loads(path.read_text(encoding="utf-8"))
                if (
                    os.name == "posix"
                    and owner.get("platform") == os.name
                    and owner.get("host") == socket.gethostname()
                    and isinstance(owner.get("pid"), int)
                    and owner["pid"] > 0
                ):
                    try:
                        os.kill(owner["pid"], 0)
                    except ProcessLookupError:
                        after = path.stat()
                        recover = (
                            after.st_dev,
                            after.st_ino,
                            after.st_mtime_ns,
                            after.st_size,
                        ) == (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
                    except PermissionError:
                        pass
            except (OSError, ValueError, TypeError):
                pass
            if recover and attempt == 0:
                path.unlink()
                continue
            raise ValueError(
                "Outro checkpoint está em execução ou deixou lock pendente. Confira o processo antes de remover o lock."
            )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(
                {"pid": os.getpid(), "host": socket.gethostname(), "platform": os.name}, output
            )
            output.flush()
            os.fsync(output.fileno())
        yield
    finally:
        path.unlink(missing_ok=True)


def file_digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def sync_directory(path):
    if os.name == "posix":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def atomic_json(path, value):
    descriptor, name = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, indent=2, ensure_ascii=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def latest_checkpoint(root):
    store = root / ".checkpoints"
    pointer = store / "latest.json"
    if not pointer.is_file() or pointer.is_symlink():
        return None
    try:
        value = json.loads(pointer.read_text(encoding="utf-8"))
        name = value["checkpoint"]
        if not isinstance(name, str) or not name or any(c not in "0123456789TZ" for c in name):
            return None
        folder = store / name
        if folder.is_symlink() or not (folder / "VERIFIED.json").is_file():
            return None
        if file_digest(folder / "manifest.json") != value["manifest_sha256"]:
            return None
        return folder
    except (OSError, ValueError, KeyError, TypeError):
        return None


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
            "refs_sha256": digest(
                read("for-each-ref", "--format=%(refname) %(objectname)")[1].encode()
            ),
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


def check(root, *, inspect_database=True):
    missing = [name for name in DOCS if not (root / name).is_file()]
    if missing:
        raise ValueError("Documentos ausentes: " + ", ".join(missing))
    info = None
    if inspect_database:
        db = database_path(root)
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            info = database_info(connection)
    return {
        "git": git_state(root),
        "database": info,
        "frontend_dependencies": (root / "frontend/node_modules").is_dir(),
        "backend_environment": any(
            (root / name).is_dir() for name in ("backend/.venv", "backend/.venv-windows")
        ),
        "documents": DOCS,
    }


def verify(folder):
    if folder.is_symlink() or any(
        (folder / name).is_symlink()
        for name in ("manifest.json", "source.zip", "data.sqlite3", "repository.bundle")
    ):
        raise ValueError("Checkpoint não pode depender de symlinks.")
    manifest = json.loads((folder / "manifest.json").read_text())
    archive = folder / "source.zip"
    if file_digest(archive) != manifest["archive_sha256"]:
        raise ValueError("Hash do arquivo de código divergente")
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        with zipfile.ZipFile(archive) as zipped:
            if len(zipped.namelist()) != len(manifest["files"]) or set(zipped.namelist()) != set(
                manifest["files"]
            ):
                raise ValueError("Lista de arquivos divergente")
            for name in zipped.namelist():
                if (
                    Path(name).is_absolute()
                    or ".." in Path(name).parts
                    or "\\" in name
                    or ":" in name
                ):
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
        if file_digest(db) != manifest["database_sha256"]:
            raise ValueError("Hash do backup SQLite divergente")
        # Restore through the SQLite API to an isolated file, then read all rows.
        with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as origin:
            with closing(sqlite3.connect(target / "restored.sqlite3")) as restored:
                origin.backup(restored)
                if database_info(restored) != manifest["state"]["database"]:
                    raise ValueError("Estado restaurado divergente")
                for _ in restored.iterdump():
                    pass  # Read every row without retaining the entire SQL dump in RAM.
        if manifest.get("git_bundle_sha256"):
            bundle = folder / "repository.bundle"
            if file_digest(bundle) != manifest["git_bundle_sha256"]:
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


def checkpoint(root, *, force_new=False):
    store = root / ".checkpoints"
    if store.is_symlink():
        raise ValueError("Diretório de checkpoints não pode ser um symlink.")
    store.mkdir(mode=0o700, exist_ok=True)
    os.chmod(store, 0o700)
    with checkpoint_lock(store):
        return _checkpoint(root, force_new=force_new)


def _checkpoint(root, *, force_new=False):
    started = time.perf_counter()
    state = check(root, inspect_database=False)
    store = root / ".checkpoints"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = Path(tempfile.mkdtemp(prefix=".pending-", dir=store))
    files = {}
    with zipfile.ZipFile(
        folder / "source.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=3
    ) as archive:
        for path in source_files(root):
            name = path.relative_to(root).as_posix()
            data = path.read_bytes()
            files[name] = digest(data)
            archive.writestr(name, data)
    current_files = {p.relative_to(root).as_posix(): file_digest(p) for p in source_files(root)}
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
    capture_done = time.perf_counter()
    database_hash = file_digest(db)
    previous = latest_checkpoint(root)
    if previous and not force_new:
        manifest = json.loads((previous / "manifest.json").read_text(encoding="utf-8"))
        old_git = manifest["state"]["git"]
        same_git = all(
            old_git.get(key) == state["git"].get(key)
            for key in ("available", "commit", "branch", "refs_sha256")
        )
        if manifest["files"] == files and manifest["database_sha256"] == database_hash and same_git:
            try:
                result = verify(previous)
            except (OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError):
                pass  # Corruption never qualifies for reuse; create a fresh verified point.
            else:
                shutil.rmtree(folder)  # Only this call's temporary, reproducible capture.
                return {
                    "checkpoint": str(previous),
                    **result,
                    "reused": True,
                    "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                }
    manifest = {
        "created_at": stamp,
        "state": state,
        "files": files,
        "archive_sha256": file_digest(folder / "source.zip"),
        "database_sha256": database_hash,
        "limitations": [
            "Não captura buffers não salvos do editor nem rascunhos do navegador.",
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
        manifest["git_bundle_sha256"] = file_digest(bundle)
        current_git = git_state(root)
        if any(
            current_git.get(key) != state["git"].get(key)
            for key in ("commit", "branch", "refs_sha256")
        ):
            raise ValueError("Histórico Git alterado durante a captura. Repita o checkpoint.")
    atomic_json(folder / "manifest.json", manifest)
    for path in folder.iterdir():
        os.chmod(path, 0o600)
        with path.open("r+b") as durable:
            os.fsync(durable.fileno())
    result = verify(folder)
    atomic_json(folder / "VERIFIED.json", result)
    final = store / stamp
    if final.exists():
        raise ValueError("Identificador de checkpoint já existe; nenhuma cópia foi substituída.")
    folder.rename(final)
    atomic_json(
        store / "latest.json",
        {"checkpoint": stamp, "manifest_sha256": file_digest(final / "manifest.json")},
    )
    return {
        "checkpoint": str(final),
        **result,
        "reused": False,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        "capture_ms": round((capture_done - started) * 1000, 2),
        "retention_review": len(list(store.glob("*/VERIFIED.json"))) > 14,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["encerrar", "retomar", "verificar"])
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument(
        "--force-new", action="store_true", help="Criar novo ponto mesmo sem mudanças."
    )
    parser.add_argument(
        "--documents",
        action="store_true",
        help="Também imprimir estado e pendências; leitura completa continua obrigatória pelo agente.",
    )
    args = parser.parse_args()
    if args.command == "encerrar":
        result = checkpoint(ROOT, force_new=args.force_new)
    elif args.command == "verificar":
        if args.checkpoint is None:
            parser.error("--checkpoint é obrigatório")
        result = verify(args.checkpoint)
    else:
        result = check(ROOT)
        latest = latest_checkpoint(ROOT)
        result["latest_checkpoint"] = str(latest) if latest else None
        result["checkpoint_verification"] = (
            "Ponteiro/hash do manifest conferidos; verificar executa restauração completa."
            if latest
            else "Sem ponteiro latest.json válido; pontos anteriores permanecem no diretório de checkpoints."
        )
        if args.documents:
            for name in ("docs/CURRENT_STATE.md", "docs/KNOWN_ISSUES.md"):
                print((ROOT / name).read_text())
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
