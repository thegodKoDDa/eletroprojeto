import asyncio
import os

import pytest
from app.database import get_session
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import sessionmaker

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client(database_engine):
    engine = database_engine
    sessions = sessionmaker(engine, expire_on_commit=False)

    def override():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = override

    # Some restricted sandboxes deny thread→loop socketpair wakeups. Opt-in
    # timer keeps the loop responsive without replacing the real ASGI stack.
    async def heartbeat():
        while True:
            await asyncio.sleep(0.01)

    task = (
        asyncio.create_task(heartbeat())
        if os.getenv("ELETROPROJETO_POLL_TEST_LOOP") == "1"
        else None
    )
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client
    finally:
        if task:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def payload():
    return {
        "name": "Casa teste",
        "municipality": "Município informado",
        "built_area_m2": "60",
        "environments": [
            {
                "name": "Banheiro",
                "type": "bathroom",
                "area_m2": "4",
                "perimeter_m": "8",
                "loads": [
                    {
                        "name": "Chuveiro",
                        "unit_power_w": "7500",
                        "quantity": 2,
                        "power_factor": "1",
                        "power_origin": "nameplate",
                    }
                ],
            }
        ],
    }


async def test_calculation(client, payload):
    response = await client.post("/api/v1/calculations/full", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["installed_power"]["value"] == "15000"
    assert "normative" not in data


async def test_lifecycle(client, payload):
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201
    project = response.json()
    project_id = project["id"]
    assert len((await client.get("/api/v1/projects")).json()) == 1
    loaded = (await client.get(f"/api/v1/projects/{project_id}")).json()
    assert loaded["name"] == "Casa teste"
    assert loaded["created_at"].endswith("-03:00")
    payload["environments"][0]["loads"][0]["unit_power_w"] = "5500"
    assert (
        await client.put(f"/api/v1/projects/{project_id}?expected_version=1", json=payload)
    ).status_code == 200
    assert (
        await client.put(f"/api/v1/projects/{project_id}?expected_version=1", json=payload)
    ).status_code == 409
    report = (await client.get(f"/api/v1/projects/{project_id}/report")).json()
    assert report["calculation"]["installed_power"]["value"] == "11000"
    history = (await client.get(f"/api/v1/projects/{project_id}/history")).json()
    assert len(history) == 2
    assert history[0]["version"] == 2
    assert history[1]["result"]["installed_power"]["value"] == "15000"
    assert (await client.delete(f"/api/v1/projects/{project_id}")).status_code == 204
    assert (await client.get(f"/api/v1/projects/{project_id}")).status_code == 404


@pytest.mark.parametrize("power", ["-1", "NaN", "Infinity"])
async def test_invalid_power(client, payload, power):
    payload["environments"][0]["loads"][0]["unit_power_w"] = power
    assert (await client.post("/api/v1/calculations/full", json=payload)).status_code == 422


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True])
async def test_invalid_quantity(client, payload, quantity):
    payload["environments"][0]["loads"][0]["quantity"] = quantity
    assert (await client.post("/api/v1/calculations/full", json=payload)).status_code == 422


async def test_duplicate_ids(client, payload):
    from uuid import uuid4

    load = payload["environments"][0]["loads"][0]
    load["id"] = str(uuid4())
    payload["environments"][0]["loads"].append(dict(load))
    assert (await client.post("/api/v1/calculations/full", json=payload)).status_code == 422


async def test_catalog_not_modified_by_project(client, payload):
    before = (await client.get("/api/v1/equipment")).json()
    payload["environments"][0]["loads"][0]["unit_power_w"] = "85"
    await client.post("/api/v1/projects", json=payload)
    assert (await client.get("/api/v1/equipment")).json() == before


async def test_unknown_fields_rejected(client, payload):
    payload["demand_factor"] = 0.92
    assert (await client.post("/api/v1/calculations/full", json=payload)).status_code == 422


async def test_full_reference_flow_with_manual_edit(client):
    import copy
    from uuid import uuid4

    catalog = (await client.get("/api/v1/equipment")).json()

    def load(id):
        ref = copy.deepcopy(next(item for item in catalog if item["id"] == id))
        return dict(
            id=str(uuid4()),
            name=ref["name"],
            category=ref["category"],
            kind=ref["kind"],
            equipment_type=ref["equipment_type"],
            technology=ref["technology"],
            unit_power_w=ref["reference_power_w"],
            voltage_v=ref["voltage_v"],
            power_factor=ref["power_factor"],
            power_origin="manufacturer",
            brand=ref["brand"] or "",
            model=ref["model"] or "",
            source=ref["source"] or "Referência",
            parameters=ref["parameters"],
            catalog_reference=ref,
        )

    led = load("philips-led-929001195311")
    led["quantity"] = 4
    tv = load("samsung-tv43-au7700")
    ac = load("lg-ac-12000-s3w12ja33b")
    shower = load("lorenzetti-advanced-127-5500")
    second_shower = copy.deepcopy(shower)
    second_shower["id"] = str(uuid4())
    project = dict(
        name="Fluxo técnico completo",
        municipality="Cidade",
        built_area_m2="60",
        environments=[
            dict(
                name="Quarto", type="bedroom", area_m2="12", perimeter_m="14", loads=[led, tv, ac]
            ),
            dict(
                name="Banheiro",
                type="bathroom",
                area_m2="4",
                perimeter_m="8",
                loads=[shower, second_shower],
            ),
        ],
    )
    before = (await client.post("/api/v1/calculations/full", json=project)).json()
    assert before["installed_power"]["value"] == "12296"
    second_shower.update(
        unit_power_w="7500",
        voltage_v="220",
        power_origin="nameplate",
        source="Etiqueta informada pelo usuário",
    )
    after = (await client.post("/api/v1/calculations/full", json=project)).json()
    assert after["installed_power"]["value"] == "14296"
    assert sorted(after["by_environment_w"].values()) == ["1296", "13000"]
    assert after["input_digest"] != before["input_digest"]
    assert "normative" not in after
    saved = (await client.post("/api/v1/projects", json=project)).json()
    restored = (await client.get(f"/api/v1/projects/{saved['id']}")).json()
    used = restored["environments"][1]["loads"][1]
    assert used["manual_override"] is True
    assert used["unit_power_w"] == "7500"
    assert used["catalog_reference"]["reference_power_w"] == "5500"
    report = (await client.get(f"/api/v1/projects/{saved['id']}/report")).json()
    assert report["calculation"]["installed_power"]["value"] == "14296"


