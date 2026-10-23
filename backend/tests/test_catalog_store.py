from copy import deepcopy

import pytest
from app.catalog import CATALOG
from app.catalog_store import initialize_catalog, publish
from app.database import CatalogRevisionRow, ProjectRow, utcnow
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker


def test_catalog_publication_is_versioned_and_never_edits_project_snapshots(database_engine):
    engine = database_engine
    sessions = sessionmaker(engine, expire_on_commit=False)
    original = deepcopy(CATALOG)
    try:
        first = initialize_catalog(sessions)
        with sessions() as session:
            session.add(
                ProjectRow(
                    id="preserved",
                    payload={"snapshot": original[0]},
                    created_at=utcnow(),
                    updated_at=utcnow(),
                )
            )
            session.commit()
            changed = deepcopy(original)
            changed[0]["note"] += " Revisão de teste."
            second = publish(session, changed)
            assert first != second
            assert publish(session, changed) == second
            assert len(list(session.scalars(select(CatalogRevisionRow)))) == 2
        assert initialize_catalog(sessions) == second
        with sessions() as session:
            assert session.get(ProjectRow, "preserved").payload["snapshot"] == original[0]
            assert (
                session.get(CatalogRevisionRow, first).payload
                != session.get(CatalogRevisionRow, second).payload
            )
            with pytest.raises(ValueError):
                publish(session, [original[0], original[0]])
    finally:
        CATALOG[:] = original
        engine.dispose()
