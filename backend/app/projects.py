"""Project snapshots and history shared by REST operations."""

from datetime import timezone
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .calculations.engine import calculate
from .database import HistoryRow, ProjectRow, TechnicalRevisionRow, utcnow
from .schemas import CalculationInput, CalculationResult, Project, ProjectInput
from .technical import registry_version, snapshot


def find(session: Session, project_id: UUID):
    row = session.get(ProjectRow, str(project_id))
    if row is None or row.deleted_at is not None:
        raise HTTPException(404, "Projeto não encontrado")
    return row


def brasilia_time(value):
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return aware.astimezone(ZoneInfo("America/Sao_Paulo"))


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
                review_status="normative_rules_pending",
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
