"""Manual independent examples and every band boundary, NDU-001 v7 pp.56/63–67."""

from copy import deepcopy
from decimal import Decimal, localcontext

import pytest
from app.calculations.energisa import (
    calculate_energisa_demand,
    count_factor,
    lighting_outlets_demand_w,
)


@pytest.fixture
def residential_input():
    return dict(
        utility="energisa_sul_sudeste",
        state="SP",
        unit_type="individual_residential",
        inventory_reviewed=True,
        has_signage_or_display_lighting=False,
        simultaneous_lighting_outlets=False,
        loads=[
            dict(name="Iluminação e TUG", group="d1", quantity=1, unit_power_w="4500"),
            dict(name="Chuveiros", group="d2", quantity=2, unit_power_w="5500"),
            dict(name="Micro-ondas", group="d3", quantity=1, unit_power_w="1400"),
            dict(name="Fogão", group="d4", quantity=1, unit_power_w="7000"),
            dict(
                name="AC individuais",
                group="d5",
                quantity=2,
                unit_power_w="800",
                air_conditioning_type="window_or_individual",
            ),
        ],
        confirmed_absent_groups=["d6", "d7"],
    )


def test_manual_mixed_inventory_without_intermediate_rounding(residential_input):
    original = deepcopy(residential_input)
    result = calculate_energisa_demand(residential_input)
    # Independent manual sum: 860+750+660+590+260; 2*5500*.75;
    # 1400;7000;2*800*.88 ->21178 W. Catalog suggestions are never read.
    assert [row["demand_w"] for row in result["groups"]] == list(
        map(Decimal, ["3120", "8250", "1400", "7000", "1408", "0", "0"])
    )
    assert result["installed_power_w"] == Decimal("25500")
    assert result["demanded_power_kw"] == Decimal("21.178")
    with localcontext() as context:
        context.prec = 40
        assert result["value"] == Decimal("21.178") / Decimal(".92")
    assert result["status"] == "estimated"
    assert [band["installed_band_w"] for band in result["groups"][0]["bands"]] == list(
        map(Decimal, ["1000", "1000", "1000", "1000", "500"])
    )
    assert residential_input == original


@pytest.mark.parametrize(
    "power,expected",
    [
        ("0", "0"),
        ("999", "859.14"),
        ("1000", "860"),
        ("1000.000001", "860.00000075"),
        ("2000", "1610"),
        ("3000", "2270"),
        ("4000", "2860"),
        ("4500", "3120"),
        ("5000", "3380"),
        ("6000", "3830"),
        ("7000", "4230"),
        ("8000", "4580"),
        ("9000", "4890"),
        ("10000", "5160"),
        ("10000.000001", "5160.00000024"),
        ("75000", "20760"),
    ],
)
def test_table5_cumulative_note_iii(power, expected):
    assert lighting_outlets_demand_w(Decimal(power), False) == Decimal(expected)
    assert lighting_outlets_demand_w(Decimal(power), True) == Decimal(power)


@pytest.mark.parametrize("power", ["-1", "75000.000001", "NaN", "Infinity"])
def test_table5_rejects_invalid_or_out_of_scope_power(power):
    with pytest.raises(ValueError):
        lighting_outlets_demand_w(Decimal(power), False)


@pytest.mark.parametrize(
    "group,bands",
    [
        (
            "d2",
            [
                (1, 100),
                (2, 75),
                (3, 70),
                (4, 66),
                (5, 62),
                (6, 59),
                (7, 56),
                (8, 53),
                (9, 51),
                (10, 49),
                (11, 47),
                (12, 45),
                (13, 43),
                (14, 41),
                (15, 40),
                (16, 39),
                (17, 38),
                (18, 37),
                (19, 36),
                (20, 35),
                (21, 34),
                (22, 33),
                (23, 32),
                (24, 31),
                (25, 30),
                (100, 30),
            ],
        ),
        (
            "d3",
            [(1, 100), (2, 70), (4, 70), (5, 60), (6, 60), (7, 50), (9, 50), (10, 45), (100, 45)],
        ),
        (
            "d4",
            [
                (1, 100),
                (2, 60),
                (3, 48),
                (4, 40),
                (5, 37),
                (6, 35),
                (7, 33),
                (8, 32),
                (9, 31),
                (10, 30),
                (11, 30),
                (12, 28),
                (15, 28),
                (16, 27),
                (20, 27),
                (21, 26),
                (25, 26),
                (26, 25),
            ],
        ),
        (
            "d5",
            [
                (1, 100),
                (2, 88),
                (3, 82),
                (4, 78),
                (5, 76),
                (6, 74),
                (7, 72),
                (8, 71),
                (9, 70),
                (11, 70),
                (12, 68),
                (14, 68),
                (15, 67),
                (16, 67),
                (17, 66),
                (22, 66),
                (23, 65),
                (30, 65),
                (31, 64),
                (50, 64),
                (51, 62),
            ],
        ),
    ],
)
def test_all_count_factor_boundaries(group, bands, subtests):
    for count, percent in bands:
        with subtests.test(group=group, count=count):
            assert count_factor(group, count) == Decimal(percent) / 100


