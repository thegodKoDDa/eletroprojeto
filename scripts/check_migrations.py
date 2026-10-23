"""Verify migrations against a disposable SQLite or explicitly supplied QA PostgreSQL.

The normal application database is never selected. PostgreSQL is selected only
through TEST_DATABASE_URL, which must name a dedicated QA database.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="eletroprojeto-migrations-") as folder:
        url = os.environ.get("TEST_DATABASE_URL")
        if url and not url.startswith("postgresql+psycopg://"):
            raise ValueError("TEST_DATABASE_URL deve ser PostgreSQL QA com psycopg.")
        environment = {
            **os.environ,
            "DATABASE_URL": url or f"sqlite:///{Path(folder, 'qa.db').as_posix()}",
        }
        for args in [("upgrade", "head"), ("check",)]:
            subprocess.run(
                [sys.executable, "-m", "alembic", *args],
                cwd=root / "backend",
                env=environment,
                check=True,
            )
    print("Migrações verificadas em banco QA; SQLite da aplicação preservado.")


if __name__ == "__main__":
    main()
