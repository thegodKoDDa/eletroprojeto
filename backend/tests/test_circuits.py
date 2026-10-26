from copy import deepcopy
from decimal import Decimal as D

import pytest
from app.calculations.circuits import calculate_circuits, voltage_drop
from app.calculations.service_entry import service_entry
from app.schemas import CalculationInput


def setup_circuit():
    circuit = dict(
        id="c1",
        name="Tomadas",
        purpose="sockets",
        load_ids=["l1"],
        method="B1",
        voltage_v="220",
        length_m="30",
        ambient_temperature_c=30,
        grouped_circuits=1,
        scope_confirmed=True,
        voltage_drop_model_confirmed=True,
        overload_duration_confirmed=True,
        breaker_ratings_a=["16", "25", "40"],
        breaker_i2_factor="1.45",
        breaker_source="Dados do fabricante informados para o estudo",
        prospective_short_circuit_ka="3",
        breaking_capacity_ka="6",
        supply_origin="public_lv_delivery",
        upstream_drop_percent="0",
    )
    load = dict(
        id="l1",
        name="Carga",
        quantity=1,
        voltage_v="220",
        power_factor="1",
        parameters={"configuration": "single_phase"},
    )
    project = dict(circuits=[circuit], environments=[dict(loads=[load])])
    result = [dict(load_id="l1", electrical_input_w=D(4400))]
    return project, result


def test_independent_resistive_example_20a_and_30m():
    project, loads = setup_circuit()
    row = calculate_circuits(project, loads)[0]
    assert row["design_current_a"] == 20
    assert row["breaker_a"] == 25
    assert row["phase_section_mm2"] == 4
    assert row["capacity_a"] == 32
    assert row["pe_section_mm2"] == 4
    assert row["voltage_drop_v"] == D("6.75")
    assert row["breaking_capacity_ok"] is True
    assert row["pending_checks"]  # Never final installation approval.


def test_mixed_power_factors_use_vector_sum_and_preserve_input():
    project, resolved = setup_circuit()
    first = project["environments"][0]["loads"][0]
    first["power_factor"] = ".6"
    second = {**deepcopy(first), "id": "l2", "power_factor": "1"}
    project["environments"][0]["loads"].append(second)
    project["circuits"][0]["load_ids"].append("l2")
    resolved = [
        dict(load_id="l1", electrical_input_w=D(1320)),
        dict(load_id="l2", electrical_input_w=D(1980)),
    ]
    before = deepcopy(project)
    row = calculate_circuits(project, resolved)[0]
    # Independent 8–15–17 triangle: P/U=15A; Q/U=8A; S/U=17A.
    assert row["design_current_a"] == D(17)
    assert abs(row["power_factor"] * 17 - 15) < D("1e-26")
    assert project == before


def test_capacity_equality_and_just_above_boundary():
    project, resolved = setup_circuit()
    project["circuits"][0].update(breaker_ratings_a=["24"], length_m="1")
    resolved[0]["electrical_input_w"] = D(5280)
    row = calculate_circuits(project, resolved)[0]
    assert row["design_current_a"] == row["breaker_a"] == row["capacity_a"] == 24
    assert row["phase_section_mm2"] == D("2.5")
    resolved[0]["electrical_input_w"] = D("5280.000001")
    row = calculate_circuits(project, resolved)[0]
    assert row["breaker_a"] is None and row["phase_section_mm2"] is None


def test_group_temperature_boundary_and_duration_condition():
    project, loads = setup_circuit()
    circuit = project["circuits"][0]
    circuit.update(ambient_temperature_c=40, grouped_circuits=3)
    row = calculate_circuits(project, loads)[0]
    # 6mm²:41*.87*.70=24.969 <25A; 10mm²:34.713A.
    assert row["phase_section_mm2"] == 10
    assert row["capacity_a"] == D("34.713")
    circuit["overload_duration_confirmed"] = False
    assert calculate_circuits(project, loads)[0]["phase_section_mm2"] == 16


def test_total_drop_constraint_and_model_no_intermediate_rounding():
    project, loads = setup_circuit()
    project["circuits"][0]["upstream_drop_percent"] = "4"
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] == 16
    assert row["voltage_drop_v"] == D("1.6875")
    assert row["total_drop_percent"] < 5
    assert voltage_drop(D(20), D(".8"), D(30), D(4)) == D("5.45760000")


