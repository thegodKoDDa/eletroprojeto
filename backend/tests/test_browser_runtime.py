import base64
import json

from app.browser_runtime import dispatch_request


def test_browser_runtime_resources_and_calculations():
    health = dispatch_request("GET", "/health")
    assert health["status"] == 200
    assert health["body"]["status"] == "ok"

    reqs = dispatch_request("GET", "/validation/requirements")
    assert reqs["status"] == 200
    assert "project.name" in reqs["body"]

    states = dispatch_request("GET", "/locations/states")
    assert states["status"] == 200
    assert "SP" in states["body"]

    utilities = dispatch_request("GET", "/utilities?state=SP")
    assert utilities["status"] == 200
    assert any(u["id"] == "energisa_sul_sudeste" for u in utilities["body"])

    equipment = dispatch_request("GET", "/equipment?q=chuveiro")
    assert equipment["status"] == 200
    assert len(equipment["body"]) >= 1

    rules = dispatch_request("GET", "/technical/rules?utility=energisa_sul_sudeste&state=SP")
    assert rules["status"] == 404

    calc_payload = {
        "name": "Casa Teste",
        "municipality": "Presidente Prudente",
        "state": "SP",
        "utility": "energisa_sul_sudeste",
        "energy_tariff_brl_per_kwh": "0.90",
        "environments": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "name": "Sala",
                "type": "living",
                "lighting_points": 1,
                "outlets": 2,
                "loads": [
                    {
                        "id": "22222222-2222-4222-8222-222222222222",
                        "name": "Lâmpada LED",
                        "category": "Iluminação",
                        "kind": "lighting",
                        "equipment_type": "lighting",
                        "quantity": 2,
                        "unit_power_w": "9",
                        "parameters": {
                            "usage_hours_per_day": "5",
                            "usage_days_per_month": 30,
                        },
                    }
                ],
            }
        ],
    }
    calc = dispatch_request("POST", "/calculations/full", json.dumps(calc_payload))
    assert calc["status"] == 200
    assert calc["body"]["installed_power"]["value"] == "18"
    assert calc["body"]["monthly_energy"]["value"] == "2.70"
    assert calc["body"]["monthly_cost"]["value"] == "2.4300"


