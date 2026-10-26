"""Integration, review invalidation and independent project demand examples."""

from copy import deepcopy
from decimal import Decimal, localcontext

import pytest
from app.calculations.engine import calculate
from app.reports.pdf import render_report
from app.reports.summary import build_summary
from app.schemas import CalculationInput, ProjectInput


def study():
    return CalculationInput.model_validate(
        dict(
            name="Demanda integrada",
            municipality="Local informado",
            state="SP",
            utility="energisa_sul_sudeste",
            energisa_demand=dict(
                enabled=True,
                unit_type="individual_residential",
                has_signage_or_display_lighting=False,
                simultaneous_lighting_outlets=False,
                confirmed_absent_groups=["d3", "d4", "d5", "d6", "d7"],
            ),
            environments=[
                dict(
                    name="Casa",
                    loads=[
                        dict(
                            name="Luz e TUG", unit_power_w="1000", energisa_demand=dict(group="d1")
                        ),
                        dict(
                            name="Chuveiro", unit_power_w="5500", energisa_demand=dict(group="d2")
                        ),
                    ],
                )
            ],
        )
    ).model_dump(mode="json")


def reviewed(data):
    data["energisa_demand"]["reviewed_inventory_digest"] = calculate(data)["energisa_demand"][
        "inventory_digest"
    ]
    return calculate(data)


def test_independent_example_review_then_edit_and_no_mutation():
    data = study()
    original = deepcopy(data)
    first = calculate(data)
    assert data == original
    assert first["normative"]["demand"]["value"] is None
    result = reviewed(data)
    with localcontext() as context:
        context.prec = 40
        assert result["normative"]["demand"]["value"] == Decimal("6.36") / Decimal(".92")
    assert result["installed_power"]["value"] == 6500
    assert result["energisa_demand"]["demanded_power_kw"] == Decimal("6.36")
    old_digest = result["input_digest"]
    data["environments"][0]["loads"][1]["unit_power_w"] = "6000"
    changed = calculate(data)
    assert changed["input_digest"] != old_digest
    assert changed["energisa_demand"]["inventory_reviewed"] is False
    assert changed["normative"]["demand"]["value"] is None


@pytest.mark.parametrize(
    "change",
    [
        "quantity",
        "classification",
        "reserve",
        "utility",
        "state",
        "unit_type",
        "absent",
        "simultaneous",
        "signage",
        "add",
        "remove",
    ],
)
def test_review_is_bound_to_inventory_and_scope(change):
    data = study()
    before = reviewed(data)
    load = data["environments"][0]["loads"][0]
    settings = data["energisa_demand"]
    if change == "quantity":
        load["quantity"] = 2
    elif change == "classification":
        load["energisa_demand"]["group"] = "d4"
    elif change == "reserve":
        load["energisa_demand"]["reserve"] = True
    elif change == "utility":
        data["utility"] = "cpfl_paulista"
    elif change == "state":
        data["state"] = "MG"
    elif change == "unit_type":
        settings["unit_type"] = "grouped"
    elif change == "absent":
        settings["confirmed_absent_groups"].remove("d3")
    elif change == "simultaneous":
        settings["simultaneous_lighting_outlets"] = True
    elif change == "signage":
        settings["has_signage_or_display_lighting"] = True
    elif change == "add":
        data["environments"][0]["loads"].append({**deepcopy(load), "id": "new-load"})
    elif change == "remove":
        data["environments"][0]["loads"].pop()
    after = calculate(data)
    assert not after["energisa_demand"]["inventory_reviewed"]
    assert after["normative"]["demand"]["value"] is None
    assert before["normative"]["demand"]["value"] is not None


def test_unclassified_load_never_assumed_even_when_absence_is_declared():
    data = study()
    data["environments"][0]["loads"][0]["energisa_demand"] = None
    result = reviewed(data)["energisa_demand"]
    assert result["value"] is None and result["groups"] == []
    assert len(result["unclassified_load_ids"]) == 1


@pytest.mark.parametrize(
    "power,status",
    [("0", "pending"), (None, "pending"), ("75000", "estimated"), ("75000.000001", "out_of_scope")],
)
def test_scope_boundary_with_project_inventory(power, status):
    data = study()
    data["environments"][0]["loads"] = data["environments"][0]["loads"][:1]
    data["environments"][0]["loads"][0]["unit_power_w"] = power
    data["energisa_demand"]["confirmed_absent_groups"] = ["d2", "d3", "d4", "d5", "d6", "d7"]
    result = reviewed(data)["energisa_demand"]
    assert result["status"] == status
    assert (result["value"] is not None) == (status == "estimated")