@pytest.mark.parametrize(
    "field,value",
    [
        ("scope_confirmed", False),
        ("method", "unknown"),
        ("ambient_temperature_c", None),
        ("breaker_i2_factor", None),
    ],
)
def test_incomplete_inputs_never_produce_cable_selection(field, value):
    project, loads = setup_circuit()
    project["circuits"][0][field] = value
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] is None
    assert row["pending_checks"]


def test_missing_power_quantity_and_cross_circuit_duplicate():
    project, loads = setup_circuit()
    loads[0]["electrical_input_w"] = None
    assert calculate_circuits(project, loads)[0]["design_current_a"] is None
    loads[0]["electrical_input_w"] = D(2200)
    project["environments"][0]["loads"][0]["quantity"] = 2
    assert calculate_circuits(project, loads)[0]["design_current_a"] == 20
    second = deepcopy(project["circuits"][0])
    second["id"] = "c2"
    project["circuits"].append(second)
    rows = calculate_circuits(project, loads)
    assert all(row["status"] == "invalid" and row["phase_section_mm2"] is None for row in rows)


def test_voltage_mismatch_and_breaking_capacity_failure():
    project, loads = setup_circuit()
    project["environments"][0]["loads"][0]["voltage_v"] = "127"
    assert calculate_circuits(project, loads)[0]["design_current_a"] is None
    project["environments"][0]["loads"][0]["voltage_v"] = "220"
    project["circuits"][0]["breaking_capacity_ka"] = "2"
    row = calculate_circuits(project, loads)[0]
    assert row["breaking_capacity_ok"] is False
    assert any("inferior" in item for item in row["pending_checks"])


def service_project():
    return dict(
        utility="energisa_sul_sudeste",
        state="SP",
        environments=[dict(loads=[dict(voltage_v="127")])],
        service_entry=dict(
            network="220_127",
            route="embedded",
            insulation="PVC70",
            scope_confirmed=True,
            special_loads_reviewed=True,
            requested_phases=None,
        ),
    )


@pytest.mark.parametrize(
    "watts,category,section",
    [
        (3800, "M1", 6),
        (3801, "M2", 10),
        (6300, "M2", 10),
        (6301, "M3", 16),
        (8800, "M3", 16),
        (8801, "B1", 10),
        (10100, "B1", 10),
        (10101, "B2", 16),
        (12700, "B2", 16),
        (12701, "B3", 25),
        (17700, "B3", 25),
    ],
)
def test_entry_table16_boundaries(watts, category, section):
    row = service_entry(service_project(), D(watts), [], None)
    assert row["category"] == category
    assert row["minimum_phase_mm2"] == section
    assert row["pending_checks"]


def test_entry_trifasico_requires_reviewed_demand_and_subterranean_insulation():
    project = service_project()
    assert service_entry(project, D(18000), [], None)["category"] is None
    project["service_entry"].update(insulation="XLPE90", route="underground")
    row = service_entry(project, D(18000), [], dict(value="15.2", pending_checks=[]))
    assert (row["category"], row["minimum_phase_mm2"], row["minimum_neutral_mm2"]) == ("T1", 10, 10)
    row = service_entry(project, D(18000), [], dict(value="15.200001", pending_checks=[]))
    assert row["category"] == "T2"
    project["service_entry"]["insulation"] = "PVC70"
    assert (
        service_entry(project, D(18000), [], dict(value="15.2", pending_checks=[]))["category"]
        is None
    )
    project["utility"] = "cpfl_paulista"
    assert service_entry(project, D(1000), [], None)["status"] == "out_of_scope"


def test_project_contract_rejects_duplicate_circuit_ids():
    with pytest.raises(ValueError, match="circuitos"):
        CalculationInput(circuits=[dict(id="same"), dict(id="same")])


