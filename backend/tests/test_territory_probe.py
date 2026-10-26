import importlib.util
from pathlib import Path

import httpx
import pytest

spec = importlib.util.spec_from_file_location(
    "territory_probe", Path(__file__).resolve().parents[2] / "scripts" / "territory.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_arcgis_error_in_http200_never_validates_data():
    response = httpx.Response(
        200,
        json={"error": {"code": 500, "message": "The connection attempt failed."}},
        request=httpx.Request("GET", probe.SERVICE),
    )
    with pytest.raises(ValueError, match="erro"):
        probe.checked_json(response)


def feature():
    return {
        "attributes": {
            "objectid": 1,
            "cnpj": "00.000.000/0001-00",
            "sigla": "Teste",
            "uf": "SP",
            "ato_legal": "Ato de teste",
        },
        "geometry": {"rings": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
    }


def test_attributes_do_not_replace_geometry_and_snapshot_must_be_complete():
    row = feature()
    row.pop("geometry")
    data = {"features": [row], "spatialReference": {"wkid": 4674}}
    assert probe.validate_features(data, 1, geometry=False) == {1}
    with pytest.raises(ValueError, match="Polígono"):
        probe.validate_features(data, 1, geometry=True)
    with pytest.raises(ValueError, match="incompleta"):
        probe.validate_features(data, 2, geometry=False)
    with pytest.raises(ValueError, match="incompleta"):
        probe.validate_features({**data, "exceededTransferLimit": True}, 1, geometry=False)


def test_polygon_reference_closed_rings_and_unique_identity_required():
    data = {"features": [feature()], "spatialReference": {"wkid": 4674}}
    assert probe.validate_features(data, 1, geometry=True) == {1}
    data["spatialReference"]["wkid"] = 4326
    with pytest.raises(ValueError, match="SIRGAS"):
        probe.validate_features(data, 1, geometry=True)
    data["spatialReference"]["wkid"] = 4674
    data["features"] = [feature(), feature()]
    with pytest.raises(ValueError, match="duplicada"):
        probe.validate_features(data, 2, geometry=True)
