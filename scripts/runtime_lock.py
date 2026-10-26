"""Derive the Linux/Python3.14 runtime subset without resolving new versions."""

import argparse
import sys
import tomllib
from importlib.metadata import requires
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


def generate():
    if sys.platform != "linux" or sys.version_info[:2] != (3, 14):
        raise ValueError("Geração destinada ao ambiente Linux/Python3.14 da imagem Docker.")
    project = tomllib.loads((ROOT / "backend/pyproject.toml").read_text())
    queue = [Requirement(value) for value in project["project"]["dependencies"]]
    visited = set()
    names = set()
    while queue:
        requirement = queue.pop()
        if requirement.marker and not requirement.marker.evaluate():
            continue
        key = (requirement.name.lower().replace("_", "-"), tuple(sorted(requirement.extras)))
        if key in visited:
            continue
        visited.add(key)
        names.add(key[0])
        for value in requires(requirement.name) or []:
            child = Requirement(value)
            if not child.marker or any(
                child.marker.evaluate({"extra": extra}) for extra in ("", *requirement.extras)
            ):
                child.marker = None
                queue.append(child)
    result = []
    for line in (ROOT / "backend/requirements.lock").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            requirement = Requirement(line)
            if requirement.name.lower().replace("_", "-") in names:
                result.append(line)
                names.remove(requirement.name.lower().replace("_", "-"))
    if names:
        raise ValueError(
            "Dependência runtime ausente do lock revisado: " + ", ".join(sorted(names))
        )
    return (
        "# Subconjunto runtime Linux/Python3.14; versões de requirements.lock.\n"
        + "\n".join(result)
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "backend/requirements-runtime.lock"
    result = generate()
    if args.check:
        if target.read_text() != result:
            raise SystemExit("Lock runtime desatualizado.")
    else:
        target.write_text(result)


if __name__ == "__main__":
    main()
