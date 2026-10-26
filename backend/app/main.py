import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from .auth import authenticate_request
from .auth import router as auth_router
from .calculations.energisa import calculate_energisa_demand
from .calculations.engine import ENGINE_VERSION, calculate
from .calculations.standards import ENERGISA_V7_EVIDENCE, RULES
from .catalog import CATALOG
from .catalog_store import initialize_catalog
from .database import HistoryRow, ProjectRow, TechnicalRevisionRow, get_session, utcnow
from .knowledge import router as knowledge_router
from .projects import (
    ProjectValidationError,
    brasilia_time,
    find,
    latest_history,
    listing_query,
    record,
    reject_invalid_draft,
    same_input,
    view,
)
from .schemas import (
    CalculationInput,
    CalculationResult,
    CatalogItem,
    DocumentRegistry,
    EnergisaDemandInput,
    EnergisaDemandResult,
    FieldRequirement,
    HealthInfo,
    InputValidationError,
    PDFExportInput,
    Project,
    ProjectInput,
    ProjectRevalidation,
    ProjectSummary,
    TechnicalRules,
    TerritoryLookup,
    UtilityInfo,
)
from .security import RequestBoundary, cors_origins
from .technical import (
    DOCUMENTS,
    MATHEMATICAL_RULES,
    REGIONAL_METHODS,
    STATES,
    UTILITIES,
    applicability,
    integrity,
    normative_capabilities,
    registry_version,
)
from .territory import lookup as territory_lookup
from .version import APP_VERSION


@asynccontextmanager
async def lifespan(app):
    initialize_catalog()
    yield


app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(authenticate_request)],
    responses={
        422: {
            "model": InputValidationError,
            "description": "Entradas inválidas; avisos localizados quando disponíveis.",
        }
    },
    separate_input_output_schemas=False,
    title="EletroProjeto",
    version=APP_VERSION,
    description="Cálculos de cargas residenciais: potência instalada (W/kW), potência aparente (VA/kVA), correntes, conversões, consumo mensal e estimativa de custo pela tarifa informada. Valores padrão são sugestões documentadas; valores manuais válidos são respeitados e recalculados. Previsão residencial de iluminação e TUG disponível por seleção explícita, com escopo e limites documentados. Demanda Energisa residencial parametrizada disponível em escopo limitado e inventário explícito. Demanda automática do cadastro e dimensionamento final permanecem pendentes.",
)
app.include_router(auth_router)
app.include_router(knowledge_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    ),
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "If-Match", "X-CSRF-Token", "Idempotency-Key"],
    allow_credentials=True,
)
app.add_middleware(RequestBoundary)
PREFIX = "/api/v1"


@app.get(PREFIX + "/health", tags=["Estado e versão"], response_model=HealthInfo)
def health():
    return {
        "status": "ok",
        "app_version": APP_VERSION,
        "api_version": APP_VERSION,
        "engine_version": ENGINE_VERSION,
    }


@app.get(PREFIX + "/projects", tags=["Projetos"], response_model=list[Project])
def projects(
    archived: bool = False,
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str = Query(default="", max_length=200),
    sort: Literal["recent", "name"] = "recent",
    session: Session = Depends(get_session),
):
    statement = listing_query(archived=archived, q=q, sort=sort).offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    return [view(row) for row in session.scalars(statement)]


