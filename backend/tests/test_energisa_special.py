"""Independent NDU7 examples: pp.56–57 and table12–14, without catalog inference."""

from copy import deepcopy
from decimal import Decimal as D
from decimal import localcontext

import pytest
from app.calculations.energisa import calculate_energisa_demand
from app.calculations.energisa_special import special_components
from app.schemas import EnergisaDemandInput


def inventory(group, **load):
    return dict(
        utility="energisa_sul_sudeste",
        state="SP",
        unit_type="individual_residential",
        inventory_reviewed=True,
        has_signage_or_display_lighting=False,
        confirmed_absent_groups=[
            g for g in ["d1", "d2", "d3", "d4", "d5", "d6", "d7"] if g != group
        ],
        loads=[
            dict(name="Exemplo independente", group=group, quantity=1, unit_power_w="1000", **load)
        ],
    )


def motor(phase="single_phase", cv="10"):
    return dict(configuration=phase, shaft_power_cv=cv, source="Placa de teste: fases e eixo")


def special(kind="arc_welder", va="1000", pf=".8", connection="standard"):
    return dict(
        equipment_type=kind,
        input_apparent_power_va=va,
        power_factor=pf,
        connection=connection,
        source="Ficha de teste: entrada e ligação",
    )


@pytest.mark.parametrize("phase,expected", [("single_phase", "15096.4"), ("three_phase", "15498")])
def test_two_10cv_example_printed_in_notes_without_rounding(phase, expected):
    data = inventory("d6", motor=motor(phase))
    data["loads"][0]["quantity"] = 2
    result = calculate_energisa_demand(data)
    # Printed example rounds per motor (7.55/7.75kW); preserve exact 8.03*.94*2 / 8.61*.90*2.
    assert result["groups"][5]["demand_w"] == D(expected)
    assert result["status"] == "estimated"
    assert result["installed_power_w"] == D("2000")  # table does not replace supplied installed W
    assert result["groups"][5]["components"][0]["power_factor"] == D(
        ".94" if phase == "single_phase" else ".90"
    )


@pytest.mark.parametrize(
    "count,expected", [(1, "9437.6"), (2, "15096.4"), (3, "19824.6"), (5, "33041"), (6, "33952.8")]
)
def test_motor_count_boundaries(count, expected):
    data = inventory("d6", motor=motor())
    data["loads"][0]["quantity"] = count
    assert calculate_energisa_demand(data)["groups"][5]["demand_w"] == D(expected)


def test_mixed_motor_sizes_and_phases_use_total_active_count_and_individual_rows():
    data = inventory("d6", motor=motor())
    data["loads"].append(
        dict(
            name="Trifásico",
            group="d6",
            quantity=1,
            unit_power_w="1100",
            motor=motor("three_phase", "1"),
        )
    )
    result = calculate_energisa_demand(data)
    assert result["groups"][5]["demand_w"] == D("7548.2") + D("902")
    # Split inventory cannot change count or demand.
    same = deepcopy(data)
    same["loads"] = [{**data["loads"][0], "quantity": 2}]
    split = deepcopy(same)
    split["loads"] = [{**same["loads"][0], "quantity": 1}] * 2
    assert calculate_energisa_demand(same)["value"] == calculate_energisa_demand(split)["value"]


@pytest.mark.parametrize(
    "phase,cv",
    [
        ("single_phase", "1/6"),
        ("single_phase", "11"),
        ("three_phase", "31"),
        ("three_phase", "0.333333"),
        ("unconfirmed", "1"),
    ],
)
def test_motor_rows_never_interpolated(phase, cv):
    result = calculate_energisa_demand(inventory("d6", motor=motor(phase, cv)))
    assert result["value"] is None and result["pending_checks"]


@pytest.mark.parametrize(
    "phase,cv,expected",
    [
        ("single_phase", "1/3", "525.4"),
        ("single_phase", "10", "9437.6"),
        ("three_phase", "1/6", "247.9"),
        ("three_phase", "30", "26926.9"),
    ],
)
def test_motor_table_extreme_rows(phase, cv, expected):
    assert calculate_energisa_demand(inventory("d6", motor=motor(phase, cv)))["groups"][5][
        "demand_w"
    ] == D(expected)


@pytest.mark.parametrize(
    "kind,connection,count,expected",
    [
        ("arc_welder", "standard", 1, "800"),
        ("arc_welder", "standard", 2, "1360"),
        ("arc_welder", "standard", 3, "1680"),
        ("arc_welder", "standard", 4, "1920"),
        ("arc_welder", "inverted_v_v", 4, "3840"),
        ("resistance_welder", "standard", 3, "1760"),
        ("resistance_welder", "inverted_v_v", 3, "3520"),
        ("x_ray", "not_applicable", 3, "1920"),
        ("galvanization", "not_applicable", 4, "1920"),
    ],
)
def test_table14_rank_quantity_and_connection(kind, connection, count, expected):
    data = inventory("d7", special=special(kind, connection=connection))
    data["loads"][0]["quantity"] = count
    assert calculate_energisa_demand(data)["groups"][6]["demand_w"] == D(expected)


def test_table14_sort_after_v_v_doubling_and_never_convert_va_as_w():
    data = inventory("d7", special=special(va="1000", connection="inverted_v_v"))
    data["loads"].append(
        dict(
            name="Maior nominal",
            group="d7",
            quantity=1,
            unit_power_w="1200",
            special=special(va="1500"),
        )
    )
    result = calculate_energisa_demand(data)
    assert result["groups"][6]["demand_w"] == D("1600") + D("840")
    assert result["groups"][6]["components"][0]["name"] == "Exemplo independente"
    assert result["installed_power_w"] == 2200


