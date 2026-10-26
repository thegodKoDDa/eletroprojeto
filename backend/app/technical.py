"""Reviewed metadata, never an implicit authorization to execute normative rules."""

import hashlib
import json
from dataclasses import asdict

from .calculations.standards import ENERGISA_V7_EVIDENCE, RULES
from .catalog import CATALOG
from .version import ENGINE_VERSION

STATES = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
DOCUMENTS = [
    dict(
        id="nbr5410",
        title="ABNT NBR 5410",
        edition="2004, versão corrigida 2008",
        effective_date=None,
        source="https://www.abntcatalogo.com.br/",
        status="residential_clauses_reviewed_limited_scope",
    ),
    dict(
        id="ndu001",
        title="Energisa NDU-001",
        edition="7.0",
        effective_date="2024-11-01",
        source="https://www.energisa.com.br/normas-tecnicas",
        status="user_full_text_reviewed_limited_residential_method",
        source_file=ENERGISA_V7_EVIDENCE.file_name,
        sha256=ENERGISA_V7_EVIDENCE.sha256,
    ),
    dict(
        id="ged13",
        title="CPFL GED-13",
        edition=None,
        effective_date=None,
        source="https://www.cpfl.com.br/normas-tecnicas",
        status="edition_review_pending",
    ),
    dict(
        id="edp_sp",
        title="EDP fornecimento em tensão secundária",
        edition=None,
        effective_date=None,
        source="https://www.edp.com.br/normas-e-padroes-tecnicos/",
        status="edition_review_pending",
    ),
    dict(
        id="enel_sp",
        title="Enel São Paulo — normas técnicas",
        edition=None,
        effective_date=None,
        source="https://www.enel.com.br/pt-saopaulo/normas-tecnicas.html",
        status="document_review_pending",
    ),
    dict(
        id="elektro",
        title="Neoenergia Elektro — fornecimento em tensão secundária",
        edition="06 (aprovação 05/11/2025)",
        effective_date=None,
        source="https://www.neoenergia.com/documents/d/rn/dis_nor_030_fornecimento_de_energia_eletrico-pdf?download=true",
        status="official_full_text_method_review_pending",
    ),
]
DOCUMENTS.append(
    dict(
        id="ndu001_legacy63",
        title="Energisa NDU-001 — referência histórica substituída",
        edition="6.3 (outubro/2020), com erratas/adendos até novembro/2023",
        effective_date=None,
        source="https://www.energisa.com.br/normas-tecnicas",
        status="superseded_by_7.0_historical_comparison_only",
        consulted_on="2026-10-23",
        source_file="NDU 001 - Versão 6.3.pdf",
        sha256="733fb17b8597e36ef325c0c5aefa7d54ebc27e97fc45298eb3073d27ae3253ba",
    )
)
UTILITIES = [
    dict(
        id=code,
        name=name,
        states=["SP"],
        document_ids=["nbr5410", document],
        status="awaiting_technical_validation",
        municipality_mapping="unverified",
    )
    for code, name, document in [
        ("energisa_sul_sudeste", "Energisa Sul-Sudeste", "ndu001"),
        ("cpfl_paulista", "CPFL Paulista", "ged13"),
        ("cpfl_piratininga", "CPFL Piratininga", "ged13"),
        ("cpfl_santa_cruz", "CPFL Santa Cruz", "ged13"),
        ("neoenergia_elektro", "Neoenergia Elektro", "elektro"),
        ("enel_sp", "Enel São Paulo", "enel_sp"),
        ("edp_sp", "EDP São Paulo", "edp_sp"),
    ]
]
for document in DOCUMENTS:
    document["consulted_on"] = (
        "2026-10-22" if document["id"] in ("nbr5410", "ndu001") else "2026-10-21"
    )
    if document["id"] == "elektro":
        document["consulted_on"] = "2026-10-23"
    if document["id"] in ("ndu001", "ndu001_legacy63"):
        document["consulted_on"] = "2026-10-23"
for utility in UTILITIES:
    if utility["id"] == "neoenergia_elektro":
        utility["states"] = ["SP", "MS"]  # DIS-NOR-030 rev06 §5.1; no municipal inference.