@pytest.mark.parametrize(
    "group,ac", [("d6", "unconfirmed"), ("d7", "unconfirmed"), ("d5", "central_unit")]
)
def test_special_equipment_without_parameters_cannot_be_approved(group, ac):
    data = study()
    load = data["environments"][0]["loads"][0]
    load["energisa_demand"].update(group=group, air_conditioning_type=ac)
    result = reviewed(data)["energisa_demand"]
    assert result["status"] == "pending" and result["value"] is None


def test_absence_conflict_and_unconfirmed_scope_are_pending():
    data = study()
    data["energisa_demand"]["confirmed_absent_groups"].append("d2")
    assert reviewed(data)["normative"]["demand"]["value"] is None
    data = study()
    data["energisa_demand"]["unit_type"] = "unconfirmed"
    data["energisa_demand"]["has_signage_or_display_lighting"] = None
    assert reviewed(data)["energisa_demand"]["status"] == "pending"


def test_disabled_legacy_project_preserved_and_export_consistent():
    data = study()
    data.pop("energisa_demand")
    assert calculate(data)["energisa_demand"] is None
    data = study()
    result = reviewed(data)
    summary = build_summary(data, result)
    assert summary["atendimento_distribuidora"]["demanda_disponivel"]
    assert summary["demanda_revisada"]["inventory_reviewed"]
    assert summary["formato_versao"] == "1.4"
    # The report exercises long inventory rows and the group memory without recalculation.
    assert render_report(data, result).startswith(b"%PDF")
    restored = ProjectInput.model_validate(data).model_dump(mode="json")
    assert calculate(restored)["energisa_demand"]["inventory_reviewed"]


def test_reserve_excluded_from_demand_but_kept_in_installed_limit():
    data = study()
    data["environments"][0]["loads"][1]["energisa_demand"]["reserve"] = True
    data["energisa_demand"]["confirmed_absent_groups"].append("d2")
    result = reviewed(data)["energisa_demand"]
    assert result["status"] == "estimated"
    assert result["installed_power_w"] == Decimal("6500")
    assert result["demanded_power_kw"] == Decimal(".86")
    assert result["ignored_reserve_loads"] == ["Chuveiro"]
    data["environments"][0]["loads"][1]["unit_power_w"] = "75000"
    result = reviewed(data)["energisa_demand"]
    assert result["status"] == "out_of_scope" and result["value"] is None


def test_empty_inventory_and_mechanical_output_never_become_demand():
    data = study()
    data["environments"] = []
    data["energisa_demand"]["confirmed_absent_groups"] = ["d1", "d2", "d3", "d4", "d5", "d6", "d7"]
    result = reviewed(data)["energisa_demand"]
    assert result["status"] == "pending" and result["value"] is None
    data = study()
    data["environments"][0]["loads"][0]["parameters"]["power_mode"] = "mechanical"
    result = reviewed(data)["energisa_demand"]
    assert result["status"] == "pending" and result["value"] is None
    assert result["inventory"][0]["unit_power_w"] is None


def test_new_demand_parameters_are_saved_exported_and_invalidate_review():
    data = study()
    load = data["environments"][0]["loads"][0]
    load["energisa_demand"].update(
        group="d6",
        motor=dict(configuration="single_phase", shaft_power_cv="1", source="Placa de teste"),
    )
    data["energisa_demand"]["confirmed_absent_groups"] = ["d1", "d3", "d4", "d5", "d7"]
    result = reviewed(data)
    assert result["energisa_demand"]["groups"][5]["demand_w"] == Decimal("1095.2")
    restored = CalculationInput.model_validate(data).model_dump(mode="json")
    assert calculate(restored)["energisa_demand"]["inventory_reviewed"]
    assert (
        build_summary(data, result)["demanda_revisada"]["inventory"][0]["motor"]["shaft_power_cv"]
        == "1"
    )
    assert render_report(data, result).startswith(b"%PDF")
    for key, value in [
        ("configuration", "three_phase"),
        ("shaft_power_cv", "2"),
        ("source", "Outra fonte"),
    ]:
        changed = deepcopy(data)
        changed["environments"][0]["loads"][0]["energisa_demand"]["motor"][key] = value
        after = calculate(changed)["energisa_demand"]
        assert not after["inventory_reviewed"] and after["value"] is None
