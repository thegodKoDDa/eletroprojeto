"""Prepare and run the local web application; no Git or real-project mutation."""

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd, env):
    subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)


def check_ports(ports):
    for port in ports:
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as error:
                raise ValueError(
                    f"Porta {port} ocupada. Nenhum serviço existente será encerrado."
                ) from error


def pins(path):
    result = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirement, _, marker = line.partition(";")
        if marker:
            match = re.fullmatch(r"""\s*sys_platform\s*==\s*['"]([^'"]+)['"]\s*""", marker)
            if not match:
                raise ValueError(
                    "Condição de dependência não reconhecida; preparação manual necessária."
                )
            if match[1] != sys.platform:
                continue
        name, version = requirement.strip().split("==")
        result[name.lower().replace("_", "-")] = version
    return result


def python_ready(python, backend):
    if not python.is_file():
        return False
    code = "import importlib.metadata as m,json; print(json.dumps({d.metadata['Name'].lower().replace('_','-'):d.version for d in m.distributions()}))"
    result = subprocess.run([str(python), "-c", code], capture_output=True, text=True)
    if result.returncode:
        return False
    installed = json.loads(result.stdout)
    return all(
        installed.get(name) == version
        for name, version in pins(backend / "requirements.lock").items()
    )


def node_ready(frontend):
    lock = json.loads((frontend / "package-lock.json").read_text())
    root = lock["packages"][""]
    for name in {**root.get("dependencies", {}), **root.get("devDependencies", {})}:
        package = frontend / "node_modules" / name / "package.json"
        if (
            not package.exists()
            or json.loads(package.read_text())["version"]
            != lock["packages"]["node_modules/" + name]["version"]
        ):
            return False
    return True


