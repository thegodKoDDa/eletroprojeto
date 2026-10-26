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
    assert data["normative"]["demand"]["value"] is None


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
    assert after["normative"]["demand"]["value"] is None
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
    assert result["normative"]["demand"]["value"] is None


async def test_regional_rules_never_fall_back_to_energisa(client, payload):
    for utility in (
        "cpfl_paulista",
        "cpfl_piratininga",
        "cpfl_santa_cruz",
        "enel_sp",
        "edp_sp",
        "neoenergia_elektro",
        "unconfirmed",
    ):
        result = (
            await client.post("/api/v1/calculations/full", json={**payload, "utility": utility})
        ).json()
        assert result["normative"]["demand"]["value"] is None
        assert "NDU-001" not in str(result["normative"]["demand"])
        assert result["technical_context"]["utility"] == utility
    result = (
        await client.post(
            "/api/v1/calculations/full",
            json={**payload, "utility": "energisa_sul_sudeste", "state": "MG"},
        )
    ).json()
    assert result["technical_context"]["status"] == "out_of_scope"
    assert "NDU-001" not in str(result["normative"]["demand"])


async def test_registry_and_revalidation_preserve_manual_values(client, payload):
    created = (await client.post("/api/v1/projects", json=payload)).json()
    pid = created["id"]
    assert created["version"] == 1
    comparison = (await client.get(f"/api/v1/projects/{pid}/revalidation")).json()
    assert comparison["requires_revalidation"] is False
    assert comparison["current_result"]["installed_power"]["value"] == "15000"
    revisions = (await client.get("/api/v1/technical/revisions")).json()
    assert len(revisions) == 1
    snapshot = (await client.get("/api/v1/technical/revisions/" + revisions[0]["id"])).json()
    assert len(snapshot["snapshot"]["equipment"]) == 37
    updated = (await client.post(f"/api/v1/projects/{pid}/recalculate?expected_version=1")).json()
    assert updated["version"] == 2
    assert updated["environments"] == created["environments"]
    assert (
        await client.post(f"/api/v1/projects/{pid}/recalculate?expected_version=1")
    ).status_code == 409
    history = (await client.get(f"/api/v1/projects/{pid}/history")).json()
    assert len(history) == 2
    assert history[0]["version"] == 2
    assert history[1]["version"] == 1
    copy = (await client.post(f"/api/v1/projects/{pid}/duplicate")).json()
    assert copy["id"] != pid
    assert copy["environments"] == created["environments"]


async def test_territorial_candidates_do_not_claim_municipality_coverage(client):
    candidates = (await client.get("/api/v1/utilities?state=SP&municipality=Desconhecido")).json()
    assert len(candidates) == 7
    assert all(item["municipality_mapping"] == "unverified" for item in candidates)
    assert (await client.get("/api/v1/utilities?state=MG")).json() == []
    assert len((await client.get("/api/v1/locations/states")).json()) == 27
    assert (await client.get("/api/v1/technical/integrity")).json()["structural_integrity"] is True


async def test_registry_change_detected_without_modifying_project(client, payload, monkeypatch):
    from app import technical

    created = (await client.post("/api/v1/projects", json=payload)).json()
    old_documents = technical.DOCUMENTS
    monkeypatch.setattr(
        technical, "DOCUMENTS", [*old_documents, dict(id="test_update", title="Unpublished test")]
    )
    result = (await client.get(f"/api/v1/projects/{created['id']}/revalidation")).json()
    assert result["requires_revalidation"] is True
    unchanged = (await client.get(f"/api/v1/projects/{created['id']}")).json()
    assert unchanged == created


async def test_reference_lookup_search_and_rules(client):
    items = (await client.get("/api/v1/equipment?q=Chuveiro")).json()
    assert items
    for item in items:
        assert (await client.get("/api/v1/equipment/" + item["id"])).json() == item
    assert (await client.get("/api/v1/equipment/missing")).status_code == 404
    rules = (await client.get("/api/v1/technical/rules")).json()
    assert all(rule["normative"] is False for rule in rules["mathematical"])
    assert {rule["code"]: rule["status"] for rule in rules["normative"]} == {
        "lighting": "calculated",
        "outlets": "calculated",
        "demand": "estimated",
    }
    documents = (await client.get("/api/v1/technical/documents")).json()
    ndu = next(doc for doc in documents["documents"] if doc["id"] == "ndu001")
    assert ndu["edition"] == "7.0"
    assert ndu["effective_date"] == "2024-11-01"
    assert ndu["status"] != "rules_validated"


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
    assert result["normative"]["demand"]["value"] is None