def test_rank_ambiguity_between_w_and_va_remains_pending():
    data = inventory("d7", special=special(va="2000", pf=".5"))
    data["loads"].append(
        dict(
            name="Outro FP",
            group="d7",
            quantity=1,
            unit_power_w="1400",
            special=special(va="1500", pf="1"),
        )
    )
    result = calculate_energisa_demand(data)
    assert result["value"] is None and "ordem" in result["groups"][6]["reason"]


def test_arc_and_galvanization_share_rank_but_xray_and_resistance_are_separate():
    data = inventory("d7", special=special(va="2000"))
    for kind in ["galvanization", "x_ray", "resistance_welder"]:
        data["loads"].append(
            dict(
                name=kind,
                group="d7",
                quantity=1,
                unit_power_w="1000",
                special=special(
                    kind, connection="standard" if kind == "resistance_welder" else "not_applicable"
                ),
            )
        )
    assert calculate_energisa_demand(data)["groups"][6]["demand_w"] == D("1600") + D("560") + D(
        "800"
    ) + D("800")


@pytest.mark.parametrize(
    "kind,connection",
    [("x_ray", "inverted_v_v"), ("arc_welder", "not_applicable"), ("galvanization", "standard")],
)
def test_wrong_special_connection_is_pending(kind, connection):
    assert (
        calculate_energisa_demand(inventory("d7", special=special(kind, connection=connection)))[
            "value"
        ]
        is None
    )


@pytest.mark.parametrize(
    "phase,expected", [("single_phase", "3960"), ("balanced_three_phase", None)]
)
def test_central_maximum_current_has_100percent_factor(phase, expected):
    data = inventory(
        "d5",
        air_conditioning_type="central_unit",
        central=dict(
            configuration=phase,
            voltage_v="220",
            maximum_total_current_a="20",
            power_factor=".9",
            source="Fabricante: máximo total",
        ),
    )
    result = calculate_energisa_demand(data)
    assert result["status"] == "estimated"
    with localcontext() as ctx:
        ctx.prec = 40
        assert result["groups"][4]["demand_w"] == (
            D(expected) if expected else D(3).sqrt() * D("3960")
        )
    assert result["groups"][4]["factor"] == 1
    assert result["installed_power_w"] == 1000


def test_individual_ac_count_excludes_centrals_and_is_not_applied_to_their_maximum_current():
    data = inventory(
        "d5",
        air_conditioning_type="central_unit",
        central=dict(
            configuration="single_phase",
            voltage_v="220",
            maximum_total_current_a="10",
            power_factor="1",
            source="Fabricante",
        ),
    )
    data["loads"].append(
        dict(
            name="Individuais",
            group="d5",
            quantity=2,
            unit_power_w="800",
            air_conditioning_type="window_or_individual",
        )
    )
    result = calculate_energisa_demand(data)
    assert result["groups"][4]["demand_w"] == D("2200") + D("1408")
    assert result["groups"][4]["factor"] is None


@pytest.mark.parametrize(
    "group,field,value",
    [
        ("d6", "motor", motor()),
        ("d7", "special", special()),
        (
            "d5",
            "central",
            dict(
                configuration="single_phase",
                voltage_v="220",
                maximum_total_current_a="10",
                power_factor=".9",
                source="Fabricante",
            ),
        ),
    ],
)
def test_missing_parameters_source_and_no_mutation(group, field, value):
    for missing in value:
        data = inventory(group, **{field: {**value, missing: None}})
        if group == "d5":
            data["loads"][0]["air_conditioning_type"] = "central_unit"
        original = deepcopy(data)
        assert calculate_energisa_demand(data)["value"] is None
        assert data == original


def test_reserve_needs_installed_w_but_no_special_demand_parameters():
    data = inventory("d6", motor=motor())
    before = calculate_energisa_demand(data)
    data["loads"].append(
        dict(name="Reserva", group="d7", quantity=1, unit_power_w="1000", reserve=True)
    )
    after = calculate_energisa_demand(data)
    assert after["value"] == before["value"]
    assert after["installed_power_w"] == 2000


def test_very_large_quantity_is_compact_and_schema_accepts_partial_parameters():
    data = inventory("d7", special=special())
    data["loads"][0]["quantity"] = 100000
    # Pure helper tests quantity aggregation independently of the installed75kW scope.
    rows, error = special_components(data["loads"])
    assert error is None and len(rows) == 4
    assert sum(x["quantity"] for x in rows) == 100000
    data["loads"][0]["motor"] = {}
    assert EnergisaDemandInput.model_validate(data)


def test_unused_parameters_from_previous_classification_never_replace_current_source():
    data = inventory("d7", special=special())
    data["loads"][0]["motor"] = motor()
    data["loads"][0]["central"] = dict(source="Central antiga")
    result = calculate_energisa_demand(data)
    assert result["groups"][6]["components"][0]["source"] == "Ficha de teste: entrada e ligação"
    data = inventory(
        "d5",
        air_conditioning_type="central_unit",
        central=dict(
            configuration="single_phase",
            voltage_v="220",
            maximum_total_current_a="10",
            power_factor=".9",
            source="Fabricante atual",
        ),
    )
    data["loads"][0]["motor"] = motor()
    assert (
        calculate_energisa_demand(data)["groups"][4]["components"][0]["source"]
        == "Fabricante atual"
    )