@app.get(PREFIX + "/projects/summaries", tags=["Projetos"], response_model=list[ProjectSummary])
def project_summaries(
    archived: bool = False,
    limit: int = Query(default=21, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str = Query(default="", max_length=200),
    sort: Literal["recent", "name"] = "recent",
    session: Session = Depends(get_session),
):
    columns = [
        ProjectRow.id,
        ProjectRow.version,
        ProjectRow.created_at,
        ProjectRow.updated_at,
        ProjectRow.deleted_at,
        ProjectRow.standards_version,
        *(
            ProjectRow.payload[key].as_string().label(key)
            for key in ("name", "municipality", "state", "utility")
        ),
    ]
    statement = (
        listing_query(archived=archived, q=q, sort=sort)
        .with_only_columns(*columns)
        .offset(offset)
        .limit(limit)
    )
    rows = session.execute(statement).mappings()
    return [
        {
            **row,
            "state": row["state"] or "SP",
            "utility": row["utility"] or "unconfirmed",
            "created_at": brasilia_time(row["created_at"]),
            "updated_at": brasilia_time(row["updated_at"]),
            "deleted_at": brasilia_time(row["deleted_at"]) if row["deleted_at"] else None,
        }
        for row in rows
    ]


@app.post(PREFIX + "/projects", tags=["Projetos"], response_model=Project, status_code=201)
def create(
    data: ProjectInput,
    session: Session = Depends(get_session),
    idempotency_key: Annotated[UUID | None, Header()] = None,
):
    reject_invalid_draft(data)
    if idempotency_key:
        previous = session.get(ProjectRow, str(idempotency_key))
        if previous is not None:
            if previous.deleted_at is None and same_input(previous.payload, data):
                return view(previous)
            raise HTTPException(
                409,
                "Primeiro salvamento já recebido. Reabra o projeto antes de reenviar alterações.",
            )
    now = utcnow()
    row = ProjectRow(
        id=str(idempotency_key or uuid4()),
        payload=data.model_dump(mode="json"),
        created_at=now,
        updated_at=now,
        standards_version=registry_version(),
    )
    session.add(row)
    try:
        session.flush()
        record(session, row)
        session.commit()
    except IntegrityError:
        session.rollback()
        if not idempotency_key:
            raise
        # Only a collision on this key is a retry; unrelated integrity failures propagate.
        if (
            session.scalar(
                select(ProjectRow.__table__.c.id).where(
                    ProjectRow.__table__.c.id == str(idempotency_key)
                )
            )
            is None
        ):
            raise
        # Concurrent identical attempts converge to the same owner-scoped project.
        previous = session.get(ProjectRow, str(idempotency_key))
        if (
            previous is not None
            and previous.deleted_at is None
            and same_input(previous.payload, data)
        ):
            return view(previous)
        raise HTTPException(
            409, "Identificador de salvamento já utilizado; confira a versão salva."
        )
    return view(row)


@app.get(PREFIX + "/projects/{project_id}", tags=["Projetos"], response_model=Project)
def read(project_id: UUID, session: Session = Depends(get_session)):
    return view(find(session, project_id))


@app.put(PREFIX + "/projects/{project_id}", tags=["Projetos"], response_model=Project)
def update(
    project_id: UUID,
    data: ProjectInput,
    expected_version: int,
    session: Session = Depends(get_session),
):
    row = find(session, project_id)
    if row.version != expected_version:
        raise HTTPException(409, "Projeto alterado em outra sessão. Recarregue antes de salvar.")
    reject_invalid_draft(data)
    payload = data.model_dump(mode="json")
    version = registry_version()
    if row.standards_version == version and same_input(row.payload, data):
        return view(row)
    row.standards_version = version
    row.payload = payload
    row.updated_at = utcnow()
    try:
        session.flush()
        record(session, row)
        session.commit()
    except StaleDataError:
        session.rollback()
        raise HTTPException(409, "Conflito de versão ao salvar")
    return view(row)


@app.delete(PREFIX + "/projects/{project_id}", tags=["Projetos"], status_code=204)
def remove(
    project_id: UUID,
    expected_version: int | None = Query(default=None, ge=1),
    session: Session = Depends(get_session),
):
    row = find(session, project_id)
    if expected_version is not None and row.version != expected_version:
        raise HTTPException(409, "Projeto alterado. Atualize a lista antes de excluir.")
    row.deleted_at = utcnow()
    row.updated_at = row.deleted_at
    try:
        session.commit()
    except StaleDataError:
        session.rollback()
        raise HTTPException(409, "Conflito de versão ao excluir")
    return Response(status_code=204)


@app.post(PREFIX + "/projects/{project_id}/restore", tags=["Projetos"], response_model=Project)
def restore(
    project_id: UUID, expected_version: int = Query(ge=1), session: Session = Depends(get_session)
):
    row = session.get(ProjectRow, str(project_id))
    if row is None or row.deleted_at is None:
        raise HTTPException(404, "Projeto excluído não encontrado")
    if row.version != expected_version:
        raise HTTPException(409, "Projeto alterado. Atualize a lista antes de restaurar.")
    row.deleted_at = None
    row.updated_at = utcnow()
    try:
        session.commit()
    except StaleDataError:
        session.rollback()
        raise HTTPException(409, "Conflito de versão ao restaurar")
    return view(row)


@app.delete(PREFIX + "/projects/{project_id}/permanent", tags=["Projetos"], status_code=204)
def permanently_remove(
    project_id: UUID, expected_version: int = Query(ge=1), session: Session = Depends(get_session)
):
    row = session.get(ProjectRow, str(project_id))
    if row is None:
        raise HTTPException(404, "Projeto excluído não encontrado")
    if row.deleted_at is None:
        raise HTTPException(409, "Envie o projeto para a lixeira antes de excluir definitivamente.")
    if row.version != expected_version:
        raise HTTPException(
            409, "Projeto alterado. Atualize a lixeira antes de excluir definitivamente."
        )
    try:
        session.delete(row)  # FK cascade removes only this project's history, atomically.
        session.commit()
    except StaleDataError:
        session.rollback()
        raise HTTPException(409, "Conflito de versão ao excluir definitivamente")
    return Response(status_code=204)


@app.post(PREFIX + "/calculations/loads", tags=["Cálculos"], response_model=CalculationResult)
@app.post(PREFIX + "/calculations/demand", tags=["Cálculos"], response_model=CalculationResult)
@app.post(PREFIX + "/calculations/full", tags=["Cálculos"], response_model=CalculationResult)
def full(data: CalculationInput):
    return calculate(data.model_dump(mode="json"))


@app.post(
    PREFIX + "/calculations/energisa-demand", tags=["Cálculos"], response_model=EnergisaDemandResult
)
def energisa_demand(data: EnergisaDemandInput):
    """NDU-001 v7 residencial individual d1–d7, inventário explícito; sem dimensionamento final."""
    result = calculate_energisa_demand(data.model_dump(mode="json"))
    return {**result, "reference": asdict(ENERGISA_V7_EVIDENCE)}


@app.get(PREFIX + "/equipment", tags=["Equipamentos"], response_model=list[CatalogItem])
def equipment(q: str = Query(default="", max_length=200), category: str | None = None):
    return [
        item
        for item in CATALOG
        if (
            not q
            or q.casefold() in (item.get("selection_name", "") + " " + item["name"]).casefold()
        )
        and (category is None or item["category"] == category)
    ]


@app.get(PREFIX + "/utilities", tags=["Localização"], response_model=list[UtilityInfo])
def utilities(
    state: str | None = Query(default=None, pattern="^[A-Z]{2}$"),
    municipality: str | None = Query(default=None, max_length=200),
):
    # Municipality deliberately does not narrow unverified state candidates.
    return [item for item in UTILITIES if state is None or state in item["states"]]


@app.get(PREFIX + "/locations/territory", tags=["Localização"], response_model=TerritoryLookup)
def territory(
    latitude: Annotated[
        Decimal,
        Query(
            ge=-90,
            le=90,
            allow_inf_nan=False,
            max_digits=18,
            decimal_places=12,
            description="Latitude SIRGAS2000 (EPSG4674); sem reprojeção automática.",
        ),
    ],
    longitude: Annotated[
        Decimal,
        Query(
            ge=-180,
            le=180,
            allow_inf_nan=False,
            max_digits=18,
            decimal_places=12,
            description="Longitude SIRGAS2000 (EPSG4674).",
        ),
    ],
):
    return territory_lookup(latitude, longitude)


@app.get(PREFIX + "/standards", tags=["Referências técnicas"])
def standards():
    return [asdict(rule) for rule in RULES]


@app.get(PREFIX + "/projects/{project_id}/report", tags=["Projetos"])
def report(project_id: UUID, session: Session = Depends(get_session)):
    row = find(session, project_id)
    latest = latest_history(session, row.id)
    return {
        "project": view(row),
        "calculation": CalculationResult.model_validate(
            calculate(CalculationInput.model_validate(row.payload).model_dump(mode="json"))
        ),
        "calculation_basis": "current_registry_preview",
        "recorded_registry_version": row.standards_version,
        "current_registry_version": registry_version(),
        "recorded_calculation": latest.result if latest else None,
        "notice": "Documento parcial. Não substitui revisão e responsabilidade técnica profissional.",
    }


@app.get(PREFIX + "/projects/{project_id}/history", tags=["Projetos"])
def history(project_id: UUID, session: Session = Depends(get_session)):
    find(session, project_id)
    rows = session.scalars(
        select(HistoryRow)
        .where(HistoryRow.project_id == str(project_id))
        .order_by(HistoryRow.project_version.desc(), HistoryRow.created_at.desc())
    )
    return [
        {
            "id": row.id,
            "version": row.project_version,
            "created_at": brasilia_time(row.created_at),
            "inputs": row.inputs,
            "result": row.result,
        }
        for row in rows
    ]


@app.get(PREFIX + "/locations/states", tags=["Localização"], response_model=list[str])
def states():
    return STATES


@app.get(
    PREFIX + "/technical/documents", tags=["Referências técnicas"], response_model=DocumentRegistry
)
def documents():
    return {"registry_version": registry_version(), "documents": DOCUMENTS}


@app.get(PREFIX + "/technical/applicability", tags=["Referências técnicas"])
def applicable(utility: str, state: str = Query(default="SP", pattern="^[A-Z]{2}$")):
    return applicability(utility, state)


@app.get(PREFIX + "/technical/integrity", tags=["Referências técnicas"])
def validate_registry():
    return integrity()


@app.get(PREFIX + "/technical/revisions", tags=["Referências técnicas"])
def revisions(session: Session = Depends(get_session)):
    rows = session.scalars(
        select(TechnicalRevisionRow).order_by(TechnicalRevisionRow.created_at.desc())
    )
    return [
        {"id": row.id, "created_at": brasilia_time(row.created_at), "status": row.review_status}
        for row in rows
    ]


@app.get(PREFIX + "/technical/revisions/{revision_id}", tags=["Referências técnicas"])
def revision(revision_id: str, session: Session = Depends(get_session)):
    row = session.get(TechnicalRevisionRow, revision_id)
    if row is None:
        raise HTTPException(404, "Versão técnica não encontrada")
    return {"id": row.id, "snapshot": row.payload, "status": row.review_status}


@app.get(
    PREFIX + "/projects/{project_id}/revalidation",
    tags=["Projetos"],
    response_model=ProjectRevalidation,
)
def revalidation(project_id: UUID, session: Session = Depends(get_session)):
    row = find(session, project_id)
    current = registry_version()
    latest = latest_history(session, row.id)
    return {
        "project_id": row.id,
        "project_version": row.version,
        "previous_engine_version": latest.result.get("engine_version") if latest else None,
        "previous_registry_version": row.standards_version,
        "current_registry_version": current,
        "requires_revalidation": row.standards_version != current
        or (latest is not None and latest.result.get("engine_version") != ENGINE_VERSION),
        "previous_result": latest.result if latest else None,
        "current_result": CalculationResult.model_validate(
            calculate(CalculationInput.model_validate(row.payload).model_dump(mode="json"))
        ),
        "notice": "Comparação conservadora. Valores manuais e histórico permanecem preservados.",
    }


@app.post(PREFIX + "/projects/{project_id}/recalculate", tags=["Projetos"], response_model=Project)
def recalculate(
    project_id: UUID, expected_version: int = Query(ge=1), session: Session = Depends(get_session)
):
    row = find(session, project_id)
    if row.version != expected_version:
        raise HTTPException(409, "Projeto alterado; recarregue antes de recalcular")
    row.updated_at = utcnow()
    row.standards_version = registry_version()
    try:
        session.flush()
        record(session, row)
        session.commit()
    except StaleDataError:
        session.rollback()
        raise HTTPException(409, "Conflito de versão ao recalcular")
    return view(row)


@app.post(
    PREFIX + "/projects/{project_id}/duplicate",
    tags=["Projetos"],
    response_model=Project,
    status_code=201,
)
def duplicate(project_id: UUID, session: Session = Depends(get_session)):
    original = find(session, project_id)
    payload = dict(original.payload)
    payload["name"] = payload["name"][:190] + " · cópia"
    return create(ProjectInput.model_validate(payload), session)


@app.get(PREFIX + "/technical/rules", tags=["Referências técnicas"], response_model=TechnicalRules)
def computational_rules(
    utility: str = Query(default="unconfirmed", max_length=100),
    state: str = Query(default="SP", pattern="^[A-Z]{2}$"),
):
    return {
        "registry_version": registry_version(),
        "coverage": normative_capabilities(utility, state),
        "mathematical": MATHEMATICAL_RULES,
        "normative": [asdict(rule) for rule in RULES],
        "regional_methods": [
            method
            for method in REGIONAL_METHODS
            if utility == "unconfirmed"
            or (utility in method["supported_utilities"] and state in method["supported_states"])
        ],
        "notice": "Validação matemática não implica conformidade normativa.",
    }


@app.get(PREFIX + "/equipment/{equipment_id}", tags=["Equipamentos"], response_model=CatalogItem)
def equipment_reference(equipment_id: str):
    item = next((item for item in CATALOG if item["id"] == equipment_id), None)
    if item is None:
        raise HTTPException(404, "Referência de equipamento não encontrada")
    return item


@app.get(
    PREFIX + "/validation/requirements",
    tags=["Validação"],
    response_model=dict[str, FieldRequirement],
)
def validation_requirements():
    from .validation import requirements

    return requirements()


@app.post(
    PREFIX + "/reports/pdf",
    tags=["Relatórios"],
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
            "description": "Relatório parcial das entradas enviadas e recalculadas no backend",
        }
    },
)
def export_pdf(data: PDFExportInput, session: Session = Depends(get_session)):
    from .reports.pdf import render_report

    project, result, version = prepare_report(data, session)
    return Response(
        render_report(project, result, project_version=version),
        media_type="application/pdf",
        headers={
            "Content-Disposition": report_disposition(project["name"], "pdf"),
        },
    )


