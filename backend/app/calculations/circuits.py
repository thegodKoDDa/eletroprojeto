"""Reviewed residential subset, never a blanket installation approval.

NBR5410:2004 table36 (Cu/PVC70, B1/B2, 2 loaded conductors), table40,
42 row1,47 and58; §§5.3.4.1/6.2.7. Prysmian LV Information2024 §5
voltage-drop estimate, non-magnetic conduit, sinusoidal single-phase loads.
"""

from collections import Counter
from decimal import Decimal, localcontext

from .protections import protection_checks

D = Decimal
SECTIONS = tuple(map(D, ("1.5", "2.5", "4", "6", "10", "16", "25", "35", "50", "70", "95")))
CAPACITIES = {
    "B1": tuple(map(D, ("17.5", "24", "32", "41", "57", "76", "101", "125", "151", "192", "232"))),
    "B2": tuple(map(D, ("16.5", "23", "30", "38", "52", "69", "90", "111", "133", "168", "201"))),
}
TEMPERATURE = {
    int(t): D(f)
    for t, f in [
        (10, "1.22"),
        (15, "1.17"),
        (20, "1.12"),
        (25, "1.06"),
        (30, "1"),
        (35, ".94"),
        (40, ".87"),
        (45, ".79"),
        (50, ".71"),
        (55, ".61"),
        (60, ".50"),
    ]
}
GROUPING = tuple(map(D, ("1", ".80", ".70", ".65", ".60", ".57", ".54", ".52")))
REFERENCE = "NBR5410:2004/VC2008: tabelas36/40/42(linha1)/47/58; §§5.3.4.1 e6.2.7. Manual Prysmian2010 pp.38/52/56, tabelas2/6/7. Prysmian Electrical Information2024 §5, p.34."
SOURCES = [
    "https://www.abntcatalogo.com.br/",
    "https://www.ipaam.am.gov.br/wp-content/uploads/2021/01/NBR-05410-05-Instala%C3%A7%C3%B5es-El%C3%A9tricas-de-baixa-Tens%C3%A3o.pdf",
    "https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/18451/material/nbr_5410.pdf",
    "https://asean.prysmian.com/sites/asean.prysmian.com/files/media/documents/241218%20-%20Prysmian%20Electrical%20Information%20for%20Low%20Voltage%20Cables.pdf",
    "https://br.prysmian.com/sites/br.prysmian.com/files/media/documents/Manual_Instalacoes_Eletricas.pdf",
]
LIMITATIONS = [
    "Escopo: cobre/PVC70°C, B1/B2, seções de1,5 a95mm²,2condutores carregados,50/60Hz, cargas senoidais monofásicas, conduto não magnético, PE no mesmo conduto e agrupamento homogêneo.",
    "Queda estimada em regime, concentrando cargas na extremidade; partida de motores, harmônicas, curto térmico, desligamento automático, DR/DPS, seletividade e geometria exigem verificações próprias.",
    "Resultados não autorizam execução nem certificam conformidade final.",
]


def circuit_current(circuit, loads, results):
    if not circuit.get("load_ids"):
        return None, None, "Associe ao menos uma carga ao circuito."
    voltage = circuit.get("voltage_v")
    if voltage is None:
        return None, None, "Informe a tensão do circuito."
    voltage = D(str(voltage))
    if voltage > 1000:
        return None, None, "Tensão acima de1000Vca fora deste escopo de baixa tensão."
    active = D(0)
    reactive = D(0)
    for key in circuit["load_ids"]:
        load = loads.get(key)
        result = results.get(key)
        if load is None or result is None:
            return None, None, "Carga associada foi removida ou não foi resolvida."
        if load.get("voltage_v") is None or D(str(load["voltage_v"])) != voltage:
            return None, None, "Confirme tensão de cada carga igual à do circuito."
        params = load.get("parameters") or {}
        if params.get("configuration") != "single_phase":
            return None, None, "Somente cargas explicitamente monofásicas são abrangidas."
        pf = D(1) if params.get("assume_resistive") else load.get("power_factor")
        power = result.get("electrical_input_w")
        if pf is None or power is None or D(str(power)) <= 0:
            return (
                None,
                None,
                "Potência/FP de uma carga desconhecido; nenhum subtotal dimensiona o circuito.",
            )
        pf = D(str(pf))
        power = D(str(power)) * load["quantity"]
        if not D(0) < pf <= D(1):
            return None, None, "FP inválido."
        active += power
        reactive += power * (D(1) - pf * pf).sqrt() / pf
    apparent = (active * active + reactive * reactive).sqrt()
    return apparent / voltage, active / apparent, None


