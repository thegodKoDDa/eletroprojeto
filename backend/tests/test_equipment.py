"""Independent dimensional examples and fail-closed normative checks."""

from decimal import Decimal as D

import pytest
from app.calculations.engine import calculate
from app.calculations.units import (
    btu_h_to_thermal_w,
    mechanical_to_w,
    motor_input_w,
    va_to_kva,
    wh_to_kwh,
)
from app.catalog import CATALOG
from app.schemas import CatalogItem, Load, ProjectInput
from pydantic import ValidationError


def run(load):
    data = ProjectInput(
        name="Casa",
        municipality="Cidade",
        built_area_m2="60",
        environments=[dict(name="Quarto", area_m2="12", perimeter_m="14", loads=[load])],
    )
    return calculate(data.model_dump(mode="json"))


def test_thermal_capacity_is_not_electrical():
    # NIST SP1038 lists 1 BTU_IT/h ≈ 0.2930711 W; 12k gives ≈3516.8532 W.
    assert abs(btu_h_to_thermal_w(D(12000)) - D("3516.8532")) < D("0.001")
    result = run(
        dict(
            name="Ar-condicionado",
            unit_power_w="1130",
            equipment_type="air_conditioner",
            parameters={"cooling_capacity_btu_h": "12000"},
        )
    )
    assert result["installed_power"]["value"] == D(1130)
    assert result["load_results"][0]["thermal_capacity_w"] > D(3500)
    assert result["load_results"][0]["unit_current_a"] is None


def test_btu_alone_does_not_create_load_power():
    result = run(
        dict(
            name="Ar sem ficha",
            equipment_type="air_conditioner",
            parameters={"cooling_capacity_btu_h": "24000"},
        )
    )
    assert result["installed_power"]["value"] == 0
    assert result["installed_power"]["status"] == "pending"
    assert len(result["unknown_load_ids"]) == 1
    assert result["apparent_power"] is None


def test_mechanical_units_differ():
    assert mechanical_to_w(D(1), "cv") == D("735.49875")
    assert abs(mechanical_to_w(D(1), "hp") - D("745.6999")) < D("0.0001")
    assert motor_input_w(D(1), "cv", D("0.75")) == D("980.665")


def test_motor_uses_electrical_input_not_output():
    result = run(
        dict(
            name="Bomba",
            unit_power_w="10",
            quantity=2,
            equipment_type="motor",
            parameters={
                "power_mode": "mechanical",
                "mechanical_power": "1",
                "mechanical_unit": "cv",
                "efficiency": "0.75",
            },
        )
    )
    assert result["installed_power"]["value"] == D("1961.330")
    assert result["installed_power"]["status"] == "estimated"
    assert result["load_results"][0]["steps"][0]["calculation"] == "motor_input"


def test_missing_motor_efficiency_blocks_result():
    result = run(
        dict(
            name="Motor",
            equipment_type="motor",
            unit_power_w="100",
            parameters={"power_mode": "mechanical", "mechanical_power": "1"},
        )
    )
    assert result["load_results"][0]["electrical_input_w"] is None
    assert result["installed_power"]["status"] == "pending"


@pytest.mark.parametrize("efficiency", ["0", "-1", "1.1", "NaN"])
def test_bad_efficiency(efficiency):
    with pytest.raises(ValueError):
        motor_input_w(D(1), "cv", D(efficiency))


def test_energy_is_not_power():
    result = run(
        dict(
            name="Geladeira",
            unit_power_w="130",
            equipment_type="refrigeration",
            parameters={"monthly_energy_kwh": "30", "maximum_power_w": "500"},
        )
    )
    assert result["installed_power"]["value"] == D(130)
    result = run(
        dict(
            name="Geladeira só com etiqueta de energia",
            equipment_type="refrigeration",
            parameters={"monthly_energy_kwh": "30"},
        )
    )
    assert result["installed_power"]["status"] == "pending"
    assert wh_to_kwh(D(36000)) == D(36)
    assert va_to_kva(D(15040)) == D("15.04")


