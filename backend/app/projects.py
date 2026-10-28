"""Project snapshots and history shared by REST operations."""

from datetime import timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .calculations.engine import calculate
from .database import HistoryRow, ProjectRow, TechnicalRevisionRow, utcnow
from .estimate_metadata import revision as registry_version
from .estimate_metadata import snapshot
from .schemas import CalculationInput, CalculationResult, Project, ProjectInput


def find(session: Session, project_id: UUID):
    row = session.get(ProjectRow, str(project_id))
    if row is None or row.deleted_at is not None:
        raise HTTPException(404, "Projeto não encontrado")
    return row


def brasilia_time(value):
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return aware.astimezone(ZoneInfo("America/Sao_Paulo"))


def latest_history(session: Session, project_id: str):
    """Stable ordering also covers histories written at the same instant."""
    return session.scalar(
        select(HistoryRow)
        .where(HistoryRow.project_id == project_id)
        .order_by(HistoryRow.project_version.desc(), HistoryRow.created_at.desc())
        .limit(1)
    )


def view(row: ProjectRow) -> Project:
    return Project(
        **row.payload,
        id=row.id,
        version=row.version,
        created_at=brasilia_time(row.created_at),
        updated_at=brasilia_time(row.updated_at),
        standards_version=row.standards_version,
        deleted_at=brasilia_time(row.deleted_at) if row.deleted_at else None,
    )


class ProjectValidationError(HTTPException):
    def __init__(self, issues):
        super().__init__(
            422,
            detail=[
                {"loc": ["body", issue["path"]], "msg": issue["message"], "type": "value_error"}
                for issue in issues
            ],
        )
        self.notifications = [
            dict(
                id=issue["path"],
                category="error",
                location=issue["location"],
                problem=issue["message"],
                solution=issue["solution"],
                affected_results=issue["affected_results"],
                target_id=issue["target_id"],
            )
            for issue in issues
        ]


def reject_invalid_draft(data: ProjectInput):
    from .validation import field_issues

    invalid = [
        issue
        for issue in field_issues(data.model_dump(mode="json"))
        if issue["status"] == "invalid"
    ]
    if invalid:
        raise ProjectValidationError(invalid)


def record(session: Session, row: ProjectRow):
    version = registry_version()
    if session.get(TechnicalRevisionRow, version) is None:
        session.add(
            TechnicalRevisionRow(
                id=version,
                payload=snapshot(),
                created_at=utcnow(),
                review_status="estimate_revision",
            )
        )
        session.flush()
    result = CalculationResult.model_validate(
        calculate(CalculationInput.model_validate(row.payload).model_dump(mode="json"))
    )
    session.add(
        HistoryRow(
            id=str(uuid4()),
            project_id=row.id,
            project_version=row.version,
            inputs=row.payload,
            result=result.model_dump(mode="json"),
            created_at=utcnow(),
        )
    )


def same_input(payload: dict, data: ProjectInput) -> bool:
    """Compare normalized snapshots, retaining generated IDs omitted by API clients.

    Explicit IDs always participate. Positional alignment is only for comparison;
    it never mutates input models or the persisted snapshot.
    """
    previous = ProjectInput.model_validate(payload).model_dump(mode="json")
    incoming = data.model_dump(mode="json")
    for index, room in enumerate(data.environments):
        if index >= len(previous["environments"]):
            break
        old_room = previous["environments"][index]
        current = incoming["environments"][index]
        if "id" not in room.model_fields_set:
            current["id"] = old_room["id"]
        for position, load in enumerate(room.loads):
            if position >= len(old_room["loads"]):
                break
            if "id" not in load.model_fields_set:
                current["loads"][position]["id"] = old_room["loads"][position]["id"]
    for index, circuit in enumerate(data.circuits):
        if index < len(previous["circuits"]) and "id" not in circuit:
            incoming["circuits"][index]["id"] = previous["circuits"][index]["id"]
    return previous == incoming


def listing_query(*, archived: bool, q: str, sort: str):
    """One owner-scoped ORM query for full and summary lists on SQLite/PostgreSQL."""
    query = select(ProjectRow).where(
        ProjectRow.deleted_at.is_not(None) if archived else ProjectRow.deleted_at.is_(None)
    )
    if q.strip():
        escaped = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            or_(
                *(
                    ProjectRow.payload[key].as_string().ilike(f"%{escaped}%", escape="\\")
                    for key in ("name", "municipality")
                )
            )
        )
    order = (
        (ProjectRow.payload["name"].as_string().asc(), ProjectRow.id.asc())
        if sort == "name"
        else (ProjectRow.updated_at.desc(), ProjectRow.id.asc())
    )
    return query.order_by(*order)