def fingerprint(frontend, proxy):
    digest = hashlib.sha256(proxy.encode())
    paths = [
        frontend / name
        for name in (
            "package.json",
            "package-lock.json",
            "next.config.ts",
            "tsconfig.json",
            "postcss.config.mjs",
        )
    ]
    paths += sorted((frontend / "src").rglob("*"))
    for path in paths:
        if path.is_file():
            digest.update(path.relative_to(frontend).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def database_path(root, data_dir):
    if data_dir is not None:
        return data_dir.resolve() / "eletroprojeto.db"
    previous = root / "backend" / "eletroprojeto.db"
    return previous if previous.exists() else root / "data" / "eletroprojeto.db"


def migrate(python, backend, database, env):
    heads = subprocess.check_output(
        [str(python), "-m", "alembic", "heads"], cwd=backend, env=env, text=True
    )
    expected = {line.split()[0] for line in heads.splitlines() if line.strip()}
    current = set()
    if database.exists():
        with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as source:
            if source.execute(
                "SELECT name FROM sqlite_master WHERE name='alembic_version'"
            ).fetchone():
                current = {
                    row[0] for row in source.execute("SELECT version_num FROM alembic_version")
                }
            if current != expected:
                destination = (
                    database.parent
                    / "backups"
                    / (
                        "before-migration-"
                        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                        + ".sqlite3"
                    )
                )
                destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with sqlite3.connect(destination) as backup:
                    source.backup(backup)
                    if backup.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise ValueError("Cópia anterior à migração falhou na verificação.")
                destination.chmod(0o600)
    if current != expected:
        run([python, "-m", "alembic", "upgrade", "head"], backend, env)
    if database.exists():
        database.chmod(0o600)


def wait_http(url, children, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if any(child.poll() is not None for child in children):
            raise ValueError(
                "Um serviço terminou antes de ficar disponível; confira a saída acima."
            )
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (URLError, OSError):
            time.sleep(0.2)
    raise ValueError(f"O serviço não respondeu em {url}.")


def serve(python, node, backend, frontend_command, env, api_port, web_port, browser):
    check_ports([api_port, web_port])
    children = []
    process_options = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {}
    )
    previous_handlers = {}

    def stop(_signal, _frame):
        raise KeyboardInterrupt

    for name in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[name] = signal.signal(name, stop)
    try:
        children.append(
            subprocess.Popen(
                [
                    str(python),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                    "--no-proxy-headers",
                ],
                cwd=backend,
                env=env,
                **process_options,
            )
        )
        wait_http(f"http://127.0.0.1:{api_port}/api/v1/health", children)
        children.append(
            subprocess.Popen(
                [str(node), *map(str, frontend_command)],
                cwd=ROOT / "frontend" if (ROOT / "frontend").exists() else ROOT / "web",
                env=env,
                **process_options,
            )
        )
        url = f"http://127.0.0.1:{web_port}"
        wait_http(url, children)
        print(
            f"\nEletroProjeto disponível em {url}\nDados: {env['DATABASE_URL']}\nCtrl+C para encerrar estes serviços.\n",
            flush=True,
        )
        if browser:
            webbrowser.open(url)
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        raise ValueError("Um serviço encerrou; os demais serão parados.")
    except KeyboardInterrupt:
        return
    finally:
        for name, previous in previous_handlers.items():
            signal.signal(name, previous)
        for child in reversed(children):
            if child.poll() is None:
                if os.name == "nt":
                    child.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    child.terminate()
        for child in reversed(children):
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                print(
                    f"O processo iniciado {child.pid} ainda está encerrando; não foi forçado.",
                    file=sys.stderr,
                )


def main():
    parser = argparse.ArgumentParser(description="Preparar e iniciar o EletroProjeto localmente.")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Preparar dependências ausentes/desatualizadas a partir dos locks.",
    )
    parser.add_argument(
        "--prepare-only", action="store_true", help="Preparar e compilar sem iniciar serviços."
    )
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--container", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not all(1 <= p <= 65535 for p in (args.port, args.api_port)) or args.port == args.api_port:
        parser.error("Portas devem ser distintas e estar entre 1 e 65535.")
    if sys.version_info < (3, 11):
        parser.error("Python 3.11 ou superior necessário.")
    check_ports([args.api_port, args.port])
    backend, frontend = ROOT / "backend", ROOT / "frontend"
    node = shutil.which("node")
    if not node:
        raise ValueError("Node.js 20.9+ não encontrado. Instale o runtime ou utilize Docker.")
    version = subprocess.check_output([node, "--version"], text=True).strip().removeprefix("v")
    if tuple(map(int, version.split(".")[:2])) < (20, 9):
        raise ValueError("Node.js 20.9 ou superior necessário.")
    database = (
        Path("/data/eletroprojeto.db") if args.container else database_path(ROOT, args.data_dir)
    )
    database.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    env = {
        **os.environ,
        "DATABASE_URL": "sqlite:///" + database.resolve().as_posix(),
        "AUTH_MODE": "local",
        "CORS_ORIGINS": f"http://localhost:{args.port},http://127.0.0.1:{args.port}",
        "NEXT_PUBLIC_API_URL": "/api/v1",
        "NEXT_PUBLIC_AUTH_MODE": "local",
        "API_PROXY_TARGET": f"http://127.0.0.1:{args.api_port}",
        "NEXT_TELEMETRY_DISABLED": "1",
    }
    if args.container:
        python = Path(sys.executable)
        migrate(python, backend, database, env)
        env.update(HOSTNAME="0.0.0.0", PORT=str(args.port))
        serve(
            python,
            node,
            backend,
            [ROOT / "web" / "server.js"],
            env,
            args.api_port,
            args.port,
            False,
        )
        return
    candidates = [
        backend / name / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        for name in (".venv", ".venv-windows")
    ]
    python = next((path for path in candidates if path.is_file()), candidates[0])
    if not python_ready(python, backend):
        if not args.setup:
            raise ValueError("Dependências Python não preparadas. Execute novamente com --setup.")
        if not python.exists():
            run([sys.executable, "-m", "venv", python.parents[1]], ROOT, env)
        run([python, "-m", "pip", "install", "-r", backend / "requirements.lock"], ROOT, env)
    if not node_ready(frontend):
        if not args.setup:
            raise ValueError("Dependências frontend não preparadas. Execute novamente com --setup.")
        npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
        if not npm:
            raise ValueError("npm não encontrado; confira a instalação do Node.js.")
        run([npm, "ci"], frontend, env)
    env["NEXT_DIST_DIR"] = ".next/local"
    env["NEXT_OUTPUT_STANDALONE"] = "0"
    signature = fingerprint(frontend, env["API_PROXY_TARGET"])
    marker = frontend / ".next/local/eletroprojeto-build.json"
    cached = json.loads(marker.read_text()) if marker.exists() else {}
    if cached.get("signature") != signature or not (marker.parent / "BUILD_ID").exists():
        run(
            [node, frontend / "node_modules/next/dist/bin/next", "build", "--webpack"],
            frontend,
            env,
        )
        marker.write_text(json.dumps({"signature": fingerprint(frontend, env["API_PROXY_TARGET"])}))
    migrate(python, backend, database, env)
    if not args.prepare_only:
        serve(
            python,
            node,
            backend,
            [
                frontend / "node_modules/next/dist/bin/next",
                "start",
                "--hostname",
                "127.0.0.1",
                "--port",
                str(args.port),
            ],
            env,
            args.api_port,
            args.port,
            not args.no_browser,
        )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Não foi possível iniciar: {error}", file=sys.stderr)
        raise SystemExit(1) from None
