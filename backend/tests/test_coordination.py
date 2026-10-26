from copy import deepcopy
from decimal import Decimal as D

import pytest
from app.calculations.coordination import coordination_checks
from app.schemas import CircuitProtectionInput


def example():
    # Synthetic manufacturer/engineering data for independent comparisons only.
    return dict(
        selectivity=dict(
            upstream_device="A",
            downstream_device="B",
            downstream_rated_a="25",
            source="Tabela fictícia revisão1",
            conditions_confirmed=True,
            limit_ka="6",
        ),
        surge=dict(
            device="DPS fictício",
            source="Ficha fictícia revisão1",
            requirements_source="Estudo fictício revisão1",
            conditions_confirmed=True,
            uc_v="275",
            required_uc_v="242",
            effective_up_v="1500",
            withstand_voltage_v="1500",
            discharge_ka="20",
            required_discharge_ka="20",
            waveform="8/20",
            requirement_waveform="8/20",
            short_withstand_ka="6",
        ),
    )


def checks(data, breaker=D(25), short=D("5.99")):
    return {c["code"]: c for c in coordination_checks(data, breaker, short)}


def test_comparisons_and_source_independent_examples():
    data = example()
    before = deepcopy(data)
    result = checks(data)
    assert all(c["passed"] is True for c in result.values())
    assert result["selectivity_short"]["value"] == 6
    assert data == before


@pytest.mark.parametrize(
    "field,value",
    [
        ("prospective_short_circuit_ka", "6"),
        ("prospective_short_circuit_ka", "6.001"),
        ("downstream_rated_a", "32"),
        ("source", None),
        ("conditions_confirmed", False),
    ],
)
def test_selectivity_boundary_and_product_binding(field, value):
    data = example()
    if field == "prospective_short_circuit_ka":
        assert checks(data, short=D(value))["selectivity_short"]["passed"] is False
        return
    data["selectivity"][field] = value
    expected = False if field == "prospective_short_circuit_ka" else None
    assert checks(data)["selectivity_short"]["passed"] is expected


@pytest.mark.parametrize(
    "field,code,value",
    [
        ("uc_v", "spd_uc", "241.999"),
        ("effective_up_v", "spd_up", "1500.001"),
        ("discharge_ka", "spd_discharge", "19.999"),
        ("short_withstand_ka", "spd_short", "5.989"),
    ],
)
def test_spd_independent_failures(field, code, value):
    data = example()
    data["surge"][field] = value
    assert checks(data)[code]["passed"] is False


def test_no_equating_impulse_and_nominal_or_imax():
    data = example()
    data["surge"]["requirement_waveform"] = "10/350"
    assert checks(data)["spd_discharge"]["passed"] is None
    data["surge"]["conditions_confirmed"] = False
    assert all(c["passed"] is None for k, c in checks(data).items() if k.startswith("spd_"))
    assert all(c["passed"] is None for c in checks({}).values())


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "0"])
def test_contract_rejects_invalid_rating(value):
    data = example()
    data["surge"]["uc_v"] = value
    with pytest.raises(ValueError):
        CircuitProtectionInput.model_validate(data)