def prepare_report(data: PDFExportInput, session: Session):
    project = data.project.model_dump(mode="json")
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    if (
        result["input_digest"] != data.expected_input_digest
        or result["engine_version"] != data.expected_engine_version
        or result["technical_context"]["registry_version"] != data.expected_registry_version
    ):
        raise HTTPException(
            409, "Entradas, motor ou referências alterados. Aguarde novo cálculo antes de exportar."
        )
    version = None
    if data.saved_project_id is not None:
        row = find(session, data.saved_project_id)
        if (
            row.version != data.saved_project_version
            or ProjectInput.model_validate(row.payload).model_dump(mode="json") != project
        ):
            raise HTTPException(
                409,
                "Projeto salvo diverge desta exportação. Salve novamente ou exporte como rascunho.",
            )
        version = row.version
    elif data.saved_project_version is not None:
        raise HTTPException(422, "Identificador do projeto salvo ausente")
    return project, result, version


def report_disposition(project_name: str, extension: str):
    import re
    from urllib.parse import quote

    name = (
        re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]', "_", project_name or "").strip(" .")[:120]
        or "Projeto sem nome"
    )
    return f"attachment; filename=projeto.{extension}; filename*=UTF-8''{quote(name + '.' + extension, safe='')}"


@app.post(PREFIX + "/reports/json", tags=["Relatórios"])
def export_json(data: PDFExportInput, session: Session = Depends(get_session)):
    import json

    from .reports.summary import build_summary

    project, result, version = prepare_report(data, session)
    return Response(
        json.dumps(
            build_summary(project, result, project_version=version), ensure_ascii=False, indent=2
        )
        + "\n",
        media_type="application/json",
        headers={
            "Content-Disposition": report_disposition(project["name"], "json"),
        },
    )


@app.exception_handler(RequestValidationError)
async def invalid_inputs(request, exc: RequestValidationError):
    from .validation import input_error_notifications

    # Omit raw inputs/validator contexts: diagnostics must not echo sensitive data.
    errors = [{key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()]
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"detail": errors, "notifications": input_error_notifications(errors, exc.body)}
        ),
    )


@app.exception_handler(ProjectValidationError)
async def invalid_project(request, exc: ProjectValidationError):
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.detail, "notifications": exc.notifications}),
    )
