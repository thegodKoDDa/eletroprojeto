"""Independent arithmetic examples and boundaries; never normative sizing."""

from copy import deepcopy
from decimal import Decimal as D

import pytest
from app.calculations.energy import energy_cost, monthly_energy, total_energy_kwh
from app.calculations.engine import calculate
from app.schemas import CalculationInput, CalculationResult
from pydantic import ValidationError


def run(loads, tariff=None):
    data = CalculationInput(
        energy_tariff_brl_per_kwh=tariff, environments=[dict(name="Sala", loads=loads)]
    )
    original = deepcopy(data.model_dump(mode="json"))
    result = calculate(original)
    CalculationResult.model_validate(result)
    assert original == data.model_dump(mode="json")
    return result


@pytest.mark.parametrize(
    "watts,hours,days,expected",
    [
        ("40", "5", 30, "6"),
        ("1000", "0.5", 20, "10"),
        ("0.1", "0.1", 31, "0.00031"),
        ("100", "24", 31, "74.4"),
        ("100", "0", 31, "0"),
        ("100", "24", 0, "0"),
    ],
)
def test_constant_power_energy(watts, hours, days, expected):
    assert monthly_energy(D(watts), D(hours), days) == D(expected)


@pytest.mark.parametrize(
    "watts,hours,days",
    [
        ("-1", "1", 30),
        ("NaN", "1", 30),
        ("1", "Infinity", 30),
        ("1", "24.000001", 30),
        ("1", "-1", 30),
        ("1", "1", 32),
        ("1", "1", -1),
        ("1", "1", True),
        ("1", "1", 1.5),
    ],
)
def test_rejects_invalid_energy(watts, hours, days):
    with pytest.raises(ValueError):
        monthly_energy(D(watts), D(hours), days)


@pytest.mark.parametrize(
    "energy,tariff", [("-1", "1"), ("1", "-1"), ("NaN", "1"), ("1", "Infinity")]
)
def test_rejects_invalid_cost(energy, tariff):
    with pytest.raises(ValueError):
        energy_cost(D(energy), D(tariff))


def test_quantity_stated_energy_partial_coverage_and_cost_are_independent_from_watts():
    result = run(
        [
            dict(
                name="LED",
                quantity=4,
                unit_power_w="9",
                parameters=dict(usage_hours_per_day="5", usage_days_per_month=30),
            ),
            dict(name="Geladeira", quantity=2, parameters=dict(monthly_energy_kwh="40")),
            dict(name="Carga sem uso", unit_power_w="100"),
        ],
        "0.8",
    )
    assert result["installed_power"]["value"] == D(136)
    assert result["installed_power"]["status"] == "pending"
    assert result["monthly_energy"] == dict(value=D("85.4"), unit="kWh", status="pending")
    assert result["monthly_cost"]["value"] == D("68.32")
    assert sum(result["energy_by_environment_kwh"].values()) == D("85.4")
    assert sum(result["energy_by_category_kwh"].values()) == D("85.4")
    assert len(result["energy_unknown_load_ids"]) == 1
    assert result["load_results"][1]["electrical_input_w"] is None
    assert result["load_results"][1]["monthly_energy_kwh"] == D(80)
    assert result["load_results"][1]["unit_current_a"] is None


def test_stated_energy_precedes_schedule_and_unknown_is_not_zero():
    result = run(
        [
            dict(
                name="A",
                unit_power_w="1000",
                parameters=dict(
                    monthly_energy_kwh="12", usage_hours_per_day="24", usage_days_per_month=31
                ),
            )
        ]
    )
    assert result["monthly_energy"]["value"] == D(12)
    assert result["monthly_energy"]["status"] == "estimated"
    assert result["load_results"][0]["energy_basis"] == "stated"
    assert result["monthly_cost"] is None
    unknown = run([dict(name="Sem horário", unit_power_w="1000")])
    assert unknown["monthly_energy"] is None
    assert unknown["monthly_cost"] is None
    assert run([])["monthly_energy"] is None


def test_explicit_zero_is_not_missing_and_tariff_changes_digest():
    loads = [
        dict(
            name="Fora de uso",
            unit_power_w="100",
            parameters=dict(usage_hours_per_day="0", usage_days_per_month=30),
        )
    ]
    before, after = run(loads), run(loads, "0")
    assert before["monthly_energy"]["value"] == 0
    assert after["monthly_cost"]["value"] == 0
    assert before["input_digest"] != after["input_digest"]
    assert (
        run([dict(name="Etiqueta", parameters=dict(monthly_energy_kwh="0"))])["monthly_energy"][
            "value"
        ]
        == 0
    )


def test_manual_recalculation_and_motor_energy():
    load = dict(
        name="Motor",
        quantity=2,
        equipment_type="motor",
        parameters=dict(
            power_mode="mechanical",
            mechanical_power="1",
            mechanical_unit="cv",
            efficiency="0.5",
            usage_hours_per_day="2",
            usage_days_per_month=10,
        ),
    )
    before = run([load], "1.25")
    assert before["monthly_energy"]["value"] == D("58.8399")
    assert before["monthly_cost"]["value"] == D("73.549875")
    load["parameters"]["efficiency"] = "1"
    assert run([load])["monthly_energy"]["value"] == D("29.41995")
    load = dict(
        name="Manual",
        unit_power_w="600",
        parameters=dict(usage_hours_per_day="3", usage_days_per_month=20),
    )
    assert run([load])["monthly_energy"]["value"] == 36
    load["unit_power_w"] = "900"
    assert run([load])["monthly_energy"]["value"] == 54


@pytest.mark.parametrize(
    "params",
    [
        dict(usage_hours_per_day="24.000001"),
        dict(usage_hours_per_day="NaN"),
        dict(usage_days_per_month=32),
        dict(usage_days_per_month=True),
        dict(usage_days_per_month=1.5),
        dict(monthly_energy_kwh="-1"),
    ],
)
def test_api_schema_energy_limits(params):
    with pytest.raises(ValidationError):
        CalculationInput(
            environments=[dict(name="Sala", loads=[dict(name="A", parameters=params)])]
        )


@pytest.mark.parametrize("quantity", [0, -1, True, 1.5])
def test_energy_quantity_validation(quantity):
    with pytest.raises(ValueError):
        total_energy_kwh(quantity, D(40))


@pytest.mark.parametrize(
    "parameters",
    [
        {"monthly_energy_kwh": "35"},
        {"monthly_energy_kwh": "0"},
        {"annual_energy_kwh": "420"},
        {"annual_energy_kwh": "0"},
    ],
)
def test_declared_energy_without_power_is_information_not_a_consumption_error(parameters):
    result = run([dict(name="Etiqueta", unit_power_w=None, parameters=parameters)])
    assert result["monthly_energy"] is not None
    power_issue = next(
        item for item in result["notifications"] if item["target_id"].endswith(".unit_power_w")
    )
    assert power_issue["category"] == "info"
    assert "kWh já está disponível" in power_issue["problem"]
    assert result["installed_power"]["status"] == "pending"
