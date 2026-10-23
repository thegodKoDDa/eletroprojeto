"""Persist published catalog revisions independently from project snapshots.

Publication is an explicit local administrative action. A running worker loads
one immutable revision; restart all workers together after publication.
"""

import hashlib
import json
from copy import deepcopy

from .catalog import CATALOG
from .database import CatalogRevisionRow, CatalogStateRow, SessionLocal, utcnow
from .schemas import CatalogItem


def publish(session, items):
    validated = [CatalogItem.model_validate(item).model_dump(mode="json") for item in items]
    ids = [item["id"] for item in validated]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Catálogo vazio ou IDs duplicados.")
    digest = hashlib.sha256(
        json.dumps(validated, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if session.get(CatalogRevisionRow, digest) is None:
        session.add(CatalogRevisionRow(id=digest, payload=validated, created_at=utcnow()))
        session.flush()
    state = session.get(CatalogStateRow, 1)
    if state is None:
        session.add(CatalogStateRow(id=1, revision_id=digest))
    else:
        state.revision_id = digest
    session.commit()
    return digest


def initialize_catalog(sessions=SessionLocal):
    with sessions() as session:
        state = session.get(CatalogStateRow, 1)
        if state is None:
            publish(session, CATALOG)
            state = session.get(CatalogStateRow, 1)
        revision = session.get(CatalogRevisionRow, state.revision_id)
        if revision is None:
            raise RuntimeError("Revisão de catálogo ausente.")
        # The shared list is updated in place so technical registry hashing and
        # every equipment endpoint use the same published revision.
        loaded = [
            CatalogItem.model_validate(item).model_dump(mode="json") for item in revision.payload
        ]
        CATALOG[:] = deepcopy(loaded)
        return revision.id
