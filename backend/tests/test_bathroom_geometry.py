from decimal import Decimal as D

import pytest
from app.calculations.bathroom_geometry import calculate_bathroom_geometry


def project(x="0.5", z="1", kind="socket"):
    return dict(
        name="Volumes QA",
        municipality="Local informado",
        utility="unconfirmed",
        environments=[
            dict(
                id="11111111-1111-4111-8111-111111111111",
                name="Banheiro",
                type="bathroom",
                loads=[],
                bathroom_geometry=dict(
                    scope_confirmed=True,
                    shower_x_m="0",
                    shower_y_m="0",
                    measurement_source="Medidas de teste",
                    points=[
                        dict(
                            id="point",
                            name="Componente QA",
                            kind=kind,
                            x_min_m=x,
                            x_max_m=x,
                            y_min_m="0",
                            y_max_m="0",
                            z_min_m=z,
                            z_max_m=z,
                        )
                    ],
                ),
            )
        ],
    )


def point_result(data):
    return calculate_bathroom_geometry(data)[0]["points"][0]


@pytest.mark.parametrize(
    "x,z,volume",
    [
        ("0", "0", "1"),
        (".6", "2.25", "1"),
        (".600001", "1", "2"),
        ("1.2", "3", "2"),
        ("1.200001", "1", "3"),
        ("3.6", "2.25", "3"),
        ("3.600001", "1", "outside"),
        (".1", "2.250001", "2"),
        (".1", "3", "2"),
        (".1", "3.000001", "outside"),
        ("2", "2.250001", "outside"),
        ("1.200001", "2.25", "3"),
    ],
)
def test_fig18_cylinders_overhead_region_and_every_boundary(x, z, volume):
    row = point_result(project(x, z))
    assert row["volume"] == volume
    assert row["nearest_horizontal_distance_m"] == D(x)
    assert row["ordinary_socket_or_switch_forbidden"] == (volume in {"1", "2"})


@pytest.mark.parametrize("kind", ["socket", "switch", "water_heater", "luminaire", "other"])
def test_only_ordinary_socket_switch_receive_specific_prohibition(kind):
    row = point_result(project(kind=kind))
    assert (row["status"] == "invalid") == (kind in {"socket", "switch"})
    assert row[
        "pending_checks"
    ]  # other components still need IP/class/DR/equipotential verification


def test_full_envelope_used_instead_of_center_and_corner_euclidean_distance():
    data = project(".55")
    p = data["environments"][0]["bathroom_geometry"]["points"][0]
    p.update(x_max_m="1.5", y_min_m=".2", y_max_m="1.5", z_min_m="2", z_max_m="2.8")
    assert (
        point_result(data)["volume"] == "1"
    )  # nearest corner .585m; center would incorrectly escape volume1
    p.update(x_min_m=".6", y_min_m=".8")
    assert point_result(data)["nearest_horizontal_distance_m"] == 1
    assert point_result(data)["volume"] == "2"


@pytest.mark.parametrize(
    "missing", ["shower_x_m", "shower_y_m", "measurement_source", "scope_confirmed"]
)
def test_unknown_scope_or_measurement_never_yields_volume(missing):
    data = project()
    data["environments"][0]["bathroom_geometry"][missing] = None
    row = point_result(data)
    assert row["volume"] is None and row["ordinary_socket_or_switch_forbidden"] is None
    assert row["status"] == "pending"


@pytest.mark.parametrize(
    "field", ["x_min_m", "x_max_m", "y_min_m", "y_max_m", "z_min_m", "z_max_m"]
)
def test_unknown_envelope_coordinate_never_assumed_zero(field):
    data = project()
    data["environments"][0]["bathroom_geometry"]["points"][0][field] = None
    assert point_result(data)["volume"] is None


def test_inverted_envelope_nonbathroom_and_empty_points():
    data = project()
    data["environments"][0]["bathroom_geometry"]["points"][0]["z_min_m"] = "3"
    assert point_result(data)["status"] == "invalid"
    data = project()
    data["environments"][0]["type"] = "other"
    assert point_result(data)["volume"] is None
    data = project()
    data["environments"][0]["bathroom_geometry"]["points"] = []
    assert calculate_bathroom_geometry(data)[0]["status"] == "pending"
