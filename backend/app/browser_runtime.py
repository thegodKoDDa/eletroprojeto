"""Pure-Python request dispatcher for static browser execution (Pyodide / GitHub Pages).

Executes the exact backend Pydantic schemas, validation rules, electrical calculation
engine, and PDF/JSON report generators without FastAPI or SQLAlchemy dependencies.
"""

import base64
import json
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, quote, urlsplit
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from pydantic import ValidationError

from .calculations.energisa import calculate_energisa_demand
from .calculations.engine import ENGINE_VERSION, calculate
from .calculations.standards import ENERGISA_V7_EVIDENCE, RULES
from .catalog import CATALOG
from .municipalities import lookup as municipality_lookup
from .reports.pdf import render_report
from .reports.summary import build_summary
from .schemas import (
    CalculationInput,
    CalculationResult,
    CatalogItem,
    DocumentRegistry,
    EnergisaDemandInput,
    EnergisaDemandResult,
    FieldRequirement,
    HealthInfo,
    MunicipalityLookup,
    PDFExportInput,
    Project,
    ProjectInput,
    ProjectRevalidation,
    ProjectSummary,
    TechnicalRules,
    TerritoryLookup,
    UtilityInfo,
)
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
    snapshot,
)
from .territory import lookup as territory_lookup
from .validation import field_issues, input_error_notifications, requirements
from .version import APP_VERSION

KNOWLEDGE_NOTICE = "Acervo de consulta. Importação não valida vigência, aplicabilidade territorial ou regras de cálculo."


class _HTTPError(Exception):
    def __init__(self, status: int, detail: Any, notifications: list[dict] | None = None):
        super().__init__(str(detail))
        self.status = status
        self.detail = detail
        self.notifications = notifications


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _brasilia_iso(value: str | datetime) -> str:
    dt = datetime.fromisoformat(value) if isinstance(value, str) else value
    aware = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    return aware.astimezone(ZoneInfo("America/Sao_Paulo")).isoformat()


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _same_input(payload: dict, data: ProjectInput) -> bool:
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
        if index < len(previous["circuits"]) and "id" not in circuit.model_fields_set:
            incoming["circuits"][index]["id"] = previous["circuits"][index]["id"]
    return previous == incoming


def _reject_invalid_draft(data: ProjectInput):
    invalid = [
        issue
        for issue in field_issues(data.model_dump(mode="json"))
        if issue["status"] == "invalid"
    ]
    if invalid:
        detail = [
            {"loc": ["body", issue["path"]], "msg": issue["message"], "type": "value_error"}
            for issue in invalid
        ]
        notifications = [
            dict(
                id=issue["path"],
                category="error",
                location=issue["location"],
                problem=issue["message"],
                solution=issue["solution"],
                affected_results=issue["affected_results"],
                target_id=issue["target_id"],
            )
            for issue in invalid
        ]
        raise _HTTPError(422, detail, notifications)


def _load_store(store_json: str | None) -> dict:
    if not store_json:
        return {"projects": {}, "history": [], "revisions": {}}
    data = json.loads(store_json)
    if not isinstance(data, dict):
        raise ValueError("Armazenamento local inválido.")
    return {
        "projects": dict(data.get("projects") or {}),
        "history": list(data.get("history") or []),
        "revisions": dict(data.get("revisions") or {}),
    }


def _view_project(row: dict) -> dict:
    return Project(
        **row["payload"],
        id=row["id"],
        version=row["version"],
        created_at=_brasilia_iso(row["created_at"]),
        updated_at=_brasilia_iso(row["updated_at"]),
        standards_version=row["standards_version"],
        deleted_at=_brasilia_iso(row["deleted_at"]) if row.get("deleted_at") else None,
    ).model_dump(mode="json")


def _find_active_project(store: dict, project_id: str) -> dict:
    try:
        key = str(UUID(str(project_id)))
    except ValueError as exc:
        raise _HTTPError(422, "Identificador de projeto inválido") from exc
    row = store["projects"].get(key)
    if row is None or row.get("deleted_at") is not None:
        raise _HTTPError(404, "Projeto não encontrado")
    return row


