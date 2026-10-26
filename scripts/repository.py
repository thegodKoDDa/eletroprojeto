"""Bounded Git synchronization with the existing public GitHub repository only."""

import json
import os
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOSITORY = "thegodKoDDa/eletroprojeto"
REMOTES = {
    f"https://github.com/{REPOSITORY}.git",
    f"https://github.com/{REPOSITORY}",
    f"git@github.com:{REPOSITORY}.git",
}


def git(root, *args, timeout=30):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"},
    )


def status(root, *, refresh=False):
    """Fetch known origin when requested; never change the worktree or merge."""
    try:
        remote = git(root, "remote", "get-url", "origin")
        if remote.returncode or remote.stdout.strip() not in REMOTES:
            return {"configured": False, "reason": "Sem origin GitHub autorizado."}
        result = {"configured": True, "repository": REPOSITORY, "refreshed": False}
        if refresh:
            fetched = git(root, "fetch", "--no-tags", "origin")
            result["refreshed"] = fetched.returncode == 0
            if fetched.returncode:
                result["reason"] = "Não foi possível consultar o remoto; estado local preservado."
        branch = git(root, "branch", "--show-current").stdout.strip()
        result["branch"] = branch
        counts = git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main")
        if counts.returncode == 0:
            result["ahead"], result["behind"] = map(int, counts.stdout.split())
        return result
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {"configured": False, "reason": "Consulta Git indisponível; use os dados locais."}


def public_origin(root):
    """Confirm destination/visibility without persisting or printing credentials."""
    remote = git(root, "remote", "get-url", "origin")
    if remote.returncode or remote.stdout.strip() not in REMOTES:
        raise ValueError("Envio permitido apenas para o origin GitHub já autorizado.")
    request = Request(
        f"https://api.github.com/repos/{REPOSITORY}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "EletroProjeto-continuity",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            repository = json.load(response)
    except (HTTPError, URLError, OSError) as error:
        raise ValueError(
            "Não foi possível confirmar a visibilidade pública do GitHub; envio suspenso."
        ) from error
    if (
        repository.get("full_name", "").lower() != REPOSITORY.lower()
        or repository.get("private") is not False
    ):
        raise ValueError("Destino não confirmado como o repositório público autorizado.")


def synchronize(root):
    """Push reviewed commits only; refusal/offline never destroys local progress."""
    try:
        if git(root, "branch", "--show-current").stdout.strip() != "main":
            raise ValueError("Sincronização automática exige a branch main.")
        worktree = git(root, "status", "--porcelain", "--untracked-files=all")
        if worktree.returncode or worktree.stdout.strip():
            raise ValueError(
                "Revise e faça o commit local antes de sincronizar; nenhum arquivo é adicionado automaticamente."
            )
        public_origin(root)
        remote = status(root, refresh=True)
        if not remote.get("refreshed"):
            raise ValueError("Consulta ao GitHub falhou; nenhum envio realizado.")
        if remote.get("behind", 1):
            raise ValueError(
                "Há commits remotos a revisar; não há merge, reset ou force-push automático."
            )
        head = git(root, "rev-parse", "HEAD").stdout.strip()
        if remote.get("ahead"):
            pushed = git(root, "push", "--set-upstream", "origin", "main", timeout=60)
            if pushed.returncode:
                raise ValueError("Push recusado ou sem conexão; commit local preservado.")
        actual = git(root, "ls-remote", "--exit-code", "origin", "refs/heads/main")
        if (
            actual.returncode
            or actual.stdout.split()[0] != head
            or git(root, "rev-parse", "HEAD").stdout.strip() != head
        ):
            raise ValueError("Não foi possível confirmar o mesmo commit local e remoto.")
        return {"ok": True, "repository": REPOSITORY, "private": False, "commit": head}
    except (OSError, subprocess.TimeoutExpired):
        return {
            "ok": False,
            "reason": "Git/rede indisponível ou tempo excedido; trabalho local preservado.",
        }
    except ValueError as error:
        return {"ok": False, "reason": str(error)}