def voltage_drop(current, pf, length, section):
    """Prysmian2024 §5: rho=.0225Ωmm²/m, lambda=.00008Ω/m.

    Explicit model acknowledgement required by caller. No assumed FP.
    """
    return (
        D(2)
        * length
        * current
        * (D(".0225") / section * pf + D(".00008") * (D(1) - pf * pf).sqrt())
    )


def calculate_circuits(project, load_results):
    loads = {load["id"]: load for room in project.get("environments", []) for load in room["loads"]}
    results = {row["load_id"]: row for row in load_results}
    output = []
    assignments = Counter(
        key for circuit in project.get("circuits", []) for key in circuit.get("load_ids", [])
    )
    with localcontext() as ctx:
        ctx.prec = 40
        for circuit in project.get("circuits", []):
            row = dict(
                circuit_id=circuit["id"],
                name=circuit["name"],
                status="pending",
                design_current_a=None,
                power_factor=None,
                breaker_a=None,
                conventional_current_a=None,
                phase_section_mm2=None,
                pe_section_mm2=None,
                capacity_a=None,
                temperature_factor=None,
                grouping_factor=None,
                voltage_drop_v=None,
                voltage_drop_percent=None,
                total_drop_percent=None,
                breaking_capacity_ok=None,
                pending_checks=[],
                protection_checks=[],
                reference=REFERENCE,
                reference_urls=SOURCES,
                limitations=LIMITATIONS,
            )
            pending = row["pending_checks"]
            current, pf, error = circuit_current(circuit, loads, results)
            if error:
                pending.append(error)
            row.update(design_current_a=current, power_factor=pf)
            duplicate = any(assignments[key] > 1 for key in circuit.get("load_ids", []))
            if duplicate:
                pending.append("Carga associada a mais de um circuito; corrija a distribuição.")
                row["status"] = "invalid"
            if not circuit.get("scope_confirmed"):
                pending.append("Confirme as condições físicas e o escopo do método.")
            method = circuit.get("method")
            temperature = circuit.get("ambient_temperature_c")
            group = circuit.get("grouped_circuits")
            if method not in CAPACITIES:
                pending.append("Método de instalação não conferido neste subconjunto.")
            if temperature not in TEMPERATURE:
                pending.append(
                    "Selecione temperatura ambiente conferida, entre10 e60°C em passos de5°C."
                )
            if group is None or group not in range(1, 9):
                pending.append("Informe1 a8circuitos homogêneos no agrupamento.")
            ratings = circuit.get("breaker_ratings_a") or []
            factor = circuit.get("breaker_i2_factor")
            if not ratings or factor is None or not circuit.get("breaker_source"):
                pending.append(
                    "Informe correntes nominais disponíveis, I2/In e fonte do dispositivo."
                )
            if current is None or pending:
                output.append(row)
                continue
            ratings = sorted({D(str(r)) for r in ratings})
            breaker = next((r for r in ratings if r >= current), None)
            if breaker is None:
                pending.append("Nenhum disjuntor informado comporta a corrente de projeto.")
                output.append(row)
                continue
            i2 = breaker * D(str(factor))
            tf = TEMPERATURE[temperature]
            gf = GROUPING[group - 1]
            row.update(
                breaker_a=breaker,
                conventional_current_a=i2,
                temperature_factor=tf,
                grouping_factor=gf,
            )
            minimum = D("1.5") if circuit["purpose"] == "lighting" else D("2.5")
            length = circuit.get("length_m")
            upstream = circuit.get("upstream_drop_percent")
            source = circuit.get("supply_origin")
            total_limit = (
                D(5)
                if source == "public_lv_delivery"
                else D(7)
                if source in {"own_transformer", "delivery_at_transformer", "generator"}
                else None
            )
            drop_ack = circuit.get("voltage_drop_model_confirmed")
            terminal_limit = D(4)
            if total_limit is not None and upstream is not None:
                terminal_limit = min(terminal_limit, total_limit - D(str(upstream)))
            chosen = None
            for section, base in zip(SECTIONS, CAPACITIES[method]):
                capacity = base * tf * gf
                i2_limit = (
                    D("1.45") if circuit.get("overload_duration_confirmed") else D(1)
                ) * capacity
                if section < minimum or capacity < breaker or i2 > i2_limit:
                    continue
                protection = circuit.get("protections") or {}
                thermal_ready = (
                    protection.get("source")
                    and protection.get("device_rated_a") is not None
                    and D(str(protection["device_rated_a"])) == breaker
                    and protection.get("cable_k") is not None
                    and protection.get("let_through_a2s") is not None
                    and protection.get("short_duration_s") is not None
                    and D(str(protection["short_duration_s"])) <= 5
                )
                if (
                    thermal_ready
                    and D(str(protection["let_through_a2s"]))
                    > (D(str(protection["cable_k"])) * section) ** 2
                ):
                    continue
                drop = (
                    voltage_drop(current, pf, D(str(length)), section)
                    if length is not None and drop_ack
                    else None
                )
                percent = drop / D(str(circuit["voltage_v"])) * 100 if drop is not None else None
                if percent is not None and percent > terminal_limit:
                    continue
                chosen = (section, capacity, drop, percent)
                break
            if chosen is None:
                pending.append(
                    "Nenhuma seção até95mm² atende aos critérios disponíveis; não extrapolar tabelas."
                )
            else:
                section, capacity, drop, percent = chosen
                row.update(
                    phase_section_mm2=section,
                    pe_section_mm2=section
                    if section <= 16
                    else D(16)
                    if section <= 35
                    else next(size for size in SECTIONS if size >= section / 2),
                    capacity_a=capacity,
                    voltage_drop_v=drop,
                    voltage_drop_percent=percent,
                    total_drop_percent=percent + D(str(upstream))
                    if percent is not None and upstream is not None
                    else None,
                )
                if drop is None:
                    pending.append(
                        "Queda pendente: informe comprimento e confirme o modelo de cálculo."
                    )
                if total_limit is None or upstream is None:
                    pending.append(
                        "Queda total pendente: informe origem do fornecimento e queda a montante."
                    )
            short = circuit.get("prospective_short_circuit_ka")
            breaking = circuit.get("breaking_capacity_ka")
            if short is None or breaking is None:
                pending.append(
                    "Capacidade de interrupção pendente: informe curto presumido e capacidade do disjuntor na tensão aplicada."
                )
            else:
                row["breaking_capacity_ok"] = D(str(breaking)) >= D(str(short))
                if not row["breaking_capacity_ok"]:
                    pending.append("Capacidade de interrupção inferior ao curto presumido.")
            row["protection_checks"] = protection_checks(
                circuit.get("protections"), row["phase_section_mm2"], row["breaker_a"]
            )
            pending.extend(
                [
                    "Verificar curto térmico/energia passante, tempos de desligamento, proteção contra choque, DR/DPS e seletividade com dados do circuito e produtos.",
                    "Compatibilizar percurso, pontos de utilização, ambientes e manuais antes de executar.",
                ]
            )
            row["status"] = "estimated" if chosen else "pending"
            output.append(row)
    return output
