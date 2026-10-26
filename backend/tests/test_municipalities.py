import csv
import hashlib
import io
import json

import pytest
from app import municipalities as module
from app.main import app
from fastapi.testclient import TestClient

FIELDS = [
    "DatGeracaoConjuntoDados",
    "NumCNPJ",
    "SigAgente",
    "NomAgente",
    "NomTipoOutorga",
    "DatReferenciaInformada",
    "CodMunicipioIBGE",
    "QtdUCAtiva",
]
PLACES = [dict(id=3550308, nome="São Paulo", microrregiao={"mesorregiao": {"UF": {"sigla": "SP"}}})]


def row(**kwargs):
    return {
        **dict(
            zip(
                FIELDS,
                [
                    "2026-10-19",
                    "00000000000001",
                    "Empresa A",
                    "Empresa A Ltda",
                    "Concessão",
                    "2026-09-01",
                    "3550308",
                    "100",
                ],
            )
        ),
        **kwargs,
    }


def index(rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    stream.seek(0)
    return module.build_index(stream, PLACES)


def test_multiple_agents_no_exclusive_or_automatic_assignment():
    data = index([row(), row(NumCNPJ="00000000000002", SigAgente="Empresa B"), row()])
    assert len(data["municipalities"]["3550308"]["candidates"]) == 2
    assert data["rows"] == 3


def test_latest_municipal_month_retains_zero_and_unknown_without_old_fallback():
    for count in ["0", ""]:
        data = index([row(DatReferenciaInformada="2026-08-01"), row(QtdUCAtiva=count)])
        assert data["municipalities"]["3550308"]["reference_month"] == "2026-09-01"
        assert data["municipalities"]["3550308"]["candidates"] == []


def test_no_code_and_unmatched_ibge_are_quarantined():
    data = index([row(CodMunicipioIBGE="0"), row(CodMunicipioIBGE="1403205"), row()])
    assert data["unassigned_rows"] == 1
    assert data["unmatched_ibge_codes"] == ["1403205"]
    assert set(data["municipalities"]) == {"3550308"}


@pytest.mark.parametrize(
    "change",
    [
        dict(NumCNPJ=""),
        dict(CodMunicipioIBGE="123"),
        dict(DatReferenciaInformada="2026-09-02"),
        dict(DatReferenciaInformada="2026-11-01"),
    ],
)
def test_reject_bad_identity_and_period(change):
    with pytest.raises(ValueError):
        index([row(**change)])


def test_conflicting_duplicate_is_not_silently_chosen():
    with pytest.raises(ValueError, match="conflitantes"):
        index([row(), row(QtdUCAtiva="101")])


def test_offline_endpoint_integrity_and_no_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    client = TestClient(app)
    assert client.get("/api/v1/locations/municipality?code=3550308").json()["status"] == "pending"
    assert client.get("/api/v1/locations/municipality?code=São Paulo").status_code == 422
    raw = json.dumps(index([row()])).encode()
    folder = tmp_path / "20261026"
    folder.mkdir()
    (folder / "index.json").write_bytes(raw)
    (folder / "report.json").write_text(
        json.dumps(
            dict(
                validated=True,
                consulted_on="2026-10-26",
                index_sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
    )
    value = client.get("/api/v1/locations/municipality?code=3550308").json()
    assert value["automatic_assignment"] is False
    assert value["municipality"]["name"] == "São Paulo"
    assert value["reference_month"] == "2026-09-01"
    assert value["candidates"][0]["active_units"] == 100
    module.load_snapshot.cache_clear()
    (folder / "index.json").write_bytes(raw + b"changed")
    assert client.get("/api/v1/locations/municipality?code=3550308").json()["status"] == "pending"


def test_lagging_agent_is_retained_with_own_period_not_silently_excluded():
    data = index([row(DatReferenciaInformada="2026-08-01"), row(NumCNPJ="00000000000002")])
    item = data["municipalities"]["3550308"]
    assert item["reference_month"] == "2026-09-01"
    assert [c["reference_month"] for c in item["candidates"]] == ["2026-08-01", "2026-09-01"]