def test_microwave_uses_input():
    result = run(
        dict(
            name="Micro-ondas",
            unit_power_w="1050",
            equipment_type="microwave",
            parameters={"microwave_output_w": "700"},
        )
    )
    assert result["installed_power"]["value"] == D(1050)


def test_unknown_voltage_is_not_inherited():
    result = run(
        dict(
            name="Carga",
            unit_power_w="2200",
            power_factor="1",
            parameters={"configuration": "single_phase"},
        )
    )
    assert result["load_results"][0]["unit_current_a"] is None


def test_explicit_resistive_assumption_and_current():
    result = run(
        dict(
            name="Chuveiro",
            unit_power_w="7500",
            quantity=2,
            voltage_v="220",
            parameters={"configuration": "single_phase", "assume_resistive": True},
        )
    )
    assert abs(result["load_results"][0]["unit_current_a"] - D("34.09090909090909")) < D("1e-13")
    assert result["apparent_power"]["value"] == D(15000)
    assert any("hipótese" in message for message in result["warnings"])


def test_reject_contradictory_resistive_assumption():
    with pytest.raises(ValidationError):
        Load(
            name="Carga",
            unit_power_w="100",
            power_factor="0.8",
            parameters={"assume_resistive": True},
        )


def test_zero_does_not_look_complete():
    result = run(dict(name="Não preenchido", unit_power_w="0"))
    assert result["installed_power"]["status"] == "pending"


def test_lighting_status_not_contaminated_by_other_estimates():
    project = ProjectInput(
        name="Casa",
        municipality="Cidade",
        built_area_m2="60",
        environments=[
            dict(
                name="Sala",
                area_m2="12",
                perimeter_m="14",
                loads=[
                    dict(
                        name="Lâmpada", kind="lighting", unit_power_w="9", power_origin="nameplate"
                    ),
                    dict(name="TV", unit_power_w="130", power_origin="user_estimate"),
                ],
            )
        ],
    )
    result = calculate(project.model_dump(mode="json"))
    assert result["installed_power"]["status"] == "estimated"
    assert result["lighting_nominal"]["status"] == "calculated"


def test_catalog_has_primary_source_metadata():
    ids = set()
    for item in CATALOG:
        ref = CatalogItem.model_validate(item)
        assert ref.id not in ids
        ids.add(ref.id)
        if ref.reference_power_w is not None:
            assert ref.source_url.startswith("https://")
            assert ref.document
            assert ref.verified_on == (
                "2026-10-22"
                if ref.id.startswith("midea-ac-")
                or ref.id
                in (
                    "mondial-ventilador-vsp40w",
                    "enel-hairdryer-small",
                    "enel-wall-exhaust",
                    "enel-phone-charger",
                    "enel-audio",
                )
                else "2026-10-21"
            )
    # Checked manufacturer declarations, not values inferred from engine outputs.
    by_id = {item["id"]: item for item in CATALOG}
    assert by_id["lg-ac-12000-s3w12ja33b"]["reference_power_w"] == "1130"
    assert by_id["philips-led-929001195311"]["power_factor"] == "0.7"
    assert by_id["samsung-tv43-au7700"]["power_rating"] == "maximum"


def test_manual_override_and_snapshot_preserved():
    import copy

    reference = copy.deepcopy(CATALOG[0])
    load = Load(
        name="LED",
        equipment_type=reference["equipment_type"],
        brand=reference["brand"],
        model=reference["model"],
        technology=reference["technology"],
        unit_power_w="12",
        power_origin="nameplate",
        power_factor=reference["power_factor"],
        catalog_reference=reference,
    )
    assert load.manual_override
    assert load.catalog_reference.reference_power_w == D(9)
    assert CATALOG[0]["reference_power_w"] == "9"


