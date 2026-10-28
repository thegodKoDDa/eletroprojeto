"""Export interpretation/coverage, independent of presentation and formulas."""

from decimal import Decimal

from app.calculations.engine import calculate
from app.reports.pdf import render_report
from app.reports.summary import build_summary
from app.schemas import CalculationInput, CalculationResult
from test_pdf import extract_pages


def sample():
    project = CalculationInput(
        name="Casa completa",
        municipality="Cidade",
        utility="energisa_sul_sudeste",
        analysis_scope="normative",
        energy_tariff_brl_per_kwh="0.8",
        environments=[
            dict(
                name="Quarto",
                type="bedroom",
                area_m2="12",
                perimeter_m="14",
                lighting_points=1,
                outlets=4,
                loads=[
                    dict(
                        name="LED",
                        quantity=4,
                        unit_power_w="9",
                        parameters=dict(usage_hours_per_day="5", usage_days_per_month=30),
                    )
                ],
            ),
            dict(
                name="Quarto",
                type="bedroom",
                area_m2="9",
                perimeter_m="12",
                lighting_points=1,
                outlets=3,
                loads=[
                    dict(
                        name="Geladeira",
                        quantity=2,
                        unit_power_w=None,
                        parameters=dict(
                            monthly_energy_kwh="40",
                            usage_hours_per_day="24",
                            usage_days_per_month=31,
                        ),
                    )
                ],
            ),
        ],
    ).model_dump(mode="json")
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    return project, result


def test_export_complete_energy_with_unknown_power_never_equates_kwh_to_w():
    project, result = sample()
    report = build_summary(project, result)
    assert Decimal(report["resultados"]["consumo_mensal"]["valor"]) == Decimal("85.4")
    assert Decimal(report["resultados"]["custo_mensal_estimado"]["valor"]) == Decimal("68.32")
    assert report["consumo"]["situacao"] == "estimado"
    assert report["consumo"]["cargas_com_estimativa"] == 2
    assert report["resultados"]["total_incompleto"]
    assert not report["resultados"]["consumo_incompleto"]
    assert report["equipamentos"][1]["potencia_unitaria_w"] is None
    assert report["equipamentos"][1]["consumo_unitario_informado_kwh"] == "40"
    assert report["equipamentos"][1]["horas_por_dia"] is None
    assert [Decimal(r["consumo_mensal_kwh"]) for r in report["ambientes"]] == [
        Decimal("5.4"),
        Decimal("80"),
    ]
    assert report["pendencias_consumo"] == []
    assert report["projeto"]["distribuidora"] == "Energisa Sul-Sudeste"
    assert "atendimento_distribuidora" not in report
    assert "previsoes_normativas" not in report
    text = "\n".join(extract_pages(render_report(project, result)))
    assert "85,4 kWh" in text and "R$ 68,32" in text
    assert "4 de 4" not in text
    assert "2 de 2" in text
    assert "5 h/dia; 30 dias/mês" in text
    assert "40 kWh/mês por unidade informado" in " ".join(text.split())
    assert "kWh/mês expressa consumo" in text
    assert "HTTP" not in text and "https://" not in text
    assert text.count("LED ·") == 1 and text.count("Geladeira ·") == 1


def test_export_distinguishes_missing_schedule_zero_empty_and_no_tariff():
    project, _ = sample()
    project["environments"][1]["loads"][0]["parameters"] = {}
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    report = build_summary(project, result)
    assert report["consumo"]["situacao"] == "parcial"
    assert report["consumo"]["cargas_sem_estimativa"] == 1
    assert report["pendencias_consumo"][0]["equipamento"] == "Geladeira"
    assert "horas" in report["pendencias_consumo"][0]["necessario"]
    assert "potência" in report["pendencias_consumo"][0]["necessario"]
    assert report["ambientes"][1]["consumo_mensal_kwh"] is None
    project["environments"] = project["environments"][:1]
    project["environments"][0]["loads"][0]["parameters"]["usage_hours_per_day"] = "0"
    project["energy_tariff_brl_per_kwh"] = "0"
    report = build_summary(
        project, CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    )
    assert report["resultados"]["consumo_mensal"]["valor"] == "0"
    assert report["resultados"]["custo_mensal_estimado"]["valor"] == "0"
    assert report["consumo"]["situacao"] == "estimado"
    project["environments"] = []
    report = build_summary(
        project, CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    )
    assert report["consumo"]["situacao"] == "nao_estimado"
    assert report["resultados"]["consumo_mensal"]["valor"] is None
    assert report["consumo"]["cargas_cadastradas"] == 0
    assert report["resultados"]["consumo_mensal"]["unidade"] == "kWh"
    assert report["resultados"]["potencia_aparente_soma_escalar"]["unidade"] == "VA"
    assert report["resultados"]["potencia_aparente_kva"]["unidade"] == "kVA"


def test_export_manual_values_and_duplicate_room_names_are_preserved():
    project, _ = sample()
    load = project["environments"][0]["loads"][0]
    load.update(
        unit_power_w="12",
        manual_override=True,
        power_user_edited=True,
        power_origin="user_estimate",
    )
    report = build_summary(
        project, CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    )
    assert report["equipamentos"][0]["potencia_unitaria_w"] == "12"
    assert report["equipamentos"][0]["potencia_total_w"] == "48"
    assert report["equipamentos"][0]["potencia_personalizada"]
    assert report["equipamentos"][0]["consumo_mensal_kwh"] == "7.2"


def test_export_power_edit_is_independent_of_usage_voltage_and_reference_edits():
    from app.catalog import CATALOG

    project, _ = sample()
    load = project["environments"][0]["loads"][0]
    reference = next(item for item in CATALOG if item["id"] == "samsung-tv43-au7700")
    load.update(
        unit_power_w="130",
        voltage_v="127",
        manual_override=True,
        power_user_edited=False,
        catalog_reference=reference,
    )
    project.update(floors=1, residence_type="Casa térrea")
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    report = build_summary(project, result)
    item = report["equipamentos"][0]
    assert not item["potencia_personalizada"]
    assert item["dados_personalizados"]
    assert "máxima" in item["tipo_potencia"]
    assert item["id"] == load["id"]
    assert item["ambiente_id"] == report["ambientes"][0]["id"]
    assert report["ambientes"][0]["id"] != report["ambientes"][1]["id"]
    assert report["projeto"]["pavimentos"] == 1
    assert report["projeto"]["tipo_residencia"] == "Casa térrea"
    assert "constante" in item["premissa_consumo"]
    assert result["monthly_cost"]["value"] == report["resultados"]["custo_mensal_estimado"]["valor"]
    text = " ".join("\n".join(extract_pages(render_report(project, result))).split())
    assert "Casa térrea" in text and "Pavimentos: 1" in text
    assert "máxima de referência" in text
    load["unit_power_w"] = "100"
    report = build_summary(
        project, CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    )
    assert report["equipamentos"][0]["potencia_personalizada"]
    assert "manualmente" in report["equipamentos"][0]["tipo_potencia"]
