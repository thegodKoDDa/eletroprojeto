"""Local installation audit and allowlisted cleanup; never removes project data."""

import argparse
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from continuity import ROOT, atomic_json, check, source_files


def private_paths(root):
    yield root / ".checkpoints", True
    for folder in (root / "backend", root / "frontend", root):
        for path in folder.glob(".env*"):
            if path.name != ".env.example" and path.is_file():
                yield path, False
    for folder in (root / "backend", root / "backend/backups"):
        for pattern in ("*.db", "*.db-*", "*.sqlite", "*.sqlite3"):
            for path in folder.glob(pattern):
                yield path, False
    store = root / ".checkpoints"
    if store.is_dir() and not store.is_symlink():
        for directory, dirs, files in os.walk(store, followlinks=False):
            dirs[:] = [name for name in dirs if not (Path(directory) / name).is_symlink()]
            for name in dirs:
                yield Path(directory) / name, True
            for name in files:
                yield Path(directory) / name, False


def permissions(root, *, fix=False):
    result = []
    for path, directory in private_paths(root):
        if not path.exists() or path.is_symlink():
            continue
        try:
            if not safe_generated(root, path):
                continue
        except ValueError:
            result.append({"path": str(path.relative_to(root)), "skipped": "symlink ancestor"})
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        expected = 0o700 if directory else 0o600
        if os.name == "posix" and mode != expected:
            item = dict(path=str(path.relative_to(root)), before=oct(mode), expected=oct(expected))
            if fix:
                os.chmod(path, expected)
                item["fixed"] = stat.S_IMODE(path.stat().st_mode) == expected
            result.append(item)
    return {
        "platform": os.name,
        "private_modes": result,
        "acl_note": "POSIX modes checked"
        if os.name == "posix"
        else "Windows ACLs need native inspection; chmod is not an ACL audit",
        "world_writable_source": [
            str(p.relative_to(root)) for p in source_files(root) if p.stat().st_mode & stat.S_IWOTH
        ],
    }


def command(args, cwd):
    started = time.perf_counter()
    try:
        run = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=30)
        return dict(
            ok=run.returncode == 0,
            exit_code=run.returncode,
            output=(run.stdout + run.stderr).strip(),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return dict(ok=False, error=str(error))


def doctor(root, *, fix_permissions=False):
    environment = (
        "backend/.venv-windows"
        if os.name == "nt" and (root / "backend/.venv-windows/Scripts/python.exe").is_file()
        else "backend/.venv"
    )
    python = root / environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm") or "npm"
    commands = {
        "python": command([str(python), "--version"], root),
        "pip": command([str(python), "-m", "pip", "check"], root),
        "node": command(["node", "--version"], root),
        "npm": command([npm, "--version"], root),
        "frontend_packages": command([npm, "ls", "--depth=0", "--json"], root / "frontend"),
        "git": command(["git", "--version"], root),
    }
    services = {}
    for name, url in (
        ("api", "http://127.0.0.1:8000/api/v1/health"),
        ("frontend", "http://127.0.0.1:3000"),
    ):
        try:
            with urlopen(url, timeout=5) as response:
                services[name] = {"status": response.status}
                if name == "api":
                    services[name]["health"] = json.loads(response.read(4096))
        except (OSError, URLError) as error:
            services[name] = {"unavailable": str(error)}
    return dict(
        state=check(root),
        checkpoint_work={
            "pending": [p.name for p in (root / ".checkpoints").glob(".pending-*")],
            "lock_present": (root / ".checkpoints/.checkpoint.lock").exists(),
        },
        installations=commands,
        permissions=permissions(root, fix=fix_permissions),
        services=services,
    )


def safe_generated(root, path):
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Limpeza não segue symlinks: " + str(relative))
    return path.resolve().is_relative_to(root.resolve())


def cleanup(root, *, apply=False, qa_builds=False):
    paths = [
        root / name
        for name in (
            ".ruff_cache",
            "backend/.ruff_cache",
            "backend/.pytest_cache",
            "frontend/tsconfig.tsbuildinfo",
            "backend/__pycache__",
            "__pycache__",
        )
    ]
    for name in ("backend/app", "backend/tests", "backend/alembic", "scripts"):
        for directory, dirs, _ in os.walk(root / name, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(directory) / d).is_symlink()]
            if "__pycache__" in dirs:
                paths.append(Path(directory) / "__pycache__")
                dirs.remove("__pycache__")
    qa_busy = False
    try:
        for port in (3010, 3011, 8010, 8011):
            with socket.socket() as connection:
                connection.settimeout(0.2)
                if connection.connect_ex(("127.0.0.1", port)) == 0:
                    qa_busy = True
    except OSError:
        qa_busy = True  # Unknown port state is not permission to delete test output.
    if not qa_busy:
        paths += [root / "frontend/test-results", root / "frontend/playwright-report"]
        if qa_builds:
            paths += [root / "frontend/.next/e2e", root / "frontend/.next/e2e-auth"]
    entries = []
    for path in paths:
        if not path.exists() or not safe_generated(root, path):
            continue
        size = (
            sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink())
            if path.is_dir()
            else path.stat().st_size
        )
        entries.append(dict(path=str(path.relative_to(root)), bytes=size))
        if apply:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    result = dict(
        applied=apply,
        entries=entries,
        bytes=sum(e["bytes"] for e in entries),
        qa_outputs_skipped=qa_busy,
        preserved=[
            "projects/databases",
            "history",
            "references",
            "checkpoints",
            "Git",
            "environments",
            "node_modules",
            "Next active/build/cache",
        ],
    )
    if apply:
        store = root / ".checkpoints"
        store.mkdir(mode=0o700, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        atomic_json(store / f"cleanup-{stamp}.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "clean"])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--qa-builds", action="store_true")
    parser.add_argument("--fix-permissions", action="store_true")
    args = parser.parse_args()
    result = (
        doctor(ROOT, fix_permissions=args.fix_permissions)
        if args.command == "doctor"
        else cleanup(ROOT, apply=args.apply, qa_builds=args.qa_builds)
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.command == "doctor" and any(
        not item["ok"] for item in result["installations"].values()
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()
