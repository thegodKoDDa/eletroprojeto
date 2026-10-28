"""Independent consumption examples and isolation from archived installation studies."""

import copy
from decimal import Decimal as D
from unittest.mock import patch

import pytest
from app.calculations.engine import calculate
from app.reports.pdf import render_report
from app.reports.summary import build_summary
from app.schemas import CalculationInput, CalculationResult
from test_pdf import extract_pages


def example(**changes):
    payload = dict(
        name="Moradia",
        state="SP",
        energy_tariff_brl_per_kwh="0.80",
        environments=[
            dict(
                name="Escritório",
                loads=[
                    dict(
                        name="Computador",
                        unit_power_w="600",
                        quantity=2,
                        source="Premissa manual",
                        power_origin="user_estimate",
                        parameters=dict(usage_hours_per_day="4", usage_days_per_month=20),
                    )
                ],
            )
        ],
    )
    payload.update(changes)
    return CalculationInput.model_validate(payload).model_dump(mode="json")


@pytest.mark.parametrize(
    "kind,stage",
    [
        ("Casa", "ready"),
        ("Casa", "planned"),
        ("Apartamento", "construction"),
        ("Kitnet", "renovation"),
        ("Studio", "planned"),
        ("Sobrado", "ready"),
    ],
)
def test_same_consumption_for_every_residential_context(kind, stage):
    result = calculate(example(residence_type=kind, property_stage=stage))
    # Two 600 W computers, four effective hours on twenty days: 96 kWh/month.
    assert result["installed_power"]["value"] == 1200
    assert result["monthly_energy"]["value"] == 96
    assert result["annual_energy"]["value"] == 1152
    assert result["monthly_cost"]["value"] == D("76.8")
    assert result["annual_cost"]["value"] == D("921.6")
    assert abs(result["daily_energy"]["value"] - D("3.156164383561643835616438356")) < D("1e-26")
    assert "normative" not in result
    CalculationResult.model_validate(result)


def test_distributor_and_archived_studies_never_invoke_normative_services():
    data = example()
    baseline = calculate(data)
    with (
        patch("app.technical.applicability", side_effect=AssertionError("normative dependency")),
        patch(
            "app.calculations.project_demand.project_energisa_demand",
            side_effect=AssertionError("demand dependency"),
        ),
        patch(
            "app.calculations.circuits.calculate_circuits",
            side_effect=AssertionError("circuit dependency"),
        ),
    ):
        for utility in ("unconfirmed", "energisa_sul_sudeste", "cpfl_paulista", "enel_sp"):
            for scope in ("installed", "normative", "current"):
                result = calculate(
                    example(
                        utility=utility,
                        analysis_scope=scope,
                        circuits=[dict(id="old", name="Estudo antigo")],
                        energisa_demand=dict(enabled=True),
                    )
                )
                assert result["monthly_energy"] == baseline["monthly_energy"]
                assert result["field_issues"] == []
                assert result.get("energisa_demand") is None
                assert not result.get("circuit_results")


def test_manual_power_and_schedule_recalculate_without_altering_catalog_reference():
    data = example()
    load = data["environments"][0]["loads"][0]
    load["catalog_reference"] = {"reference_power_w": "300"}
    original = copy.deepcopy(data)
    assert calculate(data)["monthly_energy"]["value"] == 96
    load["unit_power_w"] = "300"
    assert calculate(data)["monthly_energy"]["value"] == 48
    load["parameters"]["usage_hours_per_day"] = "2"
    assert calculate(data)["monthly_energy"]["value"] == 24
    assert load["catalog_reference"] == original["environments"][0]["loads"][0]["catalog_reference"]


def test_cyclic_appliance_declared_energy_without_power_or_operational_details():
    data = example()
    load = data["environments"][0]["loads"][0]
    load.update(
        name="Geladeira", quantity=1, unit_power_w=None, parameters={"monthly_energy_kwh": "35"}
    )
    result = calculate(data)
    assert result["monthly_energy"]["value"] == 35
    assert result["annual_energy"]["value"] == 420
    assert result["monthly_cost"]["value"] == 28
    assert result["energy_unknown_load_ids"] == []


def test_reports_are_energy_analysis_without_installation_sections():
    project = example(property_stage="planned", residence_type="Kitnet")
    result = calculate(project)
    summary = build_summary(project, result)
    assert summary["formato_versao"] == "2.0"
    assert summary["projeto"]["estagio_imovel"] == "planned"
    assert summary["resultados"]["consumo_mensal"]["valor"] == 96
    assert summary["memoria_calculo"][0]["steps"]
    assert (
        not {"previsoes_normativas", "atendimento_distribuidora", "circuitos", "entrada_de_energia"}
        & summary.keys()
    )
    text = "\n".join(extract_pages(render_report(project, result)))
    assert "96" in text and "Computador" in text and "Planejado" in text
    for obsolete in (
        "Cobertura normativa",
        "Demanda revisada",
        "Para conversar com a distribuidora",
        "Estudo de circuitos",
    ):
        assert obsolete not in text


def test_scenario_comparison_uses_independent_estimates_and_preserves_inputs():
    from app.calculations.comparison import compare_estimates

    baseline, scenario = example(), example()
    baseline["environments"][0]["loads"][0]["unit_power_w"] = "300"
    original = copy.deepcopy((baseline, scenario))
    comparison = compare_estimates(baseline, scenario)
    assert comparison["differences"]["monthly_energy"]["value"] == 48
    assert comparison["differences"]["monthly_cost"]["value"] == D("38.4")
    assert (baseline, scenario) == original
    scenario["environments"][0]["loads"][0]["parameters"] = {}
    comparison = compare_estimates(baseline, scenario)
    assert comparison["differences"]["monthly_energy"] is None
    assert comparison["differences"]["installed_power"]["value"] == 600