def test_browser_runtime_project_crud_and_reports():
    payload = {
        "name": "Residência GitHub Pages",
        "municipality": "Assis",
        "state": "SP",
        "utility": "unconfirmed",
        "energy_tariff_brl_per_kwh": "0.85",
        "environments": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "name": "Cozinha",
                "type": "kitchen",
                "lighting_points": 1,
                "outlets": 3,
                "loads": [
                    {
                        "id": "22222222-2222-4222-8222-222222222222",
                        "name": "Geladeira",
                        "category": "Cozinha",
                        "kind": "specific_use",
                        "equipment_type": "refrigeration",
                        "quantity": 1,
                        "unit_power_w": "120",
                        "parameters": {"monthly_energy_kwh": "35"},
                    }
                ],
            }
        ],
    }
    idem_key = "33333333-3333-4333-8333-333333333333"
    created = dispatch_request(
        "POST",
        "/projects",
        json.dumps(payload),
        headers={"Idempotency-Key": idem_key},
    )
    assert created["status"] == 201
    store_json = created["store_json"]
    assert store_json is not None
    project = created["body"]
    assert project["id"] == idem_key
    assert project["version"] == 1

    # Idempotent retry returns same project
    retry = dispatch_request(
        "POST",
        "/projects",
        json.dumps(payload),
        headers={"Idempotency-Key": idem_key},
        store_json=store_json,
    )
    assert retry["status"] == 201
    assert retry["body"]["id"] == idem_key

    # Summaries and read
    summaries = dispatch_request("GET", "/projects/summaries", store_json=store_json)
    assert summaries["status"] == 200
    assert len(summaries["body"]) == 1
    assert summaries["body"][0]["name"] == "Residência GitHub Pages"

    # Update with wrong version -> 409
    conflict = dispatch_request(
        "PUT",
        f"/projects/{idem_key}?expected_version=2",
        json.dumps({**payload, "name": "Outro"}),
        store_json=store_json,
    )
    assert conflict["status"] == 409

    # Update with right version -> version 2
    updated = dispatch_request(
        "PUT",
        f"/projects/{idem_key}?expected_version=1",
        json.dumps({**payload, "notes": "Atualizado"}),
        store_json=store_json,
    )
    assert updated["status"] == 200
    assert updated["body"]["version"] == 2
    store_json = updated["store_json"]

    # Export PDF and JSON
    calc = dispatch_request(
        "POST", "/calculations/full", json.dumps({**payload, "notes": "Atualizado"})
    )["body"]
    export_req = {
        "project": {**payload, "notes": "Atualizado"},
        "saved_project_id": idem_key,
        "saved_project_version": 2,
        "expected_input_digest": calc["input_digest"],
        "expected_engine_version": calc["engine_version"],
        "expected_registry_version": calc["technical_context"]["registry_version"],
    }
    pdf_resp = dispatch_request(
        "POST", "/reports/pdf", json.dumps(export_req), store_json=store_json
    )
    assert pdf_resp["status"] == 200
    assert pdf_resp["headers"]["Content-Type"] == "application/pdf"
    assert base64.b64decode(pdf_resp["body_base64"]).startswith(b"%PDF-")

    json_resp = dispatch_request(
        "POST", "/reports/json", json.dumps(export_req), store_json=store_json
    )
    assert json_resp["status"] == 200
    parsed_report = json.loads(base64.b64decode(json_resp["body_base64"]).decode("utf-8"))
    assert parsed_report["formato_versao"] == "2.0"

    # Soft delete, restore, permanent delete
    deleted = dispatch_request(
        "DELETE", f"/projects/{idem_key}?expected_version=2", store_json=store_json
    )
    assert deleted["status"] == 204
    store_json = deleted["store_json"]

    restored = dispatch_request(
        "POST", f"/projects/{idem_key}/restore?expected_version=3", store_json=store_json
    )
    assert restored["status"] == 200
    store_json = restored["store_json"]

    deleted2 = dispatch_request(
        "DELETE", f"/projects/{idem_key}?expected_version=4", store_json=store_json
    )
    store_json = deleted2["store_json"]
    purged = dispatch_request(
        "DELETE", f"/projects/{idem_key}/permanent?expected_version=5", store_json=store_json
    )
    assert purged["status"] == 204
    assert (
        dispatch_request(
            "GET", "/projects/summaries?archived=true", store_json=purged["store_json"]
        )["body"]
        == []
    )


def test_browser_runtime_validation_error_notifications():
    bad_payload = {
        "name": "Teste",
        "municipality": "SP",
        "state": "SP",
        "utility": "unconfirmed",
        "environments": [
            {
                "id": "11111111-1111-4111-8111-111111111111",
                "name": "Quarto",
                "type": "bedroom",
                "loads": [
                    {
                        "id": "22222222-2222-4222-8222-222222222222",
                        "name": "Ar",
                        "quantity": 1,
                        "unit_power_w": "-10",
                    }
                ],
            }
        ],
    }
    resp = dispatch_request("POST", "/calculations/full", json.dumps(bad_payload))
    assert resp["status"] == 422
    assert resp["body"]["notifications"][0]["target_id"] == (
        "load.22222222-2222-4222-8222-222222222222.unit_power_w"
    )


def test_browser_scenario_comparison_without_normative_routes():
    from app.schemas import CalculationInput

    data = CalculationInput.model_validate(
        dict(
            environments=[
                dict(
                    name="Sala",
                    loads=[
                        dict(
                            name="TV",
                            unit_power_w="100",
                            parameters=dict(usage_hours_per_day="4", usage_days_per_month=30),
                        )
                    ],
                )
            ]
        )
    ).model_dump(mode="json")
    result = dispatch_request(
        "POST", "/calculations/compare", json.dumps(dict(baseline=data, scenario=data))
    )
    assert result["status"] == 200
    assert result["body"]["differences"]["monthly_energy"]["value"] == "0"
    for path in ("/technical/rules", "/standards"):
        assert dispatch_request("GET", path)["status"] == 404
