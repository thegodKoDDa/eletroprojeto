"""Independent hand-worked cases and boundaries, see docs/standards.md.

Expected numbers are fixed examples, not computed by a second implementation.
A 3x4 m bedroom has area 12, perimeter 14: 160 VA light, 3 TUG/300 VA.
A 3x3 m kitchen has area 9, perimeter 12: 100 VA light, 4 TUG/1900 VA.
No summation of these VA into installed W, no assumed power factors.
"""

from decimal import Decimal as D

import pytest
from app.calculations.residential import lighting_minimum, outlet_load, outlet_minimum
from app.schemas import ProjectInput


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
