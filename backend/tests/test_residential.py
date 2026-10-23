"""Independent hand-worked cases and boundaries, see docs/standards.md.

Expected numbers are fixed examples, not computed by a second implementation.
A 3x4 m bedroom has area 12, perimeter 14: 160 VA light, 3 TUG/300 VA.
A 3x3 m kitchen has area 9, perimeter 12: 100 VA light, 4 TUG/1900 VA.
No summation of these VA into installed W, no assumed power factors.
"""

import copy
from decimal import Decimal as D

import pytest
from app.calculations.engine import calculate
from app.calculations.residential import lighting_minimum, outlet_load, outlet_minimum
from app.reports.pdf import render_report
from app.schemas import CalculationResult, ProjectInput
from test_pdf import extract_pages


@pytest.mark.parametrize(
    "area,expected",
    [
        ("0.000001", 100),
        ("6", 100),
        ("6.000001", 100),
        ("9.999999", 100),
        ("10", 160),
        ("12", 160),
        ("13.999999", 160),
        ("14", 220),
        ("18", 280),
    ],
)
def test_lighting_complete_blocks_only(area, expected):
    assert lighting_minimum(D(area)) == D(expected)


@pytest.mark.parametrize("area", ["0", "-1", "NaN", "Infinity"])
def test_lighting_rejects_invalid_area(area):
    with pytest.raises(ValueError):
        lighting_minimum(D(area))


@pytest.mark.parametrize(
    "kind,area,perimeter,expected",
    [
        ("bedroom", "12", "14", 3),
        ("living", "6", "10", 2),
        ("living", "6", "10.000001", 3),
        ("kitchen", "9", "12", 4),
        ("laundry", "4", "7", 2),
        ("laundry", "4", "7.000001", 3),
        ("bathroom", None, None, 1),
        ("corridor", "2.25", None, 1),
        ("corridor", "2.250001", None, 1),
        ("garage", "6", None, 1),
        ("garage", "6.000001", None, None),
        ("office", "8", "12", 3),
        ("outdoor", "12", "14", None),
        ("other", "12", "14", None),
    ],
)
def test_outlets_by_destination_and_boundary(kind, area, perimeter, expected):
    assert (
        outlet_minimum(kind, D(area) if area else None, D(perimeter) if perimeter else None)
        == expected
    )


@pytest.mark.parametrize(
    "kind,points,expected",
    [
        ("bathroom", 1, 600),
        ("kitchen", 3, 1800),
        ("kitchen", 4, 1900),
        ("kitchen", 7, 2200),
        ("bedroom", 5, 500),
    ],
)
def test_attributed_load_keeps_each_room_separate(kind, points, expected):
    assert outlet_load(kind, points) == D(expected)


def inputs():
    return ProjectInput.model_validate(
        dict(
            name="Estudo residencial",
            municipality="Cidade",
            analysis_scope="normative",
            utility="energisa_sul_sudeste",
            environments=[
                dict(
                    name="Quarto",
                    type="bedroom",
                    area_m2="12",
                    perimeter_m="14",
                    lighting_points=1,
                    outlets=5,
                    loads=[
                        dict(
                            name="LED manual",
                            kind="lighting",
                            unit_power_w="9",
                            quantity=1,
                            power_factor="0.7",
                            power_origin="nameplate",
                        )
                    ],
                ),
                dict(
                    name="Cozinha",
                    type="kitchen",
                    area_m2="9",
                    perimeter_m="12",
                    lighting_points=0,
                    outlets=1,
                ),
            ],
        )
    ).model_dump(mode="json")


def test_complete_prevision_does_not_mutate_or_double_count_and_recalculates():
    project = inputs()
    original = copy.deepcopy(project)
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    assert project == original
    assert result["installed_power"]["value"] == "9"
    assert result["lighting_nominal"]["value"] == "9"
    assert result["normative"]["lighting"]["value"] == "260"
    assert result["normative"]["outlets"]["value"] == "2400"  # 5 actual dry + 4 minimum wet
    assert result["normative"]["demand"]["value"] is None
    bedroom, kitchen = result["normative_environments"]
    assert bedroom["outlet_basis_points"] == 5
    assert kitchen["minimum_outlet_points"] == 4  # no extra two points for sink sockets
    assert kitchen["outlet_points_missing"] == 3
    assert kitchen["lighting_points_missing"] == 1
    assert len(result["notifications"]) == 2
    assert result["normative_capabilities"][0]["available"]
    project["environments"][1].update(area_m2="14", perimeter_m="14.000001", outlets=6)
    after = calculate(project)
    assert after["normative"]["lighting"]["value"] == D(380)
    assert after["normative"]["outlets"]["value"] == D(2600)
    assert after["input_digest"] != result["input_digest"]
    assert after["installed_power"]["value"] == D(9)


def test_missing_or_unsupported_room_never_becomes_zero_or_partial_total():
    project = inputs()
    project["environments"][1]["area_m2"] = None
    result = calculate(project)
    assert result["normative"]["lighting"]["value"] is None
    assert result["normative_environments"][0]["lighting_va"] == D(160)
    assert result["normative"]["outlets"]["value"] == D(2400)
    assert any(n["target_id"].endswith("area_m2") for n in result["notifications"])
    project["environments"][1]["type"] = "outdoor"
    result = calculate(project)
    assert result["normative_environments"][1]["status"] == "out_of_scope"
    assert all(result["normative"][key]["value"] is None for key in ("lighting", "outlets"))
    assert not result["field_issues"]


def test_opt_in_empty_and_bathroom_dependencies():
    project = inputs()
    project["analysis_scope"] = "installed"
    result = calculate(project)
    assert result["normative_environments"] == []
    assert result["normative"]["lighting"]["value"] is None
    project["analysis_scope"] = "normative"
    project["environments"] = []
    assert calculate(project)["normative"]["lighting"]["value"] is None
    project["environments"] = [
        dict(
            id="bath",
            name="Banheiro",
            type="bathroom",
            area_m2="4",
            perimeter_m=None,
            lighting_points=1,
            outlets=1,
            loads=[],
        )
    ]
    result = calculate(project)
    assert not result["field_issues"]
    assert result["normative"]["outlets"]["value"] == D(600)


def test_pdf_contains_concise_residential_results():
    project = inputs()
    result = calculate(project)
    text = "\n".join(extract_pages(render_report(project, result)))
    assert "Previsão residencial por ambiente" in text
    assert "260 VA" in text and "2.400" not in text and "2400 VA" in text
    assert "https://" not in text