# These are state-level candidates, NOT a verified municipality/concession mapping.
REGIONAL_METHODS = [
    dict(
        code="energisa_ndu001_v7_residential",
        supported_utilities=["energisa_sul_sudeste"],
        supported_states=["SP"],
        endpoint="/api/v1/calculations/energisa-demand",
        status="estimated",
        available=True,
        scope="Residência individual, Energisa Sul-Sudeste/SP, até75kW; d1–d7 classificados explicitamente, d6/d7/centrais com parâmetros próprios e fontes. Integrado ao cadastro mediante revisão; sem dimensionamento final.",
        reference=asdict(ENERGISA_V7_EVIDENCE),
    )
]


def snapshot():
    from .validation import requirements

    return dict(
        field_requirements=requirements(),
        documents=DOCUMENTS,
        utilities=UTILITIES,
        rules=[asdict(rule) for rule in RULES],
        mathematical_rules=MATHEMATICAL_RULES,
        equipment=CATALOG,
        regional_methods=REGIONAL_METHODS,
    )


def registry_version():
    return hashlib.sha256(
        json.dumps(snapshot(), sort_keys=True, ensure_ascii=False, default=str).encode()
    ).hexdigest()


def applicability(utility: str, state: str = "SP"):
    if utility == "unconfirmed":
        return dict(
            utility=utility,
            state=state,
            status="pending",
            documents=[doc for doc in DOCUMENTS if doc["id"] == "nbr5410"],
            reason="Concessionária não confirmada. Confirme a distribuidora para identificar sua norma de demanda; a validação da regra será informada separadamente.",
        )
    selected = next((item for item in UTILITIES if item["id"] == utility), None)
    compatible = selected is not None and state in selected["states"]
    ids = selected["document_ids"] if compatible else ["nbr5410"]
    return dict(
        utility=utility,
        state=state,
        status="pending"
        if utility == "energisa_sul_sudeste" and state == "SP"
        else "awaiting_technical_validation"
        if compatible
        else "out_of_scope",
        documents=[doc for doc in DOCUMENTS if doc["id"] in ids],
        reason="Método NDU-001 7.0 d1–d7 disponível com classificação e revisão explícitas; não valida território ou dimensionamento final."
        if utility == "energisa_sul_sudeste" and state == "SP"
        else "Norma selecionada, mas cálculo específico ainda não validado."
        if compatible
        else "Distribuidora/estado selecionados ainda sem cobertura verificada. Nenhuma regra de outra distribuidora foi aplicada.",
    )


def normative_capabilities(utility: str, state: str = "SP") -> list[dict]:
    """Implementation availability and reviewed scope; distinct from input completeness."""
    context = applicability(utility, state)
    capabilities = []
    for rule in RULES:
        evidence = [asdict(item) for item in rule.evidence]
        status, reason, checks = rule.status, rule.reason, list(rule.pending_checks)
        if rule.code == "demand" and not (utility == "energisa_sul_sudeste" and state == "SP"):
            status = context["status"]
            reason = (
                "Distribuidora não identificada; cálculo de demanda ainda indisponível neste estudo."
                if utility == "unconfirmed"
                else context["reason"]
            )
            evidence = [
                dict(
                    title=doc["title"],
                    url=doc["source"],
                    finding="Referência documental identificada; procedimento de demanda não habilitado.",
                    access="official_metadata",
                    consulted_on=doc["consulted_on"],
                    section=None,
                )
                for doc in context["documents"]
                if doc["id"] != "nbr5410"
            ]
            checks = [
                "Conferir a fonte oficial completa e o método específico desta distribuidora.",
                "Validar condições, limites e exemplos independentes antes de implementar.",
            ]
            if utility == "neoenergia_elektro" and state in ("SP", "MS"):
                evidence[0].update(
                    finding="Íntegra oficial rev06 acessível; escopo e exemplos de demanda lidos. Remissões e exemplos divergentes ainda exigem revisão antes da implementação.",
                    access="official_full_text",
                    section="§§4,5.1,6.26–6.28; anexos I/II",
                )
                checks = [
                    "Conferir erratas e divergências entre texto, tabelas e exemplos das parcelas b, d e j.",
                    "Revisar enquadramento trifásico, base de carga, agrupamentos e todas as notas; testar limites e exemplos independentes.",
                ]
        capabilities.append(
            dict(
                code=rule.code,
                label=rule.label,
                purpose=rule.purpose,
                available=rule.procedure is not None
                and (
                    rule.code != "demand" or (utility == "energisa_sul_sudeste" and state == "SP")
                ),
                status=status,
                reason=reason,
                evidence=evidence,
                pending_checks=checks,
            )
        )
    if utility == "energisa_sul_sudeste" and state == "SP":
        for capability in capabilities:
            if capability["code"] == "demand":
                capability.update(
                    available=True,
                    status="estimated",
                    reason="Método NDU-001 7.0 §9.1 d1–d7 disponível mediante classificação e revisão explícitas no painel de demanda.",
                    evidence=[asdict(ENERGISA_V7_EVIDENCE)],
                    pending_checks=["Confirmar escopo e revisar inventário no painel de demanda."],
                )
    return capabilities