@pytest.mark.parametrize("count", [0, -1, True, Decimal(2), 2.5])
def test_invalid_count_is_never_an_absence(count):
    with pytest.raises(ValueError):
        count_factor("d2", count)


@pytest.mark.parametrize(
    "change",
    [
        "missing_absence",
        "unknown_power",
        "zero_power",
        "unreviewed",
        "unconfirmed_simultaneity",
        "central_ac",
        "unconfirmed_ac",
        "motor",
        "special",
    ],
)
def test_unknowns_remain_null(residential_input, change):
    data = deepcopy(residential_input)
    if change == "missing_absence":
        data["confirmed_absent_groups"] = []
    elif change == "unknown_power":
        data["loads"][1]["unit_power_w"] = None
    elif change == "zero_power":
        data["loads"][1]["unit_power_w"] = "0"
    elif change == "unreviewed":
        data["inventory_reviewed"] = False
    elif change == "unconfirmed_simultaneity":
        data["simultaneous_lighting_outlets"] = None
    elif change in ("central_ac", "unconfirmed_ac"):
        data["loads"][-1]["air_conditioning_type"] = (
            "central_unit" if change == "central_ac" else "unconfirmed"
        )
    else:
        group = "d6" if change == "motor" else "d7"
        data["confirmed_absent_groups"].remove(group)
        data["loads"].append(dict(name="Especial", group=group, quantity=1, unit_power_w="1000"))
    result = calculate_energisa_demand(data)
    assert result["value"] is None
    assert result["demanded_power_kw"] is None
    assert result["status"] == (
        "out_of_scope" if change in ("central_ac", "motor", "special") else "pending"
    )
    assert result["pending_checks"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("utility", "enel_sp"),
        ("state", "MS"),
        ("unit_type", "grouped"),
        ("unit_type", "non_residential"),
    ],
)
def test_no_coefficients_for_other_utilities_or_scope(residential_input, key, value):
    residential_input[key] = value
    result = calculate_energisa_demand(residential_input)
    assert result["status"] == "out_of_scope"
    assert result["value"] is None and result["groups"] == []


def test_installed_limit_and_reserve_exclusion(residential_input):
    data = deepcopy(residential_input)
    data["loads"].append(
        dict(name="Reserva", group="d6", quantity=1, unit_power_w="1000", reserve=True)
    )
    result = calculate_energisa_demand(data)
    assert result["value"] == calculate_energisa_demand(residential_input)["value"]
    assert result["installed_power_w"] == Decimal("26500")
    assert result["ignored_reserve_loads"] == ["Reserva"]
    for missing in (None, "0"):
        data["loads"][-1]["unit_power_w"] = missing
        pending = calculate_energisa_demand(data)
        assert pending["value"] is None and pending["installed_power_w"] is None
    data["loads"][-1]["unit_power_w"] = "1000"
    data["loads"][0]["unit_power_w"] = "75000"
    assert calculate_energisa_demand(data)["status"] == "out_of_scope"


def test_explicit_empty_inventory_is_distinct_from_missing_groups(residential_input):
    residential_input["loads"] = []
    residential_input["confirmed_absent_groups"] = ["d1", "d2", "d3", "d4", "d5", "d6", "d7"]
    result = calculate_energisa_demand(residential_input)
    assert result["value"] == Decimal(0)  # seven explicit absence declarations, never defaulted
    residential_input["confirmed_absent_groups"].remove("d1")
    assert calculate_energisa_demand(residential_input)["value"] is None


def test_signage_is_outside_the_table5_scope(residential_input):
    residential_input["has_signage_or_display_lighting"] = True
    result = calculate_energisa_demand(residential_input)
    assert result["status"] == "out_of_scope" and result["groups"] == []


def test_different_unit_powers_are_summed_before_using_total_appliance_count(residential_input):
    residential_input["loads"][1]["quantity"] = 1
    residential_input["loads"].append(
        dict(name="Outro chuveiro", group="d2", quantity=1, unit_power_w="6400")
    )
    result = calculate_energisa_demand(residential_input)
    assert result["groups"][1]["installed_power_w"] == Decimal("11900")
    assert result["groups"][1]["quantity"] == 2
    assert result["groups"][1]["demand_w"] == Decimal("8925")


@pytest.mark.parametrize("power,status", [("75000", "estimated"), ("75000.000001", "out_of_scope")])
def test_full_method_installed_power_boundary(residential_input, power, status):
    residential_input["loads"] = [
        dict(name="Base declarada", group="d1", quantity=1, unit_power_w=power)
    ]
    residential_input["confirmed_absent_groups"] = ["d2", "d3", "d4", "d5", "d6", "d7"]
    result = calculate_energisa_demand(residential_input)
    assert result["status"] == status
    assert (result["value"] is not None) is (status == "estimated")


def test_known_subtotal_above_limit_is_out_of_scope_even_with_an_unknown(residential_input):
    residential_input["loads"][0]["unit_power_w"] = "75001"
    residential_input["loads"][1]["unit_power_w"] = None
    result = calculate_energisa_demand(residential_input)
    assert result["status"] == "out_of_scope" and result["value"] is None