async def test_missing_room_dimensions_do_not_block_known_power(client, payload):
    payload["analysis_scope"] = "normative"
    room = payload["environments"][0]
    room["area_m2"] = room["perimeter_m"] = None
    response = await client.post("/api/v1/calculations/full", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["installed_power"]["value"] == "15000"
    assert data["installed_power"]["status"] == "calculated"
    assert {issue["field"] for issue in data["field_issues"]} == {"environment.area_m2"}
    assert len(data["normative_capabilities"]) == 3
    assert sum(item["available"] for item in data["normative_capabilities"]) == 2
    assert data["normative"]["lighting"]["value"] is None
    assert data["normative"]["outlets"]["value"] == "600"  # bathroom needs no perimeter
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
    assert {
        "load.unit_power_w",
        "load.voltage_v",
        "load.power_factor",
        "load.parameters.configuration",
    } <= before
    load.update(
        unit_power_w="7500",
        voltage_v="220",
        power_factor="1",
        parameters={"configuration": "single_phase"},
    )
    after, result = await issues()
    assert not after
    assert result["load_results"][0]["unit_current_a"].startswith("34.090909")
    assert result["normative"]["demand"]["value"] is None  # filling fields never validates a rule
    load["voltage_v"] = None
    again, result = await issues()
    assert again == {"load.voltage_v"}
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
async def test_report_guards_include_circuits_protections_and_entry(
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
    assert (await client.post(f"/api/v1/reports/{format}", json=request)).status_code == 409


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
    comparison = (await client.get(f"/api/v1/projects/{created['id']}/revalidation")).json()
    assert comparison["project_id"] == created["id"]
    assert comparison["project_version"] == 2
    assert comparison["previous_engine_version"] == comparison["current_result"]["engine_version"]
    assert comparison["previous_result"]["installed_power"]["value"] == "11000"
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
    voltage = next(
        item
        for item in current["notifications"]
        if item.get("target_id", "").endswith(".voltage_v")
    )
    assert voltage["location"] == ["Banheiro", "Chuveiro"]
    assert voltage["solution"] and voltage["affected_results"] == ["corrente"]
    assert current["installed_power"]["value"] == "15000"
    assert len({item["id"] for item in current["notifications"]}) == len(current["notifications"])
    assert not any(item["category"] == "normative" for item in current["notifications"])
    assert not any(item["target_id"] == "project.utility" for item in current["notifications"])
    assert len(current["normative_capabilities"]) == 3


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
    assert final["normative"]["demand"]["value"] is None
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
        assert result["normative"]["demand"]["value"] is None


async def test_demand_input_pending_and_unverified_rule_are_different_states(client, payload):
    payload["utility"] = "unconfirmed"
    missing = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert missing["normative"]["demand"]["status"] == "pending"
    assert not any(n["target_id"] == "project.utility" for n in missing["notifications"])
    payload["utility"] = "energisa_sul_sudeste"
    known = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert known["normative"]["demand"]["status"] == "pending"
    assert known["normative"]["demand"]["value"] is None
    rule = next(n for n in known["normative_capabilities"] if n["code"] == "demand")
    assert rule["available"]
    assert "9.1" in rule["reason"]
    assert any("Energisa" in item["title"] for item in rule["evidence"])
    assert known["installed_power"]["value"] == missing["installed_power"]["value"] == "15000"


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
    for route in ("loads", "demand", "full"):
        result = (await client.post(f"/api/v1/calculations/{route}", json=data)).json()
        assert result["installed_power"]["value"] == "36"
        assert result["lighting_nominal"]["value"] == "36"
        assert all(item["value"] is None for item in result["normative"].values())
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


async def test_research_is_exposed_as_coverage_not_as_project_errors(client, payload):
    payload["utility"] = "energisa_sul_sudeste"
    calculated = (await client.post("/api/v1/calculations/full", json=payload)).json()
    registry = (
        await client.get("/api/v1/technical/rules?utility=energisa_sul_sudeste&state=SP")
    ).json()
    assert registry["registry_version"] == calculated["technical_context"]["registry_version"]
    assert registry["coverage"] == calculated["normative_capabilities"]
    assert {item["code"] for item in registry["coverage"]} == {"lighting", "outlets", "demand"}
    assert not any(n["category"] == "normative" for n in calculated["notifications"])
    assert not any(n["target_id"] == "project.utility" for n in calculated["notifications"])
    for item in registry["coverage"]:
        assert item["available"] is True
        assert item["label"] and item["purpose"] and item["reason"]
        assert bool(item["pending_checks"]) is (item["code"] == "demand")
        assert item["evidence"]
        for evidence in item["evidence"]:
            assert evidence["url"].startswith("https://")
            assert evidence["consulted_on"] == (
                "2026-10-26" if evidence["access"] == "user_supplied_full_text" else "2026-10-22"
            )
            assert evidence["access"] in (
                "official_index",
                "user_supplied_full_text",
                "official_metadata",
                "institutional_full_text",
                "official_full_text",
            )
        assert calculated["normative"][item["code"]]["value"] is None
    demand = next(item for item in registry["coverage"] if item["code"] == "demand")
    assert any("9.1" in (e["section"] or "") for e in demand["evidence"])
    assert all(
        bool(rule["procedure"]) == bool(rule["tests"]) is True for rule in registry["normative"]
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


async def test_energisa_endpoint_has_traceable_method_and_preserves_project_flow(
    client, energisa_payload, payload
):
    from decimal import Decimal, localcontext

    response = await client.post("/api/v1/calculations/energisa-demand", json=energisa_payload)
    assert response.status_code == 200, response.text
    data = response.json()
    with localcontext() as context:
        context.prec = 40
        assert Decimal(data["value"]) == Decimal("6.36") / Decimal(".92")
    assert data["status"] == "estimated" and data["unit"] == "kVA"
    assert (
        data["reference"]["sha256"]
        == "940b4aab66afc741e2f1f20d88ef2630672dcac2499928af31d807ac8d7442e2"
    )
    assert data["reference"]["access"] == "user_supplied_full_text"
    assert (await client.get("/api/v1/projects")).json() == []
    registry = (
        await client.get("/api/v1/technical/rules?utility=energisa_sul_sudeste&state=SP")
    ).json()
    assert registry["regional_methods"][0]["endpoint"].endswith("/calculations/energisa-demand")
    payload["utility"] = "energisa_sul_sudeste"
    normal = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert (
        normal["normative"]["demand"]["value"] is None
    )  # no guessed classification of old projects


@pytest.mark.parametrize(
    "change", ["missing_power", "missing_absence", "review", "central", "motor", "foreign_utility"]
)
async def test_energisa_endpoint_pending_and_scope(client, energisa_payload, change):
    if change == "missing_power":
        energisa_payload["loads"][1]["unit_power_w"] = None
    elif change == "missing_absence":
        energisa_payload["confirmed_absent_groups"] = []
    elif change == "review":
        energisa_payload["inventory_reviewed"] = False
    elif change == "foreign_utility":
        energisa_payload["utility"] = "enel_sp"
    else:
        group = "d5" if change == "central" else "d6"
        energisa_payload["confirmed_absent_groups"].remove(group)
        energisa_payload["loads"].append(
            dict(
                name="Carga adicional",
                group=group,
                quantity=1,
                unit_power_w="1000",
                air_conditioning_type="central_unit",
            )
        )
    response = await client.post("/api/v1/calculations/energisa-demand", json=energisa_payload)
    assert response.status_code == 200
    assert response.json()["value"] is None and response.json()["pending_checks"]


@pytest.mark.parametrize(
    "change",
    ["contradiction", "duplicate_absence", "bool_quantity", "negative", "nan", "missing_scope"],
)
async def test_energisa_endpoint_rejects_bad_inputs(client, energisa_payload, change):
    if change == "contradiction":
        energisa_payload["confirmed_absent_groups"].append("d2")
    elif change == "duplicate_absence":
        energisa_payload["confirmed_absent_groups"].append("d3")
    elif change == "bool_quantity":
        energisa_payload["loads"][1]["quantity"] = True
    elif change == "negative":
        energisa_payload["loads"][1]["unit_power_w"] = "-1"
    elif change == "nan":
        energisa_payload["loads"][1]["unit_power_w"] = "NaN"
    else:
        energisa_payload.pop("unit_type")
    assert (
        await client.post("/api/v1/calculations/energisa-demand", json=energisa_payload)
    ).status_code == 422


@pytest.mark.parametrize(
    "utility,state",
    [
        ("unconfirmed", "SP"),
        ("cpfl_paulista", "SP"),
        ("enel_sp", "SP"),
        ("energisa_sul_sudeste", "RJ"),
    ],
)
async def test_coverage_never_borrows_energisa_research_for_another_scope(client, utility, state):
    registry = (
        await client.get("/api/v1/technical/rules", params=dict(utility=utility, state=state))
    ).json()
    demand = next(item for item in registry["coverage"] if item["code"] == "demand")
    assert demand["available"] is False
    assert "NDU-001" not in str(demand)
    assert "energisa.com.br" not in str(demand)


async def test_research_snapshot_is_versioned_without_mutating_saved_history(client, payload):
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    before = (await client.get(f"/api/v1/projects/{saved['id']}/history")).json()
    registry = (
        await client.get("/api/v1/technical/revisions/" + saved["standards_version"])
    ).json()
    assert all(
        rule["evidence"] and (rule["pending_checks"] or rule["tests"])
        for rule in registry["snapshot"]["rules"]
    )
    preview = (await client.get(f"/api/v1/projects/{saved['id']}/revalidation")).json()
    assert len(preview["current_result"]["normative_capabilities"]) == 3
    assert before == (await client.get(f"/api/v1/projects/{saved['id']}/history")).json()


async def test_residential_api_recalculates_without_rewriting_previous_history(client, payload):
    payload["analysis_scope"] = "normative"
    payload["utility"] = "energisa_sul_sudeste"
    room = payload["environments"][0]
    room.update(type="kitchen", area_m2="9", perimeter_m="12", lighting_points=1, outlets=5)
    saved = (await client.post("/api/v1/projects", json=payload)).json()
    before = (await client.get(f"/api/v1/projects/{saved['id']}/history")).json()
    original = before[0]["result"]
    assert original["normative"]["lighting"]["value"] == "100"
    assert original["normative"]["outlets"]["value"] == "2000"
    assert original["installed_power"]["value"] == "15000"
    assert original["normative_environments"][0]["registered_outlet_points"] == 5
    room.update(area_m2="14", outlets=8)
    current = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert current["normative"]["lighting"]["value"] == "220"
    assert current["normative"]["outlets"]["value"] == "2300"
    assert current["normative"]["demand"]["value"] is None
    assert (await client.get(f"/api/v1/projects/{saved['id']}/history")).json() == before
    assert (await client.get(f"/api/v1/projects/{saved['id']}")).json()["environments"][0][
        "outlets"
    ] == 5


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
    assert report["previsoes_normativas"]["demand"]["valor"] is None
    assert "source_url" not in response.text and "aggregate_steps" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert "Casa%20teste.json" in response.headers["content-disposition"]
    assert (await client.get("/api/v1/projects")).json() == []
    for key in ("expected_input_digest", "expected_registry_version", "expected_engine_version"):
        changed = {**body, key: "b" * 64 if key != "expected_engine_version" else "old"}
        assert (await client.post("/api/v1/reports/json", json=changed)).status_code == 409
    body["project"]["environments"][0]["loads"][0]["quantity"] = 3
    assert (await client.post("/api/v1/reports/json", json=body)).status_code == 409


async def test_project_demand_persistence_exports_and_stale_guard(client, payload):
    from app.schemas import CalculationInput

    payload["utility"] = "energisa_sul_sudeste"
    payload["energisa_demand"] = dict(
        enabled=True,
        unit_type="individual_residential",
        has_signage_or_display_lighting=False,
        confirmed_absent_groups=["d1", "d3", "d4", "d5", "d6", "d7"],
    )
    payload["environments"][0]["loads"][0]["energisa_demand"] = dict(group="d2")
    # Normalize IDs before review exactly as the editor does; unsaved omitted UUIDs
    # intentionally create a new inventory and cannot reuse another review.
    payload = CalculationInput.model_validate(payload).model_dump(mode="json")
    first = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert first["energisa_demand"]["status"] == "pending"
    payload["energisa_demand"]["reviewed_inventory_digest"] = first["energisa_demand"][
        "inventory_digest"
    ]
    response = await client.post("/api/v1/calculations/full", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["energisa_demand"]["inventory_reviewed"]
    assert result["energisa_demand"]["demanded_power_kw"] == "11.25"
    saved_response = await client.post("/api/v1/projects", json=payload)
    assert saved_response.status_code == 201
    saved = saved_response.json()
    loaded = (await client.get(f"/api/v1/projects/{saved['id']}")).json()
    assert loaded["energisa_demand"] == payload["energisa_demand"]
    export = dict(
        project=payload,
        expected_input_digest=result["input_digest"],
        expected_engine_version=result["engine_version"],
        expected_registry_version=result["technical_context"]["registry_version"],
    )
    report = await client.post("/api/v1/reports/json", json=export)
    assert report.status_code == 200
    summary = report.json()
    assert summary["demanda_revisada"]["value"] == result["energisa_demand"]["value"]
    pdf = await client.post("/api/v1/reports/pdf", json=export)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    payload["environments"][0]["loads"][0]["quantity"] = 3
    changed = (await client.post("/api/v1/calculations/full", json=payload)).json()
    assert not changed["energisa_demand"]["inventory_reviewed"]
    assert changed["normative"]["demand"]["value"] is None
    export["project"] = payload
    rejected = await client.post("/api/v1/reports/json", json=export)
    assert rejected.status_code == 409


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