def test_short_energy_tn_and_tt_checks_use_explicit_product_data():
    from app.calculations.protections import protection_checks

    data = dict(
        source="Curvas QA independentes",
        device_rated_a="25",
        cable_k="115",
        let_through_a2s="211600",
        short_duration_s="0.1",
        earthing_system="TN",
        phase_earth_voltage_v="127",
        tn_situation=1,
        fault_loop_ohm="1",
        trip_current_a="100",
        trip_time_s="0.8",
        rcd_additional_required=True,
        rcd_sensitivity_ma="30",
        rcd_type_compatible_confirmed=True,
    )
    checks = {c["code"]: c for c in protection_checks(data, D(4), D(25))}
    assert checks["thermal_short"]["value"] == D(211600)
    assert checks["thermal_short"]["passed"] is True
    assert checks["shock_tn"]["passed"] is True
    assert checks["additional_rcd"]["passed"] is True
    data["trip_time_s"] = "0.800001"
    assert protection_checks(data, D(4), D(25))[1]["passed"] is False
    data.update(earthing_system="TT", tt_ra_ohm="1000", touch_limit_v=25)
    checks = {c["code"]: c for c in protection_checks(data, D(4), D(25))}
    assert checks["shock_tt"]["value"] == 30
    assert checks["shock_tt"]["passed"] is False
    data["touch_limit_v"] = 50
    assert protection_checks(data, D(4), D(25))[1]["passed"] is True
    data["device_rated_a"] = "16"
    assert protection_checks(data, D(4), D(25))[0]["passed"] is None


def test_short_thermal_constraint_increases_section_before_returning_candidate():
    project, loads = setup_circuit()
    project["circuits"][0]["protections"] = dict(
        source="Curva do produto",
        device_rated_a="25",
        cable_k="115",
        let_through_a2s="900000",
        short_duration_s=".1",
    )
    row = calculate_circuits(project, loads)[0]
    assert row["phase_section_mm2"] == 10
    assert row["protection_checks"][0]["passed"] is True


def test_engine_json_and_pdf_include_circuits_without_unknown_as_zero():
    from app.calculations.engine import calculate
    from app.reports.pdf import render_report
    from app.reports.summary import build_summary

    pdf = pytest.importorskip("pymupdf")
    _, resolved = setup_circuit()
    circuit = setup_circuit()[0]["circuits"][0]
    circuit["load_ids"] = ["22222222-2222-4222-8222-222222222222"]
    project = CalculationInput(
        name="Circuito de verificação",
        municipality="Município QA",
        circuits=[circuit],
        environments=[
            dict(
                id="11111111-1111-4111-8111-111111111111",
                name="Ambiente",
                loads=[
                    dict(
                        id=circuit["load_ids"][0],
                        name="Carga",
                        category="Outros",
                        quantity=1,
                        unit_power_w="4400",
                        voltage_v="220",
                        power_factor="1",
                        parameters=dict(configuration="single_phase"),
                    )
                ],
            )
        ],
    ).model_dump(mode="json")
    result = calculate(project)
    assert result["circuit_results"][0]["phase_section_mm2"] == 4
    summary = build_summary(project, result)
    assert summary["formato_versao"] == "1.4"
    assert summary["circuitos"][0]["breaker_a"] == 25
    data = render_report(project, result)
    with pdf.open(stream=data, filetype="pdf") as document:
        text = "\n".join(page.get_text() for page in document)
    assert "Estudo de circuitos" in text
    assert "fase=4" in text
    assert "None" not in text


@pytest.mark.parametrize(
    "method,section,capacity,pe",
    [
        ("B1", "50", "151", "25"),
        ("B1", "70", "192", "35"),
        ("B1", "95", "232", "50"),
        ("B2", "50", "133", "25"),
        ("B2", "70", "168", "35"),
        ("B2", "95", "201", "50"),
    ],
)
def test_extended_capacity_exact_limit_and_protective_conductor(method, section, capacity, pe):
    # Manual Prysmian2010 p52, table2 B1/B2 two loaded conductors.
    # At In=Iz and I2=1.45In, the exact capacity must be accepted.
    # Table58: S>35 requires PE>=S/2; 95/2=47.5 -> next standard size50.
    project, resolved = setup_circuit()
    circuit = project["circuits"][0]
    circuit.update(method=method, breaker_ratings_a=[capacity], length_m="1")
    resolved[0]["electrical_input_w"] = D(capacity) * D(220)
    before = deepcopy(project)
    row = calculate_circuits(project, resolved)[0]
    assert row["phase_section_mm2"] == D(section)
    assert row["capacity_a"] == D(capacity)
    assert row["pe_section_mm2"] == D(pe)
    assert project == before
    # Just above each capacity, the smaller section cannot be selected.
    above = D(capacity) + D(".000001")
    circuit["breaker_ratings_a"] = [str(above)]
    resolved[0]["electrical_input_w"] = above * D(220)
    row = calculate_circuits(project, resolved)[0]
    if section == "95":
        assert row["phase_section_mm2"] is None
        assert row["pe_section_mm2"] is None
        assert any("até95mm²" in message for message in row["pending_checks"])
    else:
        assert row["phase_section_mm2"] > D(section)


