from copy import deepcopy
from decimal import Decimal as D

import pytest
from app.calculations.circuits import calculate_circuits
from test_circuits import setup_circuit


@pytest.mark.parametrize("insulation", ["XLPE90", "EPR90"])
@pytest.mark.parametrize(
    "method,two,three",
    [("A1", 26, 23), ("A2", 25, 22), ("B1", 31, 28), ("B2", 30, 26), ("C", 33, 30), ("E", 36, 32)],
)
def test_independent_25mm2_table_values_and_equal_boundary(insulation, method, two, three):
    for balanced, expected in [(False, two), (True, three)]:
        project, loads = setup_circuit()
        c = project["circuits"][0]
        c.update(
            insulation=insulation,
            method=method,
            terminals_90c_confirmed=True,
            length_m=None,
            breaker_ratings_a=[str(expected)],
        )
        if balanced:
            c["configuration"] = "balanced_three_phase_without_neutral"
            project["environments"][0]["loads"][0]["parameters"]["configuration"] = (
                "balanced_three_phase"
            )
        row = calculate_circuits(project, loads)[0]
        assert row["phase_section_mm2"] == D("2.5")
        assert row["capacity_a"] == expected
        c["breaker_ratings_a"] = [str(D(expected) + D(".000001"))]
        assert calculate_circuits(project, loads)[0]["phase_section_mm2"] == 4


def test_normative_80a_overrides_manual_printing_divergence():
    project, loads = setup_circuit()
    c = project["circuits"][0]
    c.update(
        insulation="XLPE90",
        method="C",
        terminals_90c_confirmed=True,
        breaker_ratings_a=["80"],
        length_m=None,
    )
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] == 10 and row["capacity_a"] == 80
    c["breaker_ratings_a"] = ["80.000001"]
    assert calculate_circuits(project, loads)[0]["phase_section_mm2"] == 16


def test_90c_requires_compatible_terminals_and_own_impedance():
    project, loads = setup_circuit()
    c = project["circuits"][0]
    c.update(insulation="XLPE90")
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] is None
    c["terminals_90c_confirmed"] = True
    row = calculate_circuits(project, loads)[0]
    assert row["voltage_drop_v"] is None
    # User-supplied fictitious data for an independent arithmetic example,
    # not a recommended resistivity/reactance for any real product.
    c.update(
        hot_resistivity_ohm_mm2_m=".025",
        reactance_ohm_m="0",
        impedance_source="Fixture do fabricante fictício",
    )
    original = deepcopy(project)
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] == 4
    assert row["voltage_drop_v"] == D("7.5")  # 2.5mm² gives12V >4%; 4mm² gives7.5V.
    assert project == original


def test_temperature_factor_90c_and_no_extrapolation():
    project, loads = setup_circuit()
    c = project["circuits"][0]
    c.update(
        insulation="EPR90",
        terminals_90c_confirmed=True,
        ambient_temperature_c=40,
        grouped_circuits=2,
        breaker_ratings_a=["25"],
        length_m=None,
    )
    row = calculate_circuits(project, loads)[0]
    assert row["temperature_factor"] == D(".91")
    assert row["phase_section_mm2"] == 4
    assert row["capacity_a"] == D("30.576")  # 42*.91*.8
    c.update(breaker_ratings_a=["1000"])
    assert calculate_circuits(project, loads)[0]["phase_section_mm2"] is None


@pytest.mark.parametrize("value", ["Aluminium", "unknown"])
def test_unknown_insulation_rejected_by_contract(value):
    project, _ = setup_circuit()
    # Validate just the circuit: material isn't a selectable field at all.
    from app.schemas import CircuitInput

    with pytest.raises(ValueError):
        CircuitInput.model_validate({**project["circuits"][0], "insulation": value})


@pytest.mark.parametrize(
    "insulation,method,layout,phase,rating",
    [
        ("PVC70", "D", "unknown", False, 29),
        ("PVC70", "D", "unknown", True, 24),
        ("XLPE90", "D", "unknown", False, 34),
        ("EPR90", "D", "unknown", True, 29),
        ("PVC70", "F", "unknown", False, 31),
        ("PVC70", "F", "trefoil", True, 24),
        ("PVC70", "F", "flat_touching", True, 25),
        ("XLPE90", "F", "unknown", False, 37),
        ("XLPE90", "F", "trefoil", True, 29),
        ("EPR90", "F", "flat_touching", True, 30),
        ("PVC70", "G", "horizontal_spaced", True, 34),
        ("PVC70", "G", "vertical_spaced", True, 29),
        ("XLPE90", "G", "horizontal_spaced", True, 41),
        ("EPR90", "G", "vertical_spaced", True, 35),
    ],
)
def test_other_methods_independent_25mm2_equalities(insulation, method, layout, phase, rating):
    project, loads = setup_circuit()
    c = project["circuits"][0]
    c.update(
        insulation=insulation,
        method=method,
        air_layout=layout,
        terminals_90c_confirmed=True,
        soil_temperature_c=20,
        buried_reference_confirmed=True,
        length_m=None,
        breaker_ratings_a=[str(rating)],
    )
    if phase:
        c["configuration"] = "balanced_three_phase_without_neutral"
        project["environments"][0]["loads"][0]["parameters"]["configuration"] = (
            "balanced_three_phase"
        )
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] == D("2.5") and row["capacity_a"] == rating
    c["breaker_ratings_a"] = [str(D(rating) + D(".000001"))]
    assert calculate_circuits(project, loads)[0]["phase_section_mm2"] == 4


@pytest.mark.parametrize(
    "method,change",
    [
        ("D", {"buried_reference_confirmed": False}),
        ("D", {"soil_temperature_c": None}),
        ("D", {"grouped_circuits": 2}),
        ("F", {"air_layout": "unknown"}),
        ("G", {"air_layout": "trefoil"}),
        ("G", {"grouped_circuits": 2}),
        ("G", {"configuration": "single_phase"}),
    ],
)
def test_invalid_buried_air_geometry_never_dimensioned(method, change):
    project, loads = setup_circuit()
    c = project["circuits"][0]
    c.update(
        method=method,
        configuration="balanced_three_phase_without_neutral",
        soil_temperature_c=20,
        buried_reference_confirmed=True,
        air_layout="horizontal_spaced" if method == "G" else "trefoil",
    )
    project["environments"][0]["loads"][0]["parameters"]["configuration"] = "balanced_three_phase"
    c.update(change)
    assert calculate_circuits(project, loads)[0]["phase_section_mm2"] is None


def test_soil_temperature_distinct_from_air_and_no_conduit_impedance_for_free_air():
    project, loads = setup_circuit()
    c = project["circuits"][0]
    c.update(method="D", soil_temperature_c=30, buried_reference_confirmed=True)
    row = calculate_circuits(project, loads)[0]
    assert row["temperature_factor"] == D(".89")  # Soil30°C, not air30°C=1.
    assert row["voltage_drop_v"] is None
    c.update(method="F")
    assert calculate_circuits(project, loads)[0]["voltage_drop_v"] is None
