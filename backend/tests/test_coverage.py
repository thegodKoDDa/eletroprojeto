from app.technical import DOCUMENTS, UTILITIES, normative_capabilities


def test_official_neoenergia_metadata_does_not_enable_unreviewed_demand():
    utility = next(item for item in UTILITIES if item["id"] == "neoenergia_elektro")
    assert utility["states"] == ["SP", "MS"]
    assert utility["municipality_mapping"] == "unverified"
    document = next(item for item in DOCUMENTS if item["id"] == "elektro")
    assert document["edition"].startswith("06")
    assert document["effective_date"] is None  # approval date is not silently treated as validity
    for state in ("SP", "MS"):
        demand = next(
            item
            for item in normative_capabilities(utility["id"], state)
            if item["code"] == "demand"
        )
        assert demand["available"] is False
        assert demand["evidence"][0]["access"] == "official_full_text"
    enel = next(
        item for item in normative_capabilities("enel_sp", "SP") if item["code"] == "demand"
    )
    assert all("neoenergia" not in item["url"] for item in enel["evidence"])
