"""Optional real PostgreSQL runs use a unique disposable schema per test.

TEST_DATABASE_URL must point at a dedicated QA database. The application SQLite
is never selected by this fixture; existing schemas are never dropped.
"""

import os
from uuid import uuid4

import pytest
from app.database import Base, make_engine
from sqlalchemy import text


@pytest.fixture
def database_engine(tmp_path):
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
        Base.metadata.create_all(engine)
        try:
            yield engine
        finally:
            engine.dispose()
        return
    if not url.startswith("postgresql+psycopg://"):
        pytest.fail("TEST_DATABASE_URL deve apontar para PostgreSQL QA com psycopg.")
    base = make_engine(url)
    schema = f"qa_{uuid4().hex}"
    with base.begin() as connection:
        connection.execute(text(f"CREATE SCHEMA {schema}"))
    engine = base.execution_options(schema_translate_map={None: schema})
    try:
        Base.metadata.create_all(engine)
        yield engine
    finally:
        with base.begin() as connection:
            connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        base.dispose()