def _record_history(store: dict, row: dict):
    version = registry_version()
    if version not in store["revisions"]:
        store["revisions"][version] = {
            "id": version,
            "payload": snapshot(),
            "created_at": _utcnow_iso(),
            "review_status": "normative_rules_pending",
        }
    result = CalculationResult.model_validate(
        calculate(CalculationInput.model_validate(row["payload"]).model_dump(mode="json"))
    ).model_dump(mode="json")
    store["history"].append(
        {
            "id": str(uuid4()),
            "project_id": row["id"],
            "project_version": row["version"],
            "inputs": row["payload"],
            "result": result,
            "created_at": _utcnow_iso(),
        }
    )


def _latest_history(store: dict, project_id: str) -> dict | None:
    items = [item for item in store["history"] if item["project_id"] == project_id]
    if not items:
        return None
    items.sort(key=lambda item: (item["project_version"], item["created_at"]), reverse=True)
    return items[0]


def _filter_projects(store: dict, *, archived: bool, q: str, sort: str) -> list[dict]:
    needle = q.strip().casefold()
    rows = []
    for row in store["projects"].values():
        is_archived = row.get("deleted_at") is not None
        if is_archived != archived:
            continue
        if needle:
            name = str(row["payload"].get("name") or "").casefold()
            municipality = str(row["payload"].get("municipality") or "").casefold()
            if needle not in name and needle not in municipality:
                continue
        rows.append(row)
    if sort == "name":
        rows.sort(key=lambda r: (str(r["payload"].get("name") or ""), r["id"]))
    else:
        rows.sort(key=lambda r: r["id"])
        rows.sort(key=lambda r: r["updated_at"], reverse=True)
    return rows


def _report_disposition(project_name: str, extension: str) -> str:
    name = (
        re.sub(r'[\x00-\x1f\x7f/\\:*?"<>|]', "_", project_name or "").strip(" .")[:120]
        or "Projeto sem nome"
    )
    return f"attachment; filename=projeto.{extension}; filename*=UTF-8''{quote(name + '.' + extension, safe='')}"


def _prepare_report(data: PDFExportInput, store: dict):
    project = data.project.model_dump(mode="json")
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    if (
        result["input_digest"] != data.expected_input_digest
        or result["engine_version"] != data.expected_engine_version
        or result["technical_context"]["registry_version"] != data.expected_registry_version
    ):
        raise _HTTPError(
            409, "Entradas, motor ou referências alterados. Aguarde novo cálculo antes de exportar."
        )
    version = None
    if data.saved_project_id is not None:
        row = _find_active_project(store, str(data.saved_project_id))
        if (
            row["version"] != data.saved_project_version
            or ProjectInput.model_validate(row["payload"]).model_dump(mode="json") != project
        ):
            raise _HTTPError(
                409,
                "Projeto salvo diverge desta exportação. Salve novamente ou exporte como rascunho.",
            )
        version = row["version"]
    elif data.saved_project_version is not None:
        raise _HTTPError(422, "Identificador do projeto salvo ausente")
    return project, result, version


def _parse_json_body(raw_body: str | None) -> Any:
    if not raw_body:
        return {}
    try:
        return json.loads(raw_body)
    except ValueError as exc:
        raise _HTTPError(
            422,
            [{"loc": ["body"], "msg": "JSON inválido", "type": "json_invalid"}],
            [],
        ) from exc


