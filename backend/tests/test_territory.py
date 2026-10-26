from decimal import Decimal as D

import pytest
from app import territory

SQUARE = [[[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]]]


@pytest.mark.parametrize(
    "x,y,result",
    [
        (1, 1, "inside"),
        (4, 1, "boundary"),
        (4, 4, "boundary"),
        (5, 1, "outside"),
        (0, 2, "boundary"),
    ],
)
def test_polygon_interior_and_exact_boundaries(x, y, result):
    assert territory.relation(D(x), D(y), SQUARE) == result
    assert territory.relation(D(x), D(y), [list(reversed(SQUARE[0]))]) == result


def test_holes_multipart_and_small_decimal_boundary():
    hole = [[[1, 1], [2, 1], [2, 2], [1, 2], [1, 1]]]
    assert territory.relation(D("1.5"), D("1.5"), SQUARE + hole) == "outside"
    assert territory.relation(D("2"), D("1.5"), SQUARE + hole) == "boundary"
    assert territory.relation(D(".5"), D(".5"), SQUARE + hole) == "inside"
    triangle = [[[0, 0], [0.000000000001, 0.000000000001], [0.000000000001, 0], [0, 0]]]
    assert territory.relation(D(".0000000000005"), D(".0000000000005"), triangle) == "boundary"


def test_missing_snapshot_never_inferrs_absence_or_utility(monkeypatch):
    monkeypatch.setattr(territory, "snapshot", lambda: None)
    result = territory.lookup(-23, -46)
    assert result["status"] == "pending" and result["candidates"] == []
    assert result["automatic_assignment"] is False


def test_ended_and_open_periods_remain_separate_candidates_and_boundary_ambiguous(monkeypatch):
    data = {
        "consulted_on": "2026-10-26T00:00:00+00:00",
        "checks": [{"name": "geometry", "sha256": "test"}],
    }
    attrs = dict(
        objectid=1,
        razao_social="Empresa de teste",
        sigla="TESTE",
        cnpj="00.000.000/0001-00",
        uf="SP",
        ato_legal="Ato de teste",
        ini_vigencia=0,
        fim_vigencia=100000,
    )
    monkeypatch.setattr(
        territory,
        "snapshot",
        lambda: (
            data,
            [
                (attrs, SQUARE, (0, 0, 4, 4)),
                ({**attrs, "objectid": 2, "fim_vigencia": None}, SQUARE, (0, 0, 4, 4)),
            ],
        ),
    )
    result = territory.lookup(1, 4)
    assert result["status"] == "awaiting_technical_validation"
    assert result["automatic_assignment"] is False
    assert [c["temporal_status"] for c in result["candidates"]] == ["ended", "no_end_recorded"]
    assert all(c["relation"] == "boundary" for c in result["candidates"])
    assert territory.lookup(20, 20)["candidates"] == []