async def test_catalog_contract_and_unknown_power(client, payload):
    response = await client.get("/api/v1/equipment")
    assert response.status_code == 200
    assert len(response.json()) >= 25
    payload["environments"][0]["loads"][0]["unit_power_w"] = None
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert result["installed_power"]["status"] == "pending"
    assert len(result["unknown_load_ids"]) == 1


async def test_cors_local_addresses(client):
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = await client.options(
            "/api/v1/projects", headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


async def test_unsaved_calculation_does_not_require_project_metadata(client):
    data = {
        "environments": [
            {
                "name": "Quarto",
                "area_m2": "12",
                "perimeter_m": "14",
                "loads": [{"name": "Carga", "unit_power_w": "85"}],
            }
        ]
    }
    response = await client.post("/api/v1/calculations/full", json=data)
    assert response.status_code == 200
    assert response.json()["installed_power"]["value"] == "85"
    assert (await client.post("/api/v1/projects", json=data)).status_code == 422


async def test_simple_selection_keeps_sources_and_advanced_inputs_on_reopen(client):
    import copy
    from decimal import Decimal

    catalog = (await client.get("/api/v1/equipment")).json()
    reference = next(item for item in catalog if item["selection_name"] == "Televisor")
    data = dict(
        name="Cadastro compacto",
        municipality="Cidade",
        built_area_m2="60",
        environments=[
            dict(
                name="Quarto",
                type="bedroom",
                area_m2="12",
                perimeter_m="14",
                loads=[
                    dict(
                        name=reference["selection_name"],
                        unit_power_w=reference["reference_power_w"],
                        quantity=2,
                        voltage_v="220",
                        power_factor="0.8",
                        power_origin="user_estimate",
                        source="Referência de categoria",
                        equipment_type="television",
                        brand=reference["brand"],
                        model=reference["model"],
                        catalog_reference=copy.deepcopy(reference),
                        parameters={"configuration": "single_phase", "screen_inches": "43"},
                    )
                ],
            )
        ],
    )
    response = await client.post("/api/v1/projects", json=data)
    assert response.status_code == 201
    project_id = response.json()["id"]
    restored = (await client.get(f"/api/v1/projects/{project_id}")).json()
    load = restored["environments"][0]["loads"][0]
    assert load["name"] == "Televisor"
    assert load["parameters"]["configuration"] == "single_phase"
    assert load["power_factor"] == "0.8"
    assert load["brand"] == reference["brand"] and load["model"] == reference["model"]
    assert load["catalog_reference"]["source_url"] == reference["source_url"]
    assert load["catalog_reference"]["selection_name"] == "Televisor"
    result = (await client.get(f"/api/v1/projects/{project_id}/report")).json()["calculation"]
    assert result["installed_power"]["value"] == "260"
    assert result["installed_power"]["status"] == "estimated"
    assert Decimal(result["apparent_power"]["value"]) == Decimal("325")
    assert abs(
        Decimal(result["load_results"][0]["unit_current_a"])
        - Decimal("0.7386363636363636363636363636363636363636")
    ) < Decimal("1e-30")
    assert "normative" not in result


async def test_territorial_candidates_do_not_claim_municipality_coverage(client):
    candidates = (await client.get("/api/v1/utilities?state=SP&municipality=Desconhecido")).json()
    assert len(candidates) == 7
    assert all(item["municipality_mapping"] == "unverified" for item in candidates)
    assert (await client.get("/api/v1/utilities?state=MG")).json() == []
    assert len((await client.get("/api/v1/locations/states")).json()) == 27
    assert (await client.get("/api/v1/technical/integrity")).status_code == 404


async def test_reference_lookup_search_and_rules(client):
    items = (await client.get("/api/v1/equipment?q=Chuveiro")).json()
    assert items
    for item in items:
        assert (await client.get("/api/v1/equipment/" + item["id"])).json() == item
    assert (await client.get("/api/v1/equipment/missing")).status_code == 404
    for path in ("/technical/rules", "/technical/documents", "/standards"):
        assert (await client.get("/api/v1" + path)).status_code == 404


async def test_verified_9000_btu_reference_uses_electrical_input(client, payload):
    ref = (await client.get("/api/v1/equipment/lg-ac-9000-s3q09aa33a")).json()
    assert ref["reference_power_w"] == "800"
    assert ref["parameters"]["cooling_capacity_btu_h"] == "9000"
    assert ref["power_factor"] is None
    load = payload["environments"][0]["loads"][0]
    load.update(
        equipment_type="air_conditioner",
        quantity=2,
        unit_power_w="800",
        power_factor=None,
        parameters=ref["parameters"],
        voltage_v="220",
        power_origin="manufacturer",
        source=ref["source_url"],
    )
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert result["installed_power"]["value"] == "1600"
    assert result["apparent_power"] is None
    assert "normative" not in result


async def test_missing_room_dimensions_do_not_block_known_power(client, payload):
    payload["analysis_scope"] = "normative"
    room = payload["environments"][0]
    room["area_m2"] = room["perimeter_m"] = None
    response = await client.post("/api/v1/calculations/full", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["installed_power"]["value"] == "15000"
    assert data["installed_power"]["status"] == "calculated"
    assert data["field_issues"] == []
    assert "normative" not in data
    assert "normative_capabilities" not in data
    assert (
        await client.post("/api/v1/projects", json=payload)
    ).status_code == 201  # explicit draft


async def test_field_issues_disappear_and_return_bidirectionally(client, payload):
    payload["analysis_scope"] = "current"
    payload["utility"] = "energisa_sul_sudeste"
    load = payload["environments"][0]["loads"][0]
    load.update(unit_power_w=None, voltage_v=None, power_factor=None)

    async def issues():
        data = (await client.post("/api/v1/calculations/full", json=payload)).json()
        return {issue["field"] for issue in data["field_issues"]}, data

    before, _ = await issues()
    assert before == {"load.unit_power_w"}
    load.update(
        unit_power_w="7500",
        voltage_v="220",
        power_factor="1",
        parameters={"configuration": "single_phase"},
    )
    after, result = await issues()
    assert not after
    assert result["load_results"][0]["unit_current_a"].startswith("34.090909")
    assert "normative" not in result
    load["voltage_v"] = None
    again, result = await issues()
    assert again == set()
    assert result["load_results"][0]["unit_current_a"] is None
    assert result["installed_power"]["value"] == "15000"
    load["voltage_v"] = "-220"
    assert (await client.post("/api/v1/calculations/full", json=payload)).status_code == 422


async def test_conditional_requirements_from_api(client, payload):
    rules = (await client.get("/api/v1/validation/requirements")).json()
    assert rules["load.unit_power_w"]["when"] == {"power_mode": "electrical"}
    assert rules["load.parameters.efficiency"]["when"] == {"power_mode": "mechanical"}
    assert rules["load.power_factor"]["when"] == {"assume_resistive": False}
    load = payload["environments"][0]["loads"][0]
    load.update(
        equipment_type="motor",
        unit_power_w=None,
        parameters={"power_mode": "mechanical", "mechanical_power": "1"},
    )
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    fields = {issue["field"] for issue in result["field_issues"]}
    assert "load.parameters.efficiency" in fields
    assert "load.unit_power_w" not in fields


async def test_pdf_snapshot_export_and_stale_protection(client, payload):
    from app.schemas import CalculationInput

    payload = CalculationInput.model_validate(payload).model_dump(mode="json")
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    request = dict(
        project=payload,
        expected_input_digest=result["input_digest"],
        expected_registry_version=result["technical_context"]["registry_version"],
        expected_engine_version=result["engine_version"],
    )
    response = await client.post("/api/v1/reports/pdf", json=request)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-1.4") and response.content.endswith(b"%%EOF\n")
    request["project"]["environments"][0]["loads"][0]["unit_power_w"] = "5500"
    assert (await client.post("/api/v1/reports/pdf", json=request)).status_code == 409
    request["expected_registry_version"] = "0" * 64
    assert (await client.post("/api/v1/reports/pdf", json=request)).status_code == 409


@pytest.mark.parametrize("format", ["pdf", "json"])
@pytest.mark.parametrize(
    "changed",
    [
        {"circuits": [{"id": "c1", "name": "Circuito alterado", "length_m": "40"}]},
        {"circuits": [{"id": "c1", "protections": {"fault_loop_ohm": "0.5"}}]},
        {"circuits": [{"id": "c1", "insulation": "XLPE90", "terminals_90c_confirmed": True}]},
        {"circuits": [{"id": "c1", "protections": {"surge": {"required_uc_v": "242"}}}]},
        {"circuits": [{"id": "c1", "protections": {"selectivity": {"limit_ka": "6"}}}]},
        {"service_entry": {"network": "220_127", "route": "underground"}},
        {"circuits": [], "service_entry": None},
    ],
)
async def test_archived_study_metadata_does_not_change_energy_report(
    client, payload, format, changed
):
    from app.schemas import CalculationInput

    payload.update(circuits=[{"id": "c1"}], service_entry={"network": "unknown"})
    inputs = CalculationInput.model_validate(payload).model_dump(mode="json")
    calculation = (await client.post("/api/v1/calculations/full", json=inputs)).json()
    request = dict(
        project={**inputs, **changed},
        expected_input_digest=calculation["input_digest"],
        expected_registry_version=calculation["technical_context"]["registry_version"],
        expected_engine_version=calculation["engine_version"],
    )
    assert (await client.post(f"/api/v1/reports/{format}", json=request)).status_code == 200


async def test_latest_recorded_calculation_is_stable_with_identical_timestamps(
    client, payload, monkeypatch
):
    from datetime import datetime, timezone

    from app import main, projects

    instant = datetime(2026, 10, 24, tzinfo=timezone.utc)
    monkeypatch.setattr(main, "utcnow", lambda: instant)
    monkeypatch.setattr(projects, "utcnow", lambda: instant)
    created = (await client.post("/api/v1/projects", json=payload)).json()
    payload["environments"][0]["loads"][0]["unit_power_w"] = "5500"
    updated = await client.put(f"/api/v1/projects/{created['id']}?expected_version=1", json=payload)
    assert updated.status_code == 200
    report = (await client.get(f"/api/v1/projects/{created['id']}/report")).json()
    assert report["recorded_calculation"]["installed_power"]["value"] == "11000"
    history = (await client.get(f"/api/v1/projects/{created['id']}/history")).json()
    assert [row["version"] for row in history] == [2, 1]


async def test_saved_pdf_version_is_checked_and_invalid_data_not_exported(client, payload):
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    inputs = {
        key: value
        for key, value in saved.items()
        if key
        not in ("id", "version", "created_at", "updated_at", "standards_version", "deleted_at")
    }
    result = (await client.post("/api/v1/calculations/full", json=inputs)).json()
    request = dict(
        project=inputs,
        saved_project_id=saved["id"],
        saved_project_version=1,
        expected_input_digest=result["input_digest"],
        expected_engine_version=result["engine_version"],
        expected_registry_version=result["technical_context"]["registry_version"],
    )
    response = await client.post("/api/v1/reports/pdf", json=request)
    assert response.status_code == 200
    from tests.test_pdf import extract_pages

    assert saved["name"] in "\n".join(extract_pages(response.content))
    assert "filename*=UTF-8" in response.headers["content-disposition"]
    request["saved_project_version"] = 2
    assert (await client.post("/api/v1/reports/pdf", json=request)).status_code == 409
    request["project"]["environments"][0]["loads"][0]["power_factor"] = "1.5"
    assert (await client.post("/api/v1/reports/pdf", json=request)).status_code == 422


async def test_invalid_zero_power_cannot_be_saved_as_valid_data(client, payload):
    payload["environments"][0]["loads"][0]["unit_power_w"] = "0"
    assert (await client.post("/api/v1/projects", json=payload)).status_code == 422
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert result["installed_power"]["status"] == "pending"
    assert result["apparent_power"] is None
    assert result["load_results"][0]["unit_current_a"] is None
    assert any(
        issue["field"] == "load.unit_power_w" and issue["status"] == "invalid"
        for issue in result["field_issues"]
    )


async def test_saved_pdf_with_incomplete_metadata_returns_conflict_not_server_error(
    client, payload
):
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    inputs = {
        key: value
        for key, value in saved.items()
        if key
        not in ("id", "version", "created_at", "updated_at", "standards_version", "deleted_at")
    }
    inputs["name"] = ""
    result = (await client.post("/api/v1/calculations/full", json=inputs)).json()
    request = dict(
        project=inputs,
        saved_project_id=saved["id"],
        saved_project_version=1,
        expected_input_digest=result["input_digest"],
        expected_engine_version=result["engine_version"],
        expected_registry_version=result["technical_context"]["registry_version"],
    )
    assert (await client.post("/api/v1/reports/pdf", json=request)).status_code == 409


async def test_scope_limits_required_fields_without_changing_known_watts(client, payload):
    payload["environments"][0]["loads"][0].update(voltage_v=None, power_factor=None)
    installed = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert installed["installed_power"]["value"] == "15000"
    assert not any(item["category"] == "error" for item in installed["notifications"])
    payload["analysis_scope"] = "current"
    current = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert not current["notifications"]
    assert current["installed_power"]["value"] == "15000"
    assert len({item["id"] for item in current["notifications"]}) == len(current["notifications"])
    assert not any(item["category"] == "normative" for item in current["notifications"])
    assert not any(item["target_id"] == "project.utility" for item in current["notifications"])
    assert "normative_capabilities" not in current


async def test_edited_power_voltage_pf_quantity_category_propagate_independently(client, payload):
    payload["analysis_scope"] = "current"
    load = payload["environments"][0]["loads"][0]
    load.update(
        unit_power_w="1760",
        quantity=2,
        voltage_v="220",
        power_factor="0.8",
        parameters={"configuration": "single_phase"},
        category="Teste A",
    )

    async def calc():
        return (await client.post("/api/v1/calculations/full", json=payload)).json()

    first = await calc()
    assert first["installed_power"]["value"] == "3520"
    assert first["apparent_power"]["value"] == "4400"
    from decimal import Decimal

    assert Decimal(first["load_results"][0]["unit_current_a"]) == Decimal("10")
    load["voltage_v"] = "110"
    voltage = await calc()
    assert voltage["installed_power"]["value"] == "3520"
    assert voltage["apparent_power"]["value"] == "4400"
    assert Decimal(voltage["load_results"][0]["unit_current_a"]) == Decimal("20")
    load.update(power_factor="1", quantity=3, category="Teste B")
    final = await calc()
    assert final["installed_power"]["value"] == "5280"
    assert final["apparent_power"]["value"] == "5280"
    assert Decimal(final["load_results"][0]["unit_current_a"]) == Decimal("16")
    assert final["by_category_w"] == {"Teste B": "5280"}
    assert len(final["memory"]) == 1
    assert "normative" not in final
    assert final["input_digest"] != first["input_digest"]


async def test_invalid_field_notification_has_precise_target_and_no_raw_input(client, payload):
    from uuid import uuid4

    load = payload["environments"][0]["loads"][0]
    load["id"] = str(uuid4())
    load["power_factor"] = "1.5"
    response = await client.post("/api/v1/calculations/full", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert all("input" not in item and "ctx" not in item for item in data["detail"])
    notice = data["notifications"][0]
    assert notice["target_id"] == f"load.{load['id']}.power_factor"
    assert notice["location"] == ["Banheiro", "Chuveiro"]
    assert "Fator de potência" in notice["problem"]
    assert notice["solution"]


async def test_version_and_documentation_groups_are_consistent(client):
    import json
    import tomllib
    from pathlib import Path

    from app.version import APP_VERSION, ENGINE_VERSION

    root = Path(__file__).resolve().parents[2]
    frontend = json.loads((root / "frontend/package.json").read_text())
    backend = tomllib.loads((root / "backend/pyproject.toml").read_text())
    health = (await client.get("/api/v1/health")).json()
    assert (
        health["app_version"]
        == health["api_version"]
        == frontend["version"]
        == backend["project"]["version"]
        == APP_VERSION
    )
    assert health["engine_version"] == ENGINE_VERSION
    spec = (await client.get("/openapi.json")).json()
    assert spec["info"]["version"] == APP_VERSION
    assert spec["paths"]["/api/v1/reports/pdf"]["post"]["tags"] == ["Relatórios"]


async def test_voltage_mismatch_is_a_technical_warning_not_a_power_rewrite(client, payload):
    from app.catalog import CATALOG

    ref = next(item for item in CATALOG if item["id"] == "lorenzetti-advanced-220-7500")
    load = payload["environments"][0]["loads"][0]
    load.update(unit_power_w="7500", voltage_v="127", catalog_reference=ref)
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert result["installed_power"]["value"] == "15000"
    notice = next(item for item in result["notifications"] if item["id"].endswith(".voltage"))
    assert notice["category"] == "technical"
    assert notice["target_id"].endswith(".voltage_v")


@pytest.mark.parametrize(
    "body", [None, [], {"environments": [2]}, {"environments": [{"loads": [3]}]}]
)
async def test_malformed_input_diagnostics_do_not_raise_server_errors(client, body):
    assert (await client.post("/api/v1/calculations/full", json=body)).status_code == 422


async def test_optional_metadata_can_be_unknown_without_blocking_save_or_known_power(
    client, payload
):
    payload.update(built_area_m2=None, floors=None, residence_type=None, reference_voltage_v=None)
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201
    stored = response.json()
    assert stored["floors"] is None and stored["built_area_m2"] is None
    result = (await client.get(f"/api/v1/projects/{stored['id']}/report")).json()["calculation"]
    assert result["installed_power"]["value"] == "15000"


async def test_reversible_deletion_preserves_history_and_guards_versions(client, payload):
    project = (await client.post("/api/v1/projects", json=payload)).json()
    path = f"/api/v1/projects/{project['id']}"
    assert (await client.delete(path + "?expected_version=99")).status_code == 409
    assert (await client.get(path)).status_code == 200
    assert (await client.delete(path + "?expected_version=1")).status_code == 204
    assert (await client.get("/api/v1/projects")).json() == []
    assert (await client.get(path)).status_code == 404
    archived = (await client.get("/api/v1/projects?archived=true")).json()
    assert len(archived) == 1 and archived[0]["id"] == project["id"]
    assert (await client.post(path + "/restore?expected_version=1")).status_code == 409
    restored = await client.post(path + f"/restore?expected_version={archived[0]['version']}")
    assert restored.status_code == 200
    assert restored.json()["environments"] == project["environments"]
    history = (await client.get(path + "/history")).json()
    assert len(history) == 1
    assert history[0]["result"]["installed_power"]["value"] == "15000"
    assert (await client.get("/api/v1/projects?archived=true")).json() == []


async def test_security_headers_and_oversized_body(client):
    response = await client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"
    response = await client.post("/api/v1/calculations/full", content=b" " * (4194304 + 1))
    assert response.status_code == 413
    assert "Traceback" not in response.text


async def test_five_projects_remain_independent_after_edit_duplicate_delete_and_new_session(
    client, payload
):
    import copy

    projects = []
    for number in range(5):
        data = copy.deepcopy(payload)
        data["name"] = f"Casa independente {number}"
        data["environments"][0]["loads"][0]["unit_power_w"] = str(1000 + number * 100)
        response = await client.post("/api/v1/projects", json=data)
        assert response.status_code == 201
        projects.append(response.json())
    ids = {item["id"] for item in projects}
    assert len(ids) == 5
    assert {item["id"] for item in (await client.get("/api/v1/projects")).json()} == ids
    recent = (await client.get("/api/v1/projects?limit=3")).json()
    assert [item["id"] for item in recent] == [item["id"] for item in reversed(projects[-3:])]
    others = (await client.get("/api/v1/projects?limit=3&offset=3")).json()
    assert {item["id"] for item in recent + others} == ids
    assert len((await client.get("/api/v1/projects?q=independente%202")).json()) == 1
    first = projects[0]
    edited = copy.deepcopy(payload)
    edited["name"] = "Casa editada isoladamente"
    edited["environments"][0]["loads"][0]["unit_power_w"] = "7500"
    assert (
        await client.put(f"/api/v1/projects/{first['id']}?expected_version=1", json=edited)
    ).status_code == 200
    for original in projects[1:]:
        reopened = (await client.get(f"/api/v1/projects/{original['id']}")).json()
        assert reopened == original
    duplicated = (await client.post(f"/api/v1/projects/{projects[2]['id']}/duplicate")).json()
    assert duplicated["id"] not in ids
    assert duplicated["environments"] == projects[2]["environments"]
    assert (
        await client.delete(f"/api/v1/projects/{projects[1]['id']}?expected_version=1")
    ).status_code == 204
    remaining = (await client.get("/api/v1/projects")).json()
    assert {item["id"] for item in remaining} == ids - {projects[1]["id"]} | {duplicated["id"]}
    # Each GET uses a fresh SQLAlchemy session against the same persisted file.
    for item in remaining:
        assert (await client.get(f"/api/v1/projects/{item['id']}")).json() == item
    assert (await client.get("/api/v1/projects?limit=0")).status_code == 422
    assert (await client.get("/api/v1/projects?limit=101")).status_code == 422


async def test_room_recommendations_are_data_not_restrictions(client, payload):
    catalog = (await client.get("/api/v1/equipment")).json()
    shower = next(item for item in catalog if item["id"] == "lorenzetti-advanced-220-7500")
    assert "bathroom" in shower["recommended_environments"]
    assert "bedroom" not in shower["recommended_environments"]
    assert "kitchen" not in shower["recommended_environments"]
    television = next(item for item in catalog if item["equipment_type"] == "television")
    assert "bedroom" in television["recommended_environments"]
    # A professional may still register a shower in a bedroom: no API prohibition.
    payload["environments"][0]["type"] = "bedroom"
    assert (await client.post("/api/v1/projects", json=payload)).status_code == 201


async def test_documented_ac_capacities_are_electrical_inputs_not_thermal_watts(client):
    import copy
    from uuid import uuid4

    catalog = (await client.get("/api/v1/equipment")).json()
    for capacity, watts in [("18000", "1583"), ("24000", "2170"), ("30000", "2430")]:
        ref = next(item for item in catalog if item["id"] == f"midea-ac-{capacity}-xtreme-c")
        assert ref["reference_power_w"] == watts
        assert ref["power_factor"] is None
        assert ref["voltage_v"] == "220"
        assert ref["source_url"].startswith("https://www.midea.com/")
        load = dict(
            name="Ar-condicionado",
            category="Climatização",
            equipment_type="air_conditioner",
            quantity=2,
            unit_power_w=watts,
            voltage_v="220",
            parameters=copy.deepcopy(ref["parameters"]),
            catalog_reference=ref,
        )
        result = (
            await client.post(
                "/api/v1/calculations/full",
                json={
                    "environments": [
                        {"id": str(uuid4()), "name": "Quarto", "type": "bedroom", "loads": [load]}
                    ]
                },
            )
        ).json()
        assert result["installed_power"]["value"] == str(int(watts) * 2)
        assert result["load_results"][0]["unit_current_a"] is None
        assert "normative" not in result


async def test_invalid_save_has_actionable_field_notice(client, payload):
    from uuid import uuid4

    load = payload["environments"][0]["loads"][0]
    load.update(id=str(uuid4()), unit_power_w="0")
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 422
    notice = response.json()["notifications"][0]
    assert notice["target_id"] == f"load.{load['id']}.unit_power_w"
    assert notice["location"] == ["Banheiro", "Chuveiro"]
    assert notice["solution"] and notice["affected_results"]


async def test_permanent_deletion_requires_trash_and_version_and_preserves_others(
    client, payload, database_engine
):
    first = (await client.post("/api/v1/projects", json=payload)).json()
    second = (await client.post("/api/v1/projects", json={**payload, "name": "Outra casa"})).json()
    path = f"/api/v1/projects/{first['id']}"
    assert (await client.delete(path + "/permanent?expected_version=1")).status_code == 409
    assert (await client.delete(path + "?expected_version=1")).status_code == 204
    archived = (await client.get("/api/v1/projects?archived=true")).json()[0]
    assert archived["deleted_at"] is not None
    assert (await client.delete(path + "/permanent?expected_version=1")).status_code == 409
    assert (
        await client.delete(path + f"/permanent?expected_version={archived['version']}")
    ).status_code == 204
    assert (await client.get("/api/v1/projects?archived=true")).json() == []
    from app.database import HistoryRow
    from sqlalchemy import func, select

    with database_engine.connect() as connection:
        assert (
            connection.scalar(
                select(func.count())
                .select_from(HistoryRow)
                .where(HistoryRow.project_id == first["id"])
            )
            == 0
        )
    assert (
        await client.post(path + f"/restore?expected_version={archived['version']}")
    ).status_code == 404
    assert (await client.get(f"/api/v1/projects/{second['id']}")).json() == second
    assert len((await client.get(f"/api/v1/projects/{second['id']}/history")).json()) == 1


async def test_computer_manual_adopted_power_is_not_a_catalog_violation(client):
    from app.catalog import CATALOG

    ref = next(item for item in CATALOG if item["id"] == "enel-computer")
    payload = dict(
        name="Computador manual",
        municipality="Cidade",
        environments=[
            dict(
                name="Escritório",
                type="office",
                loads=[
                    dict(
                        name="Computador",
                        category="Outros",
                        equipment_type="appliance",
                        unit_power_w="600",
                        quantity=2,
                        power_user_edited=True,
                        voltage_v="220",
                        power_factor="0.8",
                        parameters={"configuration": "single_phase"},
                        catalog_reference=ref,
                    )
                ],
            )
        ],
    )
    before = (await client.get("/api/v1/equipment/enel-computer")).json()
    created = (await client.post("/api/v1/projects", json=payload)).json()
    report = (await client.get(f"/api/v1/projects/{created['id']}/report")).json()
    result = report["calculation"]
    assert result["installed_power"]["value"] == "1200"
    assert result["apparent_power"]["value"] == "1500"
    assert result["memory"][0]["inputs"]["unit_power_w"] == "600"
    assert not any(
        n["category"] == "error" or n["id"].endswith((".estimate", ".manual"))
        for n in result["notifications"]
    )
    assert created["environments"][0]["loads"][0]["unit_power_w"] == "600"
    assert (await client.get("/api/v1/equipment/enel-computer")).json() == before
    from app.reports.pdf import render_report
    from tests.test_pdf import extract_pages

    text = "\n".join(extract_pages(render_report(report["project"], result)))
    assert "1200 W" in text


async def test_api_manual_recalculation_preserves_reference_and_saves_current_values(client):
    import copy
    from decimal import Decimal

    ref = (await client.get("/api/v1/equipment/philips-led-929001195311")).json()
    data = dict(
        name="Revisão API",
        municipality="Cidade",
        environments=[
            dict(
                name="Sala",
                loads=[
                    dict(
                        name="LED",
                        equipment_type="lighting",
                        technology=ref["technology"],
                        category=ref["category"],
                        unit_power_w=ref["reference_power_w"],
                        power_factor=ref["power_factor"],
                        voltage_v="200",
                        quantity=4,
                        parameters={"configuration": "single_phase"},
                        catalog_reference=copy.deepcopy(ref),
                    )
                ],
            )
        ],
    )
    for route in ("loads", "full"):
        result = (await client.post(f"/api/v1/calculations/{route}", json=data)).json()
        assert result["installed_power"]["value"] == "36"
        assert result["lighting_nominal"]["value"] == "36"
        assert "normative" not in result
    load = data["environments"][0]["loads"][0]
    load.update(
        unit_power_w="12.345678",
        quantity=3,
        power_factor="0.75",
        voltage_v="100",
        power_user_edited=True,
    )
    result = (await client.post("/api/v1/calculations/full", json=data)).json()
    assert result["installed_power"]["value"] == "37.037034"
    assert result["installed_power_kw"]["value"] == "0.037037034"
    assert result["apparent_power"]["value"] == "49.382712"
    assert Decimal(result["load_results"][0]["unit_current_a"]) == Decimal("0.16460904")
    saved = (await client.post("/api/v1/projects", json=data)).json()
    actual = saved["environments"][0]["loads"][0]
    assert actual["unit_power_w"] == "12.345678"
    assert actual["power_user_edited"] and actual["manual_override"]
    assert actual["catalog_reference"]["reference_power_w"] == "9"
    assert (await client.get("/api/v1/equipment/philips-led-929001195311")).json() == ref
    load["unit_power_w"] = None
    missing = (await client.post("/api/v1/calculations/full", json=data)).json()
    assert missing["installed_power"]["status"] == "pending"
    assert missing["apparent_power"] is None
    assert missing["load_results"][0]["unit_current_a"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("quantity", 0),
        ("quantity", -1),
        ("quantity", 1.5),
        ("quantity", True),
        ("quantity", 100001),
        ("unit_power_w", "-0.000001"),
        ("unit_power_w", "NaN"),
        ("unit_power_w", "Infinity"),
        ("unit_power_w", "0.0000001"),
        ("unit_power_w", "1000000000000.000001"),
        ("voltage_v", "0"),
        ("voltage_v", "-1"),
        ("power_factor", "0"),
        ("power_factor", "1.000001"),
        ("power_factor", "NaN"),
    ],
)
async def test_api_rejects_invalid_manual_fields_without_using_old_values(
    client, payload, field, value
):
    payload["environments"][0]["loads"][0][field] = value
    response = await client.post("/api/v1/calculations/full", json=payload)
    assert response.status_code == 422
    assert "installed_power" not in response.json()
    assert response.json()["notifications"]


async def test_energy_persistence_recalculation_and_invalid_schedule(client, payload):
    payload["energy_tariff_brl_per_kwh"] = "0.8"
    load = payload["environments"][0]["loads"][0]
    load["parameters"] = dict(usage_hours_per_day="0.5", usage_days_per_month=30)
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    result = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert result["monthly_energy"]["value"] == "225.0"
    assert result["monthly_cost"]["value"] == "180.00"
    history = (await client.get(f"/api/v1/projects/{saved['id']}/history")).json()
    assert history[0]["result"]["monthly_cost"]["value"] == "180.00"
    assert (await client.get(f"/api/v1/projects/{saved['id']}")).json()[
        "energy_tariff_brl_per_kwh"
    ] == "0.8"
    payload["energy_tariff_brl_per_kwh"] = "1.2"
    newer = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert newer["input_digest"] != result["input_digest"]
    assert newer["monthly_cost"]["value"] == "270.00"
    load["parameters"]["usage_hours_per_day"] = "25"
    invalid = await client.post("/api/v1/calculations/full", json=payload)
    assert invalid.status_code == 422
    assert any(
        item["target_id"].endswith("parameters.usage_hours_per_day")
        for item in invalid.json()["notifications"]
    )


@pytest.fixture
def energisa_payload():
    return dict(
        utility="energisa_sul_sudeste",
        state="SP",
        unit_type="individual_residential",
        inventory_reviewed=True,
        has_signage_or_display_lighting=False,
        simultaneous_lighting_outlets=False,
        loads=[
            dict(name="Iluminação/TUG", group="d1", quantity=1, unit_power_w="1000"),
            dict(name="Chuveiro manual", group="d2", quantity=1, unit_power_w="5500"),
        ],
        confirmed_absent_groups=["d3", "d4", "d5", "d6", "d7"],
    )


async def test_json_report_recalculates_and_guards_snapshot_without_saving(client, payload):
    payload["utility"] = "energisa_sul_sudeste"
    payload["energy_tariff_brl_per_kwh"] = "0.8"
    payload["environments"][0]["loads"][0]["parameters"] = dict(
        usage_hours_per_day="1", usage_days_per_month=30
    )
    from app.schemas import CalculationInput

    payload = CalculationInput.model_validate(payload).model_dump(mode="json")
    calculated = (await client.post("/api/v1/calculations/full", json=payload)).json()
    body = dict(
        project=payload,
        expected_input_digest=calculated["input_digest"],
        expected_registry_version=calculated["technical_context"]["registry_version"],
        expected_engine_version=calculated["engine_version"],
    )
    response = await client.post("/api/v1/reports/json", json=body)
    assert response.status_code == 200
    report = response.json()
    assert response.text.startswith('{\n  "formato_versao"')
    assert report["resultados"]["consumo_mensal"]["valor"] == "450"
    assert report["resultados"]["custo_mensal_estimado"]["valor"] == "360.0"
    assert report["projeto"]["nome"] == payload["name"]
    assert report["emissao"]["fuso"] == "America/Sao_Paulo"
    assert report["equipamentos"][0]["quantidade"] == 2
    assert "previsoes_normativas" not in report
    assert "source_url" not in response.text and "aggregate_steps" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert "Casa%20teste.json" in response.headers["content-disposition"]
    assert (await client.get("/api/v1/projects")).json() == []
    for key in ("expected_input_digest", "expected_registry_version", "expected_engine_version"):
        changed = {**body, key: "b" * 64 if key != "expected_engine_version" else "old"}
        assert (await client.post("/api/v1/reports/json", json=changed)).status_code == 409
    body["project"]["environments"][0]["loads"][0]["quantity"] = 3
    assert (await client.post("/api/v1/reports/json", json=body)).status_code == 409


async def test_lightweight_summary_search_trash_and_full_open(client, payload):
    payload["notes"] = "Detalhe privado do projeto " * 200
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    full = await client.get("/api/v1/projects")
    response = await client.get("/api/v1/projects/summaries?limit=21")
    assert response.status_code == 200
    summary = response.json()[0]
    assert summary["id"] == saved["id"] and summary["name"] == saved["name"]
    assert "environments" not in summary and "notes" not in summary
    by_city = (
        await client.get("/api/v1/projects/summaries", params={"q": payload["municipality"]})
    ).json()
    assert by_city[0]["id"] == saved["id"]
    assert len(response.content) < len(full.content) / 5
    assert (await client.get("/api/v1/projects/summaries?q=does-not-exist")).json() == []
    assert (await client.get("/api/v1/projects/summaries?q=%25")).json() == []
    await client.delete(f"/api/v1/projects/{saved['id']}?expected_version=1")
    assert (await client.get("/api/v1/projects/summaries")).json() == []
    trash = (await client.get("/api/v1/projects/summaries?archived=true")).json()
    assert trash[0]["id"] == saved["id"] and trash[0]["deleted_at"]


async def test_unchanged_put_has_no_new_history_or_version_and_stale_still_conflicts(
    client, payload
):
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    repeat = (
        await client.put(f"/api/v1/projects/{saved['id']}?expected_version=1", json=payload)
    ).json()
    assert repeat["version"] == 1 and repeat["updated_at"] == saved["updated_at"]
    assert len((await client.get(f"/api/v1/projects/{saved['id']}/history")).json()) == 1
    changed = {**payload, "notes": "Nota nova"}
    update = await client.put(f"/api/v1/projects/{saved['id']}?expected_version=1", json=changed)
    assert update.json()["version"] == 2
    stale = await client.put(f"/api/v1/projects/{saved['id']}?expected_version=1", json=changed)
    assert stale.status_code == 409
    assert len((await client.get(f"/api/v1/projects/{saved['id']}/history")).json()) == 2


async def test_first_save_retry_is_idempotent_without_overwriting_newer_input(client, payload):
    from uuid import uuid4

    headers = {"Idempotency-Key": str(uuid4())}
    first = await client.post("/api/v1/projects", json=payload, headers=headers)
    repeat = await client.post("/api/v1/projects", json=payload, headers=headers)
    assert first.status_code == repeat.status_code == 201
    assert first.json()["id"] == repeat.json()["id"] == headers["Idempotency-Key"]
    assert len((await client.get("/api/v1/projects")).json()) == 1
    assert len((await client.get(f"/api/v1/projects/{first.json()['id']}/history")).json()) == 1
    conflict = await client.post(
        "/api/v1/projects", json={**payload, "notes": "Edição após queda"}, headers=headers
    )
    assert conflict.status_code == 409
    assert (await client.get(f"/api/v1/projects/{first.json()['id']}")).json()["notes"] == ""
    invalid = await client.post(
        "/api/v1/projects", json=payload, headers={"Idempotency-Key": "invalid"}
    )
    assert invalid.status_code == 422


async def test_territory_api_validates_coordinate_limits_and_no_snapshot(client, monkeypatch):
    from app import territory

    monkeypatch.setattr(territory, "snapshot", lambda: None)
    result = await client.get("/api/v1/locations/territory?latitude=-23.55&longitude=-46.63")
    assert result.status_code == 200 and result.json()["automatic_assignment"] is False
    for query in [
        "latitude=91&longitude=0",
        "latitude=0&longitude=-181",
        "latitude=NaN&longitude=0",
    ]:
        assert (await client.get("/api/v1/locations/territory?" + query)).status_code == 422


async def test_estimates_save_export_without_normative_registry(client, monkeypatch):
    from app import technical

    def obsolete(*args, **kwargs):
        raise AssertionError("Normative registry must not be accessed")

    monkeypatch.setattr(technical, "registry_version", obsolete)
    monkeypatch.setattr(technical, "snapshot", obsolete)
    data = dict(
        name="Kitnet planejada",
        property_stage="planned",
        residence_type="Kitnet",
        environments=[
            dict(
                name="Escritório",
                loads=[
                    dict(
                        name="Computador",
                        quantity=1,
                        unit_power_w="600",
                        parameters=dict(usage_hours_per_day="4", usage_days_per_month=20),
                    )
                ],
            )
        ],
    )
    from app.schemas import CalculationInput

    data = CalculationInput.model_validate(data).model_dump(mode="json")
    calculation = (await client.post("/api/v1/calculations/full", json=data)).json()
    assert calculation["monthly_energy"]["value"] == "48"
    saved = (await client.post("/api/v1/projects", json=data)).json()
    assert saved["id"]
    report = dict(
        project=data,
        expected_input_digest=calculation["input_digest"],
        expected_engine_version=calculation["engine_version"],
        expected_registry_version=calculation["technical_context"]["registry_version"],
    )
    for kind in ("json", "pdf"):
        response = await client.post("/api/v1/reports/" + kind, json=report)
        assert response.status_code == 200
    comparison = await client.post(
        "/api/v1/calculations/compare", json={"baseline": data, "scenario": data}
    )
    assert comparison.status_code == 200
    assert comparison.json()["differences"]["monthly_energy"]["value"] == "0"
    for path in (
        "/technical/rules",
        "/technical/applicability",
        "/technical/documents",
        "/standards",
        "/projects/" + saved["id"] + "/revalidation",
    ):
        assert (await client.get("/api/v1" + path)).status_code == 404
    assert (await client.post("/api/v1/calculations/energisa-demand", json={})).status_code == 404


async def test_old_project_keeps_manual_values_and_archived_studies_on_open_edit_and_export(
    client, payload
):
    import copy

    payload.update(
        analysis_scope="normative",
        circuits=[dict(id="old", name="Estudo anterior", length_m="20")],
        energisa_demand=dict(enabled=True),
        service_entry=dict(scope_confirmed=True),
    )
    payload["environments"][0]["loads"][0]["unit_power_w"] = "600"
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    original = copy.deepcopy(saved)
    reopened = (await client.get("/api/v1/projects/" + saved["id"])).json()
    assert reopened == original
    inputs = {
        k: v
        for k, v in reopened.items()
        if k not in ("id", "version", "created_at", "updated_at", "standards_version", "deleted_at")
    }
    energy_only = {
        k: v for k, v in inputs.items() if k not in ("circuits", "service_entry", "energisa_demand")
    }
    energy_only["analysis_scope"] = "installed"
    calculation = (await client.post("/api/v1/calculations/full", json=energy_only)).json()
    export = dict(
        project=inputs,
        saved_project_id=saved["id"],
        saved_project_version=1,
        expected_input_digest=calculation["input_digest"],
        expected_registry_version=calculation["technical_context"]["registry_version"],
        expected_engine_version=calculation["engine_version"],
    )
    assert (await client.post("/api/v1/reports/json", json=export)).status_code == 200
    inputs["environments"][0]["loads"][0]["unit_power_w"] = "650"
    updated = (
        await client.put(f"/api/v1/projects/{saved['id']}?expected_version=1", json=inputs)
    ).json()
    assert updated["circuits"] == original["circuits"]
    assert updated["service_entry"] == original["service_entry"]
    assert updated["energisa_demand"] == original["energisa_demand"]
    history = (await client.get(f"/api/v1/projects/{saved['id']}/history")).json()
    assert [item["version"] for item in history] == [2, 1]
    assert history[-1]["inputs"]["environments"][0]["loads"][0]["unit_power_w"] == "600"


async def test_opaque_legacy_study_without_id_can_be_saved_twice(client):
    data = dict(name="Estudo legado preservado", circuits=[{"annotation": "sem identidade"}])
    created = await client.post("/api/v1/projects", json=data)
    assert created.status_code == 201
    saved = created.json()
    response = await client.put(f"/api/v1/projects/{saved['id']}?expected_version=1", json=data)
    assert response.status_code == 200
    assert response.json()["version"] == 1
    assert response.json()["circuits"] == data["circuits"]


@pytest.mark.parametrize(
    "field",
    ["circuits", "service_entry", "energisa_demand", "bathroom_geometry", "load_classification"],
)
async def test_nonfinite_opaque_metadata_is_rejected_before_persistence(client, field):
    import json

    data = {
        "name": "Dados inválidos",
        "environments": [{"name": "Sala", "loads": [{"name": "TV", "unit_power_w": "100"}]}],
    }
    opaque = {"annotation": [float("nan")]}
    if field == "circuits":
        data[field] = [opaque]
    elif field == "bathroom_geometry":
        data["environments"][0][field] = opaque
    elif field == "load_classification":
        data["environments"][0]["loads"][0]["energisa_demand"] = opaque
    else:
        data[field] = opaque
    response = await client.post(
        "/api/v1/projects", content=json.dumps(data), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert (await client.get("/api/v1/projects")).json() == []


async def test_empty_delete_all_and_new_project_cycle_preserves_catalog_and_revision_archive(
    client,
):
    assert (await client.get("/api/v1/projects")).json() == []
    catalog = (await client.get("/api/v1/equipment")).json()
    for index in range(3):
        saved = (await client.post("/api/v1/projects", json={"name": f"Temporário {index}"})).json()
        moved = await client.delete(f"/api/v1/projects/{saved['id']}?expected_version=1")
        assert moved.status_code == 204
        deleted = (await client.get("/api/v1/projects?archived=true")).json()
        row = next(item for item in deleted if item["id"] == saved["id"])
        assert (
            await client.delete(
                f"/api/v1/projects/{saved['id']}/permanent?expected_version={row['version']}"
            )
        ).status_code == 204
    assert (await client.get("/api/v1/projects")).json() == []
    assert (await client.get("/api/v1/projects?archived=true")).json() == []
    assert (await client.get("/api/v1/equipment")).json() == catalog
    assert len((await client.get("/api/v1/technical/revisions")).json()) == 1
    fresh = (
        await client.post(
            "/api/v1/projects", json={"name": "Recomeço planejado", "property_stage": "planned"}
        )
    ).json()
    assert fresh["version"] == 1 and fresh["environments"] == []
    assert len((await client.get(f"/api/v1/projects/{fresh['id']}/history")).json()) == 1