def test_aggregate_memory_contains_independent_substitutions():
    result = run(dict(name="Chuveiro", unit_power_w="7500", quantity=2, power_factor="1"))
    steps = {step["calculation"]: step for step in result["aggregate_steps"]}
    assert steps["Potência instalada cadastrada"]["value"] == D(15000)
    assert steps["Conversão W/kW"]["value"] == D(15)
    assert steps["Conversão VA/kVA"]["value"] == D(15)
    assert "15000 W / 1000 = 15 kW" == steps["Conversão W/kW"]["substituted"]


def test_metadata_does_not_change_electrical_digest():
    first = ProjectInput(name="Casa A", municipality="Cidade", built_area_m2="60")
    second = first.model_copy(update={"name": "Casa B", "notes": "Observação"})
    assert (
        calculate(first.model_dump(mode="json"))["input_digest"]
        == calculate(second.model_dump(mode="json"))["input_digest"]
    )


def test_lighting_classification_cannot_hide_lighting_load():
    with pytest.raises(ValidationError):
        Load(name="Lâmpada", equipment_type="lighting", kind="specific_use", unit_power_w="9")


def test_simple_catalog_selection_keeps_documented_ratings_and_unique_defaults():
    from collections import Counter

    counts = Counter(item["selection_name"] for item in CATALOG if item["selection_default"])
    assert all(count == 1 for count in counts.values())
    assert {
        "Televisor",
        "Lâmpada LED",
        "Bomba de água",
        "Motor elétrico",
        "Chuveiro elétrico",
    } <= set(counts)
    default_shower = next(
        item
        for item in CATALOG
        if item["selection_name"] == "Chuveiro elétrico" and item["selection_default"]
    )
    assert default_shower["reference_power_w"] == "7500"
    assert default_shower["voltage_v"] == "220"


@pytest.mark.parametrize(
    "identifier,watts,room",
    [
        ("enel-hairdryer-small", "600", "bathroom"),
        ("enel-wall-exhaust", "110", "bathroom"),
        ("enel-phone-charger", "50", "bedroom"),
        ("enel-audio", "120", "living"),
    ],
)
def test_new_room_category_references_remain_estimates(identifier, watts, room):
    item = next(item for item in CATALOG if item["id"] == identifier)
    assert item["reference_power_w"] == watts
    assert item["unit"] == "W" and item["power_rating"] == "estimated"
    assert item["power_factor"] is None and item["voltage_v"] is None
    assert room in item["recommended_environments"]
    assert item["source_url"] == "https://www.eneldistribuicao.com.br/Equipamentos.aspx"


@pytest.mark.parametrize("reference", CATALOG, ids=lambda item: item["id"])
def test_every_catalog_default_and_manual_power_recalculation(reference):
    """Independent multiplication oracle for every suggestion, including unknowns."""
    import copy

    snapshot = copy.deepcopy(reference)
    load = dict(
        name=reference.get("selection_name") or reference["name"],
        category=reference["category"],
        kind=reference["kind"],
        equipment_type=reference["equipment_type"],
        technology=reference["technology"],
        brand=reference.get("brand") or "",
        model=reference.get("model") or "",
        unit_power_w=reference["reference_power_w"],
        voltage_v=reference["voltage_v"],
        power_factor=reference["power_factor"],
        parameters=copy.deepcopy(reference["parameters"]),
        catalog_reference=copy.deepcopy(reference),
        quantity=3,
    )
    before = run(load)
    if reference["reference_power_w"] is None:
        assert before["installed_power"]["status"] == "pending"
        assert before["load_results"][0]["electrical_input_w"] is None
        assert before["apparent_power"] is None
    else:
        expected = D(reference["reference_power_w"]) * 3
        assert before["installed_power"]["value"] == expected
        assert before["installed_power_kw"]["value"] == expected / 1000
        assert before["lighting_nominal"]["value"] == (
            expected if reference["kind"] == "lighting" else 0
        )
    # The live value must win over a reference, including a value above its rating.
    load.update(unit_power_w="12345.123456", power_user_edited=True)
    after = run(load)
    assert after["installed_power"]["value"] == D("37035.370368")
    assert after["installed_power_kw"]["value"] == D("37.035370368")
    assert after["input_digest"] != before["input_digest"]
    assert after["memory"][0]["manual_override"]
    assert reference == snapshot  # Never edit the catalog to change an instance.
    load["quantity"] = 1
    assert run(load)["installed_power"]["value"] == D("12345.123456")
    load["unit_power_w"] = None
    missing = run(load)
    assert missing["installed_power"]["status"] == "pending"
    assert missing["apparent_power"] is None