def _validate_model(model_cls, payload: Any, loc_prefix: str = "body"):
    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        errors = [
            {
                "loc": [loc_prefix, *error["loc"]],
                "msg": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        raise _HTTPError(
            422,
            errors,
            input_error_notifications(errors, payload if loc_prefix == "body" else {}),
        ) from exc


def _query_param(query: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = query.get(key)
    return values[0] if values else default


def _query_int(
    query: dict[str, list[str]],
    key: str,
    default: int | None = None,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int | None:
    raw = _query_param(query, key)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise _HTTPError(422, f"Parâmetro {key} inválido") from exc
    if minimum is not None and value < minimum:
        raise _HTTPError(422, f"Parâmetro {key} abaixo do mínimo ({minimum})")
    if maximum is not None and value > maximum:
        raise _HTTPError(422, f"Parâmetro {key} acima do máximo ({maximum})")
    return value


def _query_bool(query: dict[str, list[str]], key: str, default: bool = False) -> bool:
    raw = _query_param(query, key)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in {"1", "true", "yes"}:
        return True
    if lowered in {"0", "false", "no"}:
        return False
    raise _HTTPError(422, f"Parâmetro booleano {key} inválido")


def dispatch_request(
    method: str,
    url_or_path: str,
    body: str | None = None,
    headers: dict[str, str] | None = None,
    store_json: str | None = None,
) -> dict[str, Any]:
    """Handle an API request and return status, headers, body, and updated store_json."""
    method = method.upper()
    parsed = urlsplit(url_or_path)
    path = parsed.path
    if path.startswith("/api/v1"):
        path = path[len("/api/v1") :] or "/"
    query = parse_qs(parsed.query, keep_blank_values=True)
    normalized_headers = {k.lower(): v for k, v in (headers or {}).items()}
    store = _load_store(store_json)
    mutated = False

    try:
        if method == "GET" and path == "/health":
            payload = HealthInfo(
                status="ok",
                app_version=APP_VERSION,
                api_version=APP_VERSION,
                engine_version=ENGINE_VERSION,
            ).model_dump(mode="json")
            return _json_response(200, payload)

        if method == "GET" and path == "/auth/session":
            return _json_response(
                200,
                {"mode": "local", "authenticated": True, "username": None, "csrf": None},
            )

        if method == "GET" and path == "/validation/requirements":
            payload = {
                key: FieldRequirement.model_validate(val).model_dump(mode="json")
                for key, val in requirements().items()
            }
            return _json_response(200, payload)

        if method == "GET" and path == "/locations/states":
            return _json_response(200, list(STATES))

        if method == "GET" and path == "/utilities":
            state = _query_param(query, "state")
            if state is not None and not re.fullmatch(r"^[A-Z]{2}$", state):
                raise _HTTPError(422, "UF inválida")
            items = [
                UtilityInfo.model_validate(item).model_dump(mode="json")
                for item in UTILITIES
                if state is None or state in item["states"]
            ]
            return _json_response(200, items)

        if method == "GET" and path == "/equipment":
            q = (_query_param(query, "q", "") or "")[:200]
            category = _query_param(query, "category")
            items = [
                CatalogItem.model_validate(item).model_dump(mode="json")
                for item in CATALOG
                if (
                    not q
                    or q.casefold()
                    in (item.get("selection_name", "") + " " + item["name"]).casefold()
                )
                and (category is None or item["category"] == category)
            ]
            return _json_response(200, items)

        if method == "GET" and path.startswith("/equipment/"):
            equipment_id = path.removeprefix("/equipment/")
            item = next((entry for entry in CATALOG if entry["id"] == equipment_id), None)
            if item is None:
                raise _HTTPError(404, "Referência de equipamento não encontrada")
            return _json_response(200, CatalogItem.model_validate(item).model_dump(mode="json"))

        if method == "GET" and path == "/standards":
            return _json_response(200, _to_jsonable([asdict(rule) for rule in RULES]))

        if method == "GET" and path == "/technical/documents":
            payload = DocumentRegistry(
                registry_version=registry_version(), documents=DOCUMENTS
            ).model_dump(mode="json")
            return _json_response(200, payload)

        if method == "GET" and path == "/technical/applicability":
            utility = _query_param(query, "utility")
            if not utility:
                raise _HTTPError(422, "Parâmetro utility obrigatório")
            state = _query_param(query, "state", "SP") or "SP"
            if not re.fullmatch(r"^[A-Z]{2}$", state):
                raise _HTTPError(422, "UF inválida")
            return _json_response(200, _to_jsonable(applicability(utility, state)))

        if method == "GET" and path == "/technical/integrity":
            return _json_response(200, _to_jsonable(integrity()))

        if method == "GET" and path == "/technical/revisions":
            revs = sorted(
                store["revisions"].values(), key=lambda item: item["created_at"], reverse=True
            )
            return _json_response(
                200,
                [
                    {
                        "id": row["id"],
                        "created_at": _brasilia_iso(row["created_at"]),
                        "status": row["review_status"],
                    }
                    for row in revs
                ],
            )

        if method == "GET" and path.startswith("/technical/revisions/"):
            rev_id = path.removeprefix("/technical/revisions/")
            row = store["revisions"].get(rev_id)
            if row is None:
                raise _HTTPError(404, "Versão técnica não encontrada")
            return _json_response(
                200,
                _to_jsonable(
                    {"id": row["id"], "snapshot": row["payload"], "status": row["review_status"]}
                ),
            )

        if method == "GET" and path == "/technical/rules":
            utility = _query_param(query, "utility", "unconfirmed") or "unconfirmed"
            state = _query_param(query, "state", "SP") or "SP"
            if not re.fullmatch(r"^[A-Z]{2}$", state):
                raise _HTTPError(422, "UF inválida")
            payload = TechnicalRules.model_validate(
                {
                    "registry_version": registry_version(),
                    "coverage": normative_capabilities(utility, state),
                    "mathematical": MATHEMATICAL_RULES,
                    "normative": [asdict(rule) for rule in RULES],
                    "regional_methods": [
                        method_info
                        for method_info in REGIONAL_METHODS
                        if utility == "unconfirmed"
                        or (
                            utility in method_info["supported_utilities"]
                            and state in method_info["supported_states"]
                        )
                    ],
                    "notice": "Validação matemática não implica conformidade normativa.",
                }
            ).model_dump(mode="json")
            return _json_response(200, payload)

        if method == "GET" and path == "/locations/municipality":
            code = _query_param(query, "code", "") or ""
            if not re.fullmatch(r"^\d{7}$", code):
                raise _HTTPError(422, "Código IBGE de 7 dígitos obrigatório")
            payload = MunicipalityLookup.model_validate(municipality_lookup(code)).model_dump(
                mode="json"
            )
            return _json_response(200, payload)

        if method == "GET" and path == "/locations/territory":
            raw_lat = _query_param(query, "latitude")
            raw_lon = _query_param(query, "longitude")
            if raw_lat is None or raw_lon is None:
                raise _HTTPError(422, "Coordenadas obrigatórias")
            try:
                lat = Decimal(raw_lat)
                lon = Decimal(raw_lon)
            except InvalidOperation as exc:
                raise _HTTPError(422, "Coordenadas inválidas") from exc
            if (
                not lat.is_finite()
                or not lon.is_finite()
                or lat < -90
                or lat > 90
                or lon < -180
                or lon > 180
            ):
                raise _HTTPError(422, "Coordenadas fora dos limites SIRGAS2000")
            payload = TerritoryLookup.model_validate(territory_lookup(lat, lon)).model_dump(
                mode="json"
            )
            return _json_response(200, payload)

        if method == "POST" and path in (
            "/calculations/full",
            "/calculations/loads",
            "/calculations/demand",
        ):
            parsed_body = _parse_json_body(body)
            calc_input = _validate_model(CalculationInput, parsed_body)
            result = CalculationResult.model_validate(
                calculate(calc_input.model_dump(mode="json"))
            ).model_dump(mode="json")
            return _json_response(200, result)

        if method == "POST" and path == "/calculations/energisa-demand":
            parsed_body = _parse_json_body(body)
            demand_input = _validate_model(EnergisaDemandInput, parsed_body)
            result = calculate_energisa_demand(demand_input.model_dump(mode="json"))
            payload = EnergisaDemandResult.model_validate(
                {**result, "reference": asdict(ENERGISA_V7_EVIDENCE)}
            ).model_dump(mode="json")
            return _json_response(200, payload)

        if method == "GET" and path == "/projects":
            archived = _query_bool(query, "archived", False)
            limit = _query_int(query, "limit", None, minimum=1, maximum=100)
            offset = _query_int(query, "offset", 0, minimum=0) or 0
            q = (_query_param(query, "q", "") or "")[:200]
            sort = _query_param(query, "sort", "recent") or "recent"
            rows = _filter_projects(store, archived=archived, q=q, sort=sort)[offset:]
            if limit is not None:
                rows = rows[:limit]
            return _json_response(200, [_view_project(row) for row in rows])

        if method == "GET" and path == "/projects/summaries":
            archived = _query_bool(query, "archived", False)
            limit = _query_int(query, "limit", 21, minimum=1, maximum=100) or 21
            offset = _query_int(query, "offset", 0, minimum=0) or 0
            q = (_query_param(query, "q", "") or "")[:200]
            sort = _query_param(query, "sort", "recent") or "recent"
            rows = _filter_projects(store, archived=archived, q=q, sort=sort)[
                offset : offset + limit
            ]
            summaries = [
                ProjectSummary(
                    id=row["id"],
                    version=row["version"],
                    created_at=_brasilia_iso(row["created_at"]),
                    updated_at=_brasilia_iso(row["updated_at"]),
                    deleted_at=_brasilia_iso(row["deleted_at"]) if row.get("deleted_at") else None,
                    standards_version=row["standards_version"],
                    name=str(row["payload"].get("name") or ""),
                    municipality=str(row["payload"].get("municipality") or ""),
                    state=str(row["payload"].get("state") or "SP"),
                    utility=str(row["payload"].get("utility") or "unconfirmed"),
                ).model_dump(mode="json")
                for row in rows
            ]
            return _json_response(200, summaries)

        if method == "POST" and path == "/projects":
            parsed_body = _parse_json_body(body)
            data = _validate_model(ProjectInput, parsed_body)
            _reject_invalid_draft(data)
            idem_raw = normalized_headers.get("idempotency-key")
            idem_key = None
            if idem_raw:
                try:
                    idem_key = str(UUID(idem_raw))
                except ValueError as exc:
                    raise _HTTPError(422, "Idempotency-Key inválido") from exc
                previous = store["projects"].get(idem_key)
                if previous is not None:
                    if previous.get("deleted_at") is None and _same_input(
                        previous["payload"], data
                    ):
                        return _json_response(201, _view_project(previous))
                    raise _HTTPError(
                        409,
                        "Primeiro salvamento já recebido. Reabra o projeto antes de reenviar alterações.",
                    )
            now = _utcnow_iso()
            project_id = idem_key or str(uuid4())
            row = {
                "id": project_id,
                "version": 1,
                "payload": data.model_dump(mode="json"),
                "created_at": now,
                "updated_at": now,
                "deleted_at": None,
                "standards_version": registry_version(),
            }
            store["projects"][project_id] = row
            _record_history(store, row)
            mutated = True
            return _json_response(201, _view_project(row), store if mutated else None)

        project_match = re.fullmatch(r"/projects/([0-9a-fA-F-]{36})(?:/([a-z]+))?", path)
        if project_match:
            project_id, action = project_match.group(1), project_match.group(2)

            if action is None and method == "GET":
                row = _find_active_project(store, project_id)
                return _json_response(200, _view_project(row))

            if action is None and method == "PUT":
                expected_version = _query_int(query, "expected_version", minimum=1)
                if expected_version is None:
                    raise _HTTPError(422, "expected_version obrigatório")
                row = _find_active_project(store, project_id)
                if row["version"] != expected_version:
                    raise _HTTPError(
                        409, "Projeto alterado em outra sessão. Recarregue antes de salvar."
                    )
                parsed_body = _parse_json_body(body)
                data = _validate_model(ProjectInput, parsed_body)
                _reject_invalid_draft(data)
                current_reg = registry_version()
                if row["standards_version"] == current_reg and _same_input(row["payload"], data):
                    return _json_response(200, _view_project(row))
                row["version"] += 1
                row["standards_version"] = current_reg
                row["payload"] = data.model_dump(mode="json")
                row["updated_at"] = _utcnow_iso()
                _record_history(store, row)
                mutated = True
                return _json_response(200, _view_project(row), store if mutated else None)

            if action is None and method == "DELETE":
                expected_version = _query_int(query, "expected_version", minimum=1)
                row = _find_active_project(store, project_id)
                if expected_version is not None and row["version"] != expected_version:
                    raise _HTTPError(409, "Projeto alterado. Atualize a lista antes de excluir.")
                now = _utcnow_iso()
                row["version"] += 1
                row["deleted_at"] = now
                row["updated_at"] = now
                mutated = True
                return _json_response(204, None, store if mutated else None)

            if action == "restore" and method == "POST":
                expected_version = _query_int(query, "expected_version", minimum=1)
                if expected_version is None:
                    raise _HTTPError(422, "expected_version obrigatório")
                key = str(UUID(project_id))
                row = store["projects"].get(key)
                if row is None or row.get("deleted_at") is None:
                    raise _HTTPError(404, "Projeto excluído não encontrado")
                if row["version"] != expected_version:
                    raise _HTTPError(409, "Projeto alterado. Atualize a lista antes de restaurar.")
                row["version"] += 1
                row["deleted_at"] = None
                row["updated_at"] = _utcnow_iso()
                mutated = True
                return _json_response(200, _view_project(row), store if mutated else None)

            if action == "permanent" and method == "DELETE":
                expected_version = _query_int(query, "expected_version", minimum=1)
                if expected_version is None:
                    raise _HTTPError(422, "expected_version obrigatório")
                key = str(UUID(project_id))
                row = store["projects"].get(key)
                if row is None:
                    raise _HTTPError(404, "Projeto excluído não encontrado")
                if row.get("deleted_at") is None:
                    raise _HTTPError(
                        409, "Envie o projeto para a lixeira antes de excluir definitivamente."
                    )
                if row["version"] != expected_version:
                    raise _HTTPError(
                        409,
                        "Projeto alterado. Atualize a lixeira antes de excluir definitivamente.",
                    )
                del store["projects"][key]
                store["history"] = [item for item in store["history"] if item["project_id"] != key]
                mutated = True
                return _json_response(204, None, store if mutated else None)

            if action == "duplicate" and method == "POST":
                original = _find_active_project(store, project_id)
                payload = dict(original["payload"])
                payload["name"] = payload["name"][:190] + " · cópia"
                data = _validate_model(ProjectInput, payload)
                _reject_invalid_draft(data)
                now = _utcnow_iso()
                copy_id = str(uuid4())
                row = {
                    "id": copy_id,
                    "version": 1,
                    "payload": data.model_dump(mode="json"),
                    "created_at": now,
                    "updated_at": now,
                    "deleted_at": None,
                    "standards_version": registry_version(),
                }
                store["projects"][copy_id] = row
                _record_history(store, row)
                mutated = True
                return _json_response(201, _view_project(row), store if mutated else None)

            if action == "history" and method == "GET":
                row = _find_active_project(store, project_id)
                items = [item for item in store["history"] if item["project_id"] == row["id"]]
                items.sort(
                    key=lambda item: (item["project_version"], item["created_at"]),
                    reverse=True,
                )
                return _json_response(
                    200,
                    [
                        {
                            "id": item["id"],
                            "version": item["project_version"],
                            "created_at": _brasilia_iso(item["created_at"]),
                            "inputs": item["inputs"],
                            "result": item["result"],
                        }
                        for item in items
                    ],
                )

            if action == "report" and method == "GET":
                row = _find_active_project(store, project_id)
                latest = _latest_history(store, row["id"])
                calc = CalculationResult.model_validate(
                    calculate(
                        CalculationInput.model_validate(row["payload"]).model_dump(mode="json")
                    )
                ).model_dump(mode="json")
                return _json_response(
                    200,
                    {
                        "project": _view_project(row),
                        "calculation": calc,
                        "calculation_basis": "current_registry_preview",
                        "recorded_registry_version": row["standards_version"],
                        "current_registry_version": registry_version(),
                        "recorded_calculation": latest["result"] if latest else None,
                        "notice": "Documento parcial. Não substitui revisão e responsabilidade técnica profissional.",
                    },
                )

            if action == "revalidation" and method == "GET":
                row = _find_active_project(store, project_id)
                current = registry_version()
                latest = _latest_history(store, row["id"])
                prev_engine = (
                    latest["result"].get("engine_version")
                    if latest and latest.get("result")
                    else None
                )
                reval = ProjectRevalidation(
                    project_id=row["id"],
                    project_version=row["version"],
                    previous_engine_version=prev_engine,
                    previous_registry_version=row["standards_version"],
                    current_registry_version=current,
                    requires_revalidation=row["standards_version"] != current
                    or (latest is not None and prev_engine != ENGINE_VERSION),
                    previous_result=latest["result"] if latest else None,
                    current_result=CalculationResult.model_validate(
                        calculate(
                            CalculationInput.model_validate(row["payload"]).model_dump(mode="json")
                        )
                    ),
                    notice="Comparação conservadora. Valores manuais e histórico permanecem preservados.",
                ).model_dump(mode="json")
                return _json_response(200, reval)

            if action == "recalculate" and method == "POST":
                expected_version = _query_int(query, "expected_version", minimum=1)
                if expected_version is None:
                    raise _HTTPError(422, "expected_version obrigatório")
                row = _find_active_project(store, project_id)
                if row["version"] != expected_version:
                    raise _HTTPError(409, "Projeto alterado; recarregue antes de recalcular")
                row["version"] += 1
                row["updated_at"] = _utcnow_iso()
                row["standards_version"] = registry_version()
                _record_history(store, row)
                mutated = True
                return _json_response(200, _view_project(row), store if mutated else None)

        if method == "POST" and path == "/reports/pdf":
            parsed_body = _parse_json_body(body)
            export_input = _validate_model(PDFExportInput, parsed_body)
            project, result, version = _prepare_report(export_input, store)
            pdf_bytes = render_report(project, result, project_version=version)
            return {
                "status": 200,
                "headers": {
                    "Content-Type": "application/pdf",
                    "Content-Disposition": _report_disposition(project["name"], "pdf"),
                },
                "body": None,
                "body_base64": base64.b64encode(pdf_bytes).decode("ascii"),
                "store_json": None,
            }

        if method == "POST" and path == "/reports/json":
            parsed_body = _parse_json_body(body)
            export_input = _validate_model(PDFExportInput, parsed_body)
            project, result, version = _prepare_report(export_input, store)
            summary_bytes = (
                json.dumps(
                    build_summary(project, result, project_version=version),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            ).encode("utf-8")
            return {
                "status": 200,
                "headers": {
                    "Content-Type": "application/json",
                    "Content-Disposition": _report_disposition(project["name"], "json"),
                },
                "body": None,
                "body_base64": base64.b64encode(summary_bytes).decode("ascii"),
                "store_json": None,
            }

        if method == "GET" and path == "/knowledge/stats":
            return _json_response(
                200,
                {
                    "documents": 0,
                    "pages": 0,
                    "text_pages": 0,
                    "sources": 0,
                    "extraction_counts": {},
                    "kinds": {},
                    "review_states": {},
                    "notice": KNOWLEDGE_NOTICE,
                },
            )

        if method == "GET" and path == "/knowledge/documents":
            return _json_response(
                200,
                {"items": [], "next_offset": None, "notice": KNOWLEDGE_NOTICE},
            )

        if method == "GET" and path == "/knowledge/sources":
            return _json_response(200, [])

        if method == "GET" and path.startswith("/knowledge/documents/"):
            raise _HTTPError(404, "Documento não encontrado.")

        raise _HTTPError(404, "Rota não encontrada")
    except _HTTPError as exc:
        error_payload: dict[str, Any] = {"detail": exc.detail}
        if exc.notifications is not None:
            error_payload["notifications"] = exc.notifications
        return _json_response(exc.status, error_payload)


def _json_response(status: int, payload: Any, store: dict | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": payload,
        "body_base64": None,
        "store_json": json.dumps(store, ensure_ascii=False, separators=(",", ":"))
        if store is not None
        else None,
    }
