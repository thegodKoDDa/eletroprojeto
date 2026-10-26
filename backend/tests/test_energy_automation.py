"""Independent examples, boundaries, precedence and immutable legacy inputs."""

from copy import deepcopy
from decimal import Decimal as D

import pytest
from app.calculations.engine import calculate
from app.reports.summary import build_summary
from app.schemas import CalculationInput, CalculationResult
from pydantic import ValidationError


def run(params, *, quantity=1, power="2000", tariff="0.8", extra=None):
    project = CalculationInput(
        energy_tariff_brl_per_kwh=tariff,
        environments=[
            dict(
                name="Sala",
                loads=[
                    dict(name="A", unit_power_w=power, quantity=quantity, parameters=params),
                    *(extra or []),
                ],
            )
        ],
    ).model_dump(mode="json")
    before = deepcopy(project)
    result = calculate(project)
    CalculationResult.model_validate(result)
    assert project == before
    return result, project


@pytest.mark.parametrize(
    "minutes,days,quantity,expected",
    [
        ("15", 30, 2, "30"),
        ("1", 1, 1, "0.03333333333333333333333333333333333333333"),
        ("0", 31, 1, "0"),
        ("1440", 31, 1, "1488"),
        ("0.000001", 1, 1, "0.00000003333333333333333333333333333333333333333"),
    ],
)
def test_minutes_independent_results(minutes, days, quantity, expected):
    result, _ = run(
        dict(usage_time_unit="minutes", usage_minutes_per_day=minutes, usage_days_per_month=days),
        quantity=quantity,
    )
    assert result["monthly_energy"]["value"] == D(expected)
    assert result["load_results"][0]["energy_basis"] == "schedule"


def test_annual_exact_projection_average_and_cost_without_power_inference():
    result, project = run(dict(annual_energy_kwh="100"), quantity=3, power=None)
    assert result["monthly_energy"]["value"] == 25
    assert result["annual_energy"]["value"] == 300
    assert result["monthly_cost"]["value"] == 20
    assert result["annual_cost"]["value"] == 240
    assert result["unknown_load_ids"]  # Energy does not supply W, VA or current.
    assert result["load_results"][0]["energy_basis"] == "annual_stated"
    summary = build_summary(project, result)
    assert summary["equipamentos"][0]["consumo_anual_unitario_informado_kwh"] == "100"
    assert summary["resultados"]["projecao_consumo_anual"]["valor"] == 300


def test_priority_and_time_unit_never_overwrite_dormant_manual_values():
    params = dict(
        monthly_energy_kwh="0",
        annual_energy_kwh="500",
        usage_hours_per_day="4",
        usage_minutes_per_day="15",
        usage_time_unit="minutes",
        usage_days_per_month=30,
    )
    result, _ = run(params)
    assert result["monthly_energy"]["value"] == 0
    assert all(value is None for value in result["energy_share_by_load_pct"].values())
    params["monthly_energy_kwh"] = None
    assert run(params)[0]["annual_energy"]["value"] == 500
    params["annual_energy_kwh"] = None
    assert run(params)[0]["monthly_energy"]["value"] == 15
    params["usage_time_unit"] = "hours"
    assert run(params)[0]["monthly_energy"]["value"] == 240


def test_partial_empty_zero_tariff_and_annual_rounding_boundaries():
    result, _ = run(
        dict(annual_energy_kwh="1"),
        extra=[dict(name="B", parameters=dict(annual_energy_kwh="2")), dict(name="Unknown")],
        tariff="0",
    )
    assert result["annual_energy"]["value"] == 3
    assert result["annual_energy"]["status"] == "pending"
    assert result["annual_cost"]["value"] == 0
    assert result["energy_known_load_count"] == 2 and result["energy_pending_load_count"] == 1
    assert sum(result["energy_share_by_load_pct"].values()) == D(100)
    assert all(v == 0 for v in result["energy_cost_by_environment_brl"].values())
    assert run({})[0]["annual_energy"] is None
    assert run(dict(annual_energy_kwh="1"), tariff=None)[0]["annual_cost"] is None
    empty = calculate(CalculationInput().model_dump(mode="json"))
    assert empty["monthly_energy"] is None and empty["annual_energy"] is None
    assert empty["energy_known_load_count"] == 0


@pytest.mark.parametrize(
    "params",
    [
        dict(usage_minutes_per_day="1440.000001"),
        dict(usage_minutes_per_day="-1"),
        dict(usage_minutes_per_day="NaN"),
        dict(usage_time_unit="seconds"),
        dict(annual_energy_kwh="-1"),
        dict(annual_energy_kwh="Infinity"),
    ],
)
def test_new_input_boundaries(params):
    with pytest.raises(ValidationError):
        run(params)


def test_missing_selected_duration_remains_pending_even_with_dormant_hours():
    result, _ = run(
        dict(usage_time_unit="minutes", usage_hours_per_day="5", usage_days_per_month=30)
    )
    assert result["monthly_energy"] is None
    assert result["annual_energy"] is None


def test_breakdowns_use_quantities_and_sort_highest_first():
    result, _ = run(
        dict(monthly_energy_kwh="4"),
        quantity=2,
        extra=[dict(name="B", parameters=dict(monthly_energy_kwh="2"))],
    )
    assert result["monthly_energy"]["value"] == 10
    assert list(result["energy_cost_by_environment_brl"].values()) == [D("8")]
    assert sorted(result["energy_share_by_load_pct"].values()) == [20, 80]
    assert result["load_results"][0]["load_id"] == result["energy_ranked_load_ids"][0]


def test_pdf_and_summary_keep_explicit_minutes_annual_inputs_and_projection_limits():
    from app.reports.pdf import render_report
    from test_pdf import extract_pages

    result, project = run(
        dict(
            usage_time_unit="minutes",
            usage_minutes_per_day="15",
            usage_hours_per_day="8",
            usage_days_per_month=20,
        ),
        extra=[dict(name="Label", parameters=dict(annual_energy_kwh="120"))],
    )
    summary = build_summary(project, result)
    assert summary["equipamentos"][0]["minutos_por_dia"] == "15"
    assert summary["equipamentos"][0]["horas_por_dia"] is None
    assert summary["equipamentos"][1]["consumo_anual_unitario_informado_kwh"] == "120"
    assert summary["ambientes"][0]["custo_mensal_brl"] == D("16")
    text = " ".join("\n".join(extract_pages(render_report(project, result))).split())
    assert "15 min/dia" in text and "120 kWh/ano/un." in text
    assert "Projeção de consumo em 12 meses" in text
    assert "Sem sazonalidade" in text
