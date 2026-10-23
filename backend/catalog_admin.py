"""Publish a reviewed catalog or show its current persisted revision."""

import argparse
import json
from pathlib import Path

from app.catalog_store import initialize_catalog, publish
from app.database import SessionLocal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["status", "publish-reviewed"])
    parser.add_argument("--file", type=Path)
    args = parser.parse_args()
    if args.command == "status":
        print(initialize_catalog())
    else:
        if args.file is None:
            parser.error("--file deve conter o catálogo completo já revisado, com fontes e datas.")
        items = json.loads(args.file.read_text(encoding="utf-8"))
        with SessionLocal() as session:
            print(publish(session, items))
        print(
            "Revisão publicada. Reinicie todos os workers; instâncias dos projetos não foram alteradas."
        )


if __name__ == "__main__":
    main()