def test_extended_capacity_still_applies_grouping_temperature_and_unknowns():
    project, resolved = setup_circuit()
    circuit = project["circuits"][0]
    # B1 50:151*.87*.8=105.096<110; 70:192*.87*.8=133.632A.
    circuit.update(
        method="B1",
        breaker_ratings_a=["110"],
        length_m="1",
        ambient_temperature_c=40,
        grouped_circuits=2,
    )
    resolved[0]["electrical_input_w"] = D(24200)
    row = calculate_circuits(project, resolved)[0]
    assert row["phase_section_mm2"] == D(70)
    assert row["capacity_a"] == D("133.632")
    resolved[0]["electrical_input_w"] = None
    row = calculate_circuits(project, resolved)[0]
    assert row["phase_section_mm2"] is None
    assert row["pe_section_mm2"] is None


@pytest.mark.parametrize(
    "method,phase,capacity,section",
    [
        ("A1", False, "19.5", "2.5"),
        ("A2", False, "18.5", "2.5"),
        ("C", False, "27", "2.5"),
        ("A1", True, "18", "2.5"),
        ("A2", True, "17.5", "2.5"),
        ("B1", True, "21", "2.5"),
        ("B2", True, "20", "2.5"),
        ("C", True, "24", "2.5"),
        ("A1", True, "164", "95"),
        ("A2", True, "150", "95"),
        ("B1", True, "207", "95"),
        ("B2", True, "179", "95"),
        ("C", True, "223", "95"),
    ],
)
def test_reviewed_table36_capacity_at_equality_and_above(method, phase, capacity, section):
    project, resolved = setup_circuit()
    c = project["circuits"][0]
    load = project["environments"][0]["loads"][0]
    c.update(method=method, breaker_ratings_a=[capacity], length_m="0.01")
    resolved[0]["electrical_input_w"] = D("100")
    if phase:
        c["configuration"] = "balanced_three_phase_without_neutral"
        load["parameters"]["configuration"] = "balanced_three_phase"
    row = calculate_circuits(project, resolved)[0]
    assert row["phase_section_mm2"] == D(section)
    assert row["capacity_a"] == D(capacity)
    c["breaker_ratings_a"] = [str(D(capacity) + D(".000001"))]
    bigger = calculate_circuits(project, resolved)[0]
    assert (
        bigger["phase_section_mm2"] is None
        if section == "95"
        else bigger["phase_section_mm2"] > D(section)
    )


def test_balanced_three_phase_current_and_voltage_drop_independent_resistive_example():
    from decimal import localcontext

    project, resolved = setup_circuit()
    c = project["circuits"][0]
    load = project["environments"][0]["loads"][0]
    c.update(
        configuration="balanced_three_phase_without_neutral",
        method="B1",
        voltage_v="220",
        length_m="30",
    )
    load["parameters"]["configuration"] = "balanced_three_phase"
    resolved[0]["electrical_input_w"] = D("6600")
    row = calculate_circuits(project, resolved)[0]
    with localcontext() as ctx:
        ctx.prec = 40
        assert abs(row["design_current_a"] - D(30) / D(3).sqrt()) < D("1e-36")
    assert row["breaker_a"] == 25 and row["phase_section_mm2"] == 4
    assert abs(row["voltage_drop_v"] - D("5.0625")) < D("1e-36")


def test_phase_mixture_never_sizes_and_legacy_configuration_is_preserved():
    project, resolved = setup_circuit()
    legacy = calculate_circuits(project, resolved)
    project["circuits"][0]["configuration"] = "single_phase"
    assert calculate_circuits(project, resolved) == legacy
    project["circuits"][0]["configuration"] = "balanced_three_phase_without_neutral"
    row = calculate_circuits(project, resolved)[0]
    assert row["design_current_a"] is None and row["phase_section_mm2"] is None