def integrity():
    issues = []
    ids = set()
    for item in CATALOG:
        if item["id"] in ids:
            issues.append(f"ID duplicado: {item['id']}")
        ids.add(item["id"])
        if item.get("reference_power_w") is not None and not all(
            item.get(k) for k in ("source_url", "document", "verified_on")
        ):
            issues.append(f"Referência incompleta: {item['id']}")
    return dict(
        registry_version=registry_version(),
        issues=issues,
        structural_integrity=not issues,
        notice="Integridade estrutural não verifica disponibilidade de links nem valida regras normativas.",
    )


MATHEMATICAL_RULES = [
    dict(
        id=code,
        procedure=formula,
        inputs=inputs,
        output_unit=unit,
        implementation_version=ENGINE_VERSION,
        validation="mathematical_tests_passed",
        normative=False,
        conditions=condition,
        tests=tests,
    )
    for code, formula, inputs, unit, condition, tests in [
        (
            "installed_power",
            "quantity * electrical_input_w",
            ["quantity", "electrical_input_w"],
            "W",
            "Potência elétrica de entrada; cada instância contada uma vez.",
            ["tests/test_math.py"],
        ),
        (
            "apparent_power",
            "active_power_w / power_factor",
            ["active_power_w", "power_factor"],
            "VA",
            "FP total conhecido e 0 < FP <= 1; não presumir FP de eletrônicos.",
            ["tests/test_math.py"],
        ),
        (
            "single_phase_current",
            "active_power_w / (voltage_v * power_factor)",
            ["active_power_w", "voltage_v", "power_factor"],
            "A",
            "Carga monofásica; tensão nos terminais; não dimensiona proteção.",
            ["tests/test_math.py"],
        ),
        (
            "balanced_three_phase_current",
            "active_power_w / (sqrt(3) * line_voltage_v * power_factor)",
            ["active_power_w", "line_voltage_v", "power_factor"],
            "A",
            "Carga trifásica equilibrada; tensão entre fases.",
            ["tests/test_math.py"],
        ),
        (
            "motor_input",
            "mechanical_output_w / efficiency",
            ["mechanical_output_w", "efficiency"],
            "W",
            "Rendimento do motor conhecido; 0 < rendimento <= 1.",
            ["tests/test_equipment.py"],
        ),
        (
            "monthly_energy",
            "quantity * power_w * hours_per_day * days / 1000",
            ["quantity", "power_w", "hours_per_day", "days"],
            "kWh",
            "Potência constante; etiqueta/medição mensal unitária prevalece quando informada. Sem ciclo presumido.",
            ["tests/test_energy.py"],
        ),
        (
            "monthly_cost",
            "monthly_energy_kwh * tariff_brl_per_kwh",
            ["monthly_energy_kwh", "tariff_brl_per_kwh"],
            "BRL",
            "Estimativa pela tarifa informada; não equivale à fatura completa.",
            ["tests/test_energy.py"],
        ),
        (
            "thermal_capacity",
            "btu_it_per_hour * 1055.05585262 / 3600",
            ["btu_it_per_hour"],
            "W térmico",
            "Conversão térmica; nunca determina consumo elétrico.",
            ["tests/test_equipment.py"],
        ),
    ]
]