@pytest.mark.parametrize(
    "power,voltage,pf",
    [
        ("1", "127", "0.9"),
        ("9", "220", "0.7"),
        ("1234.567891", "380", "0.876543"),
        ("0.000001", "0.000001", "0.000001"),
        ("999999999999.999999", "999999999999.999999", "1"),
    ],
)
def test_current_matches_rational_oracle_without_intermediate_rounding(power, voltage, pf):
    from decimal import localcontext
    from fractions import Fraction

    from app.calculations.current import current_from_active

    exact = Fraction(power) / (Fraction(voltage) * Fraction(pf))
    with localcontext() as ctx:
        ctx.prec = 40
        expected = D(exact.numerator) / D(exact.denominator)
    assert current_from_active(D(power), D(voltage), D(pf), "single_phase") == expected


def test_manual_quantity_voltage_pf_and_motor_recalculate_only_relevant_results():
    load = dict(
        name="Carga",
        unit_power_w="1800",
        quantity=2,
        power_factor="0.9",
        voltage_v="200",
        parameters={"configuration": "single_phase"},
    )
    first = run(load)
    assert first["installed_power"]["value"] == D(3600)
    assert first["apparent_power"]["value"] == D(4000)
    assert first["load_results"][0]["unit_current_a"] == D(10)
    load["voltage_v"] = "100"
    voltage = run(load)
    assert voltage["installed_power"] == first["installed_power"]
    assert voltage["apparent_power"] == first["apparent_power"]
    assert voltage["load_results"][0]["unit_current_a"] == D(20)
    load["power_factor"] = "0.5"
    pf = run(load)
    assert pf["installed_power"] == first["installed_power"]
    assert pf["apparent_power"]["value"] == D(7200)
    assert pf["load_results"][0]["unit_current_a"] == D(36)
    load["power_factor"] = None
    unknown = run(load)
    assert unknown["installed_power"] == first["installed_power"]
    assert unknown["apparent_power"] is None
    assert unknown["load_results"][0]["unit_current_a"] is None
    motor = dict(
        name="Motor",
        equipment_type="motor",
        quantity=2,
        parameters={
            "power_mode": "mechanical",
            "mechanical_power": "1",
            "mechanical_unit": "cv",
            "efficiency": "0.75",
        },
    )
    assert run(motor)["installed_power"]["value"] == D("1961.33")
    motor["parameters"]["efficiency"] = "0.5"
    assert run(motor)["installed_power"]["value"] == D("2941.995")
    motor["parameters"]["mechanical_power"] = "2"
    assert run(motor)["installed_power"]["value"] == D("5883.99")


def test_corrected_fan_default_does_not_rewrite_old_snapshots_or_manual_values():
    import copy

    from app.schemas import CalculationInput

    current = copy.deepcopy(
        next(item for item in CATALOG if item["id"] == "mondial-ventilador-vsp40w")
    )
    assert current["reference_power_w"] == "140"
    assert current["verified_on"] == "2026-10-22"
    old = copy.deepcopy(current)
    old["reference_power_w"] = "60"
    old["verified_on"] = "2026-10-21"
    for power, reference in [("60", old), ("140", current), ("175", current)]:
        project = CalculationInput(
            environments=[
                dict(
                    name="Sala",
                    loads=[
                        dict(
                            name="Ventilador",
                            quantity=2,
                            unit_power_w=power,
                            equipment_type="appliance",
                            catalog_reference=reference,
                        )
                    ],
                )
            ]
        )
        result = calculate(project.model_dump(mode="json"))
        assert result["installed_power"]["value"] == D(power) * 2
        assert project.environments[0].loads[0].unit_power_w == D(power)
