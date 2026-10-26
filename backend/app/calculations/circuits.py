"""Reviewed residential subset, never a blanket installation approval.

NBR5410:2004 tables36–40 (Cu/PVC70, XLPE/EPR90, A1/A2/B1/B2/C/D/E/F/G, 2 or 3 loaded conductors),
42 row1,47 and58; §§5.3.4.1/6.2.7. Prysmian LV Information2024 §5
voltage-drop estimate, non-magnetic conduit, sinusoidal single-phase or balanced three-phase loads without neutral.
"""

from collections import Counter
from decimal import Decimal, localcontext

from .protections import protection_checks

D = Decimal
SECTIONS = tuple(map(D, ("1.5", "2.5", "4", "6", "10", "16", "25", "35", "50", "70", "95")))
CAPACITIES = {
    "E": tuple(map(D, ("22", "30", "40", "51", "70", "94", "119", "148", "180", "232", "282"))),
    "A1": tuple(map(D, ("14.5", "19.5", "26", "34", "46", "61", "80", "99", "119", "151", "182"))),
    "A2": tuple(map(D, ("14", "18.5", "25", "32", "43", "57", "75", "92", "110", "139", "167"))),
    "C": tuple(map(D, ("19.5", "27", "36", "46", "63", "85", "112", "138", "168", "213", "258"))),
    "B1": tuple(map(D, ("17.5", "24", "32", "41", "57", "76", "101", "125", "151", "192", "232"))),
    "B2": tuple(map(D, ("16.5", "23", "30", "38", "52", "69", "90", "111", "133", "168", "201"))),
}
THREE_LOADED_CAPACITIES = {
    "E": tuple(map(D, ("18.5", "25", "34", "43", "60", "80", "101", "126", "153", "196", "238"))),
    "A1": tuple(map(D, ("13.5", "18", "24", "31", "42", "56", "73", "89", "108", "136", "164"))),
    "A2": tuple(map(D, ("13", "17.5", "23", "29", "39", "52", "68", "83", "99", "125", "150"))),
    "B1": tuple(map(D, ("15.5", "21", "28", "36", "50", "68", "89", "110", "134", "171", "207"))),
    "B2": tuple(map(D, ("15", "20", "27", "34", "46", "62", "80", "99", "118", "149", "179"))),
    "C": tuple(map(D, ("17.5", "24", "32", "41", "57", "76", "96", "119", "144", "184", "223"))),
}
THERMOSET_CAPACITIES = {
    "A1": tuple(map(D, ("19", "26", "35", "45", "61", "81", "106", "131", "158", "200", "241"))),
    "A2": tuple(map(D, ("18.5", "25", "33", "42", "57", "76", "99", "121", "145", "183", "220"))),
    "B1": tuple(map(D, ("23", "31", "42", "54", "75", "100", "133", "164", "198", "253", "306"))),
    "B2": tuple(map(D, ("22", "30", "40", "51", "69", "91", "119", "146", "175", "221", "265"))),
    # NBR table37: C/10mm²/2 loaded =80A; the local 2010 manual prints90A.
    "C": tuple(map(D, ("24", "33", "45", "58", "80", "107", "138", "171", "209", "269", "328"))),
    "E": tuple(map(D, ("26", "36", "49", "63", "86", "115", "149", "185", "225", "289", "352"))),
}
THERMOSET_THREE_LOADED_CAPACITIES = {
    "A1": tuple(map(D, ("17", "23", "31", "40", "54", "73", "95", "117", "141", "179", "216"))),
    "A2": tuple(map(D, ("16.5", "22", "30", "38", "51", "68", "89", "109", "130", "164", "197"))),
    "B1": tuple(map(D, ("20", "28", "37", "48", "66", "88", "117", "144", "175", "222", "269"))),
    "B2": tuple(map(D, ("19.5", "26", "35", "44", "60", "80", "105", "128", "154", "194", "233"))),
    "C": tuple(map(D, ("22", "30", "40", "52", "71", "96", "119", "147", "179", "229", "278"))),
    "E": tuple(map(D, ("23", "32", "42", "54", "75", "100", "127", "158", "192", "246", "298"))),
}
THERMOSET_TEMPERATURE = dict(
    zip(
        range(10, 61, 5),
        map(D, ("1.15", "1.12", "1.08", "1.04", "1", ".96", ".91", ".87", ".82", ".76", ".71")),
    )
)
# Tables36–39, distinct cable layouts; no interpolation or neutral assumption.
CAPACITIES["D"] = tuple(
    map(D, ("22", "29", "38", "47", "63", "81", "104", "125", "148", "183", "216"))
)
THREE_LOADED_CAPACITIES["D"] = tuple(
    map(D, ("18", "24", "31", "39", "52", "67", "86", "103", "122", "151", "179"))
)
THERMOSET_CAPACITIES["D"] = tuple(
    map(D, ("26", "34", "44", "56", "73", "95", "121", "146", "173", "213", "252"))
)
THERMOSET_THREE_LOADED_CAPACITIES["D"] = tuple(
    map(D, ("22", "29", "37", "46", "61", "79", "101", "122", "144", "178", "211"))
)
CAPACITIES["F"] = tuple(
    map(D, ("22", "31", "41", "53", "73", "99", "131", "162", "196", "251", "304"))
)
THREE_LOADED_CAPACITIES["F"] = tuple(
    map(D, ("17", "24", "33", "43", "60", "82", "110", "137", "167", "216", "264"))
)
THERMOSET_CAPACITIES["F"] = tuple(
    map(D, ("27", "37", "50", "65", "90", "121", "161", "200", "242", "310", "377"))
)
THERMOSET_THREE_LOADED_CAPACITIES["F"] = tuple(
    map(D, ("21", "29", "40", "53", "74", "101", "135", "169", "207", "268", "328"))
)
AIR_THREE_CAPACITIES = {
    "PVC70": {
        "flat_touching": tuple(
            map(D, ("18", "25", "34", "45", "63", "85", "114", "143", "174", "225", "275"))
        ),
        "horizontal_spaced": tuple(
            map(D, ("24", "34", "45", "59", "81", "110", "146", "181", "219", "281", "341"))
        ),
        "vertical_spaced": tuple(
            map(D, ("21", "29", "39", "51", "71", "97", "130", "162", "197", "254", "311"))
        ),
    },
    "90": {
        "flat_touching": tuple(
            map(D, ("22", "30", "42", "55", "77", "105", "141", "176", "216", "279", "342"))
        ),
        "horizontal_spaced": tuple(
            map(D, ("30", "41", "56", "73", "101", "137", "182", "226", "275", "353", "430"))
        ),
        "vertical_spaced": tuple(
            map(D, ("25", "35", "48", "63", "88", "120", "161", "201", "246", "318", "389"))
        ),
    },
}
SOIL_TEMPERATURE = {
    "PVC70": dict(
        zip(
            range(10, 61, 5),
            map(D, ("1.10", "1.05", "1", ".95", ".89", ".84", ".77", ".71", ".63", ".55", ".45")),
        )
    ),
    "90": dict(
        zip(
            range(10, 61, 5),
            map(D, ("1.07", "1.04", "1", ".96", ".93", ".89", ".85", ".80", ".76", ".71", ".65")),
        )
    ),
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
REFERENCE = "NBR5410:2004/VC2008: tabelas33/36–40/42(linha1)/47/58; §§5.3.4.1,6.2.5 e6.2.7. Manual Prysmian2010 pp.38/52–56, tabelas2–7. Prysmian Electrical Information2024 §5, p.34 (modelo PVC)."
SOURCES = [
    "https://www.abntcatalogo.com.br/",
    "https://www.ipaam.am.gov.br/wp-content/uploads/2021/01/NBR-05410-05-Instala%C3%A7%C3%B5es-El%C3%A9tricas-de-baixa-Tens%C3%A3o.pdf",
    "https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/18451/material/nbr_5410.pdf",
    "https://asean.prysmian.com/sites/asean.prysmian.com/files/media/documents/241218%20-%20Prysmian%20Electrical%20Information%20for%20Low%20Voltage%20Cables.pdf",
    "https://br.prysmian.com/sites/br.prysmian.com/files/media/documents/Manual_Instalacoes_Eletricas.pdf",
]
LIMITATIONS = [
    "Escopo: cobre/PVC70°C ou XLPE/EPR90°C com terminais compatíveis confirmados, A1/A2/B1/B2/C/D/E/F/G, com arranjos próprios, seções de1,5 a95mm²,2condutores monofásicos ou3trifásicos equilibrados sem neutro,50/60Hz, cargas senoidais indutivas/resistivas, sem FP capacitivo, cabos não armados até0,6/1kV, percurso não magnético, PE acompanha fases e agrupamento homogêneo em feixe (Tabela42 linha1); sem sol direto. Respeitar condições de dissipação da Tabela33/6.2.5. D somente cabo multipolar em eletroduto enterrado a0,7m, solo homogêneo com resistividade térmica2,5K·m/W e circuito único. F unipolares justapostos; G três unipolares espaçados, circuito único. F/G afastados de superfícies≥1diâmetro; E≥0,3diâmetro; G espaçamento entre cabos≥1diâmetro.",
    "Queda estimada em regime, concentrando cargas na extremidade; partida de motores, harmônicas, curto térmico, desligamento automático, DR/DPS, seletividade e geometria exigem verificações próprias.",
    "Resultados não autorizam execução nem certificam conformidade final.",
]


def study_conditions(circuit):
    def value(key):
        data = circuit.get(key)
        return str(data) if data is not None else "pendente"

    configuration = (
        "trifásica equilibrada sem neutro"
        if circuit.get("configuration") == "balanced_three_phase_without_neutral"
        else "monofásica"
    )
    layout = {
        "trefoil": "trifólio",
        "flat_touching": "plano justaposto",
        "horizontal_spaced": "espaçado horizontal",
        "vertical_spaced": "espaçado vertical",
    }.get(circuit.get("air_layout"), "não informado/não aplicável")
    conditions = [
        "Método="
        + circuit.get("method", "unknown")
        + "; cobre/"
        + circuit.get("insulation", "PVC70")
        + "; configuração="
        + configuration,
        "Arranjo="
        + layout
        + "; temperatura ambiente="
        + value("ambient_temperature_c")
        + "°C; solo="
        + value("soil_temperature_c")
        + "°C; circuitos agrupados="
        + value("grouped_circuits"),
        "Fonte de In e I2/In: " + (circuit.get("breaker_source") or "pendente"),
    ]
    if circuit.get("method") == "D":
        conditions.append(
            "Referência enterrada0,7m/solo2,5K·m/W/circuito único: "
            + (
                "declarada pelo usuário"
                if circuit.get("buried_reference_confirmed")
                else "pendente"
            )
        )
    if circuit.get("insulation", "PVC70") != "PVC70" or circuit.get("method") in {
        "D",
        "E",
        "F",
        "G",
    }:
        conditions.append(
            "Resistividade na temperatura de serviço="
            + value("hot_resistivity_ohm_mm2_m")
            + "Ω·mm²/m; reatância="
            + value("reactance_ohm_m")
            + "Ω/m; fonte="
            + (circuit.get("impedance_source") or "pendente")
        )
    return conditions


def circuit_current(circuit, loads, results):
    if not circuit.get("load_ids"):
        return None, None, "Associe ao menos uma carga ao circuito."
    voltage = circuit.get("voltage_v")
    if voltage is None:
        return None, None, "Informe a tensão do circuito."
    voltage = D(str(voltage))
    if voltage > 1000:
        return None, None, "Tensão acima de1000Vca fora deste escopo de baixa tensão."
    configuration = circuit.get("configuration", "single_phase")
    if configuration not in {"single_phase", "balanced_three_phase_without_neutral"}:
        return None, None, "Configuração de circuito fora do escopo implementado."
    expected = "single_phase" if configuration == "single_phase" else "balanced_three_phase"
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
        if params.get("configuration") != expected:
            return (
                None,
                None,
                "Confirme a mesma configuração em todas as cargas: monofásica ou trifásica equilibrada, conforme o circuito; cargas mistas ou desequilibradas exigem estudo próprio.",
            )
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
    divisor = voltage * (D(3).sqrt() if expected == "balanced_three_phase" else D(1))
    return apparent / divisor, active / apparent, None


def voltage_drop(
    current, pf, length, section, three_phase=False, rho=D(".0225"), reactance=D(".00008")
):
    """Prysmian2024 §5: rho=.0225Ωmm²/m, lambda=.00008Ω/m.

    Explicit model acknowledgement required by caller. No assumed FP.
    """
    return (
        (D(3).sqrt() if three_phase else D(2))
        * length
        * current
        * (rho / section * pf + reactance * (D(1) - pf * pf).sqrt())
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
                study_conditions=study_conditions(circuit),
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
            insulation = circuit.get("insulation", "PVC70")
            thermoset = insulation in {"XLPE90", "EPR90"}
            if insulation not in {"PVC70", "XLPE90", "EPR90"}:
                pending.append("Isolação fora do escopo conferido.")
            if thermoset and not circuit.get("terminals_90c_confirmed"):
                pending.append(
                    "Confirme compatibilidade térmica de terminais, conexões e equipamentos com o condutor a90°C (§6.2.5.1.1)."
                )
            three_phase = circuit.get("configuration") == "balanced_three_phase_without_neutral"
            layout = circuit.get("air_layout", "unknown")
            temperature = (
                circuit.get("soil_temperature_c")
                if method == "D"
                else circuit.get("ambient_temperature_c")
            )
            if method == "D" and not circuit.get("buried_reference_confirmed"):
                pending.append(
                    "Confirme cabo multipolar em eletroduto enterrado a0,7m, solo homogêneo2,5K·m/W, sem secagem e sem outros circuitos/condutos próximos. Fora dessas condições é necessário estudo térmico próprio."
                )
            if method == "F" and three_phase and layout not in {"trefoil", "flat_touching"}:
                pending.append(
                    "F trifásico exige arranjo explícito em trifólio ou plano justaposto."
                )
            if method == "G" and (
                not three_phase or layout not in {"horizontal_spaced", "vertical_spaced"}
            ):
                pending.append(
                    "G somente três fases equilibradas sem neutro, espaçadas na horizontal ou vertical; confirmar distância entre cabos e superfícies≥1diâmetro."
                )
            group = circuit.get("grouped_circuits")
            if method not in {*CAPACITIES, "G"}:
                pending.append("Método de instalação não conferido neste subconjunto.")
            if temperature not in TEMPERATURE:
                pending.append(
                    "Selecione temperatura conferida entre10 e60°C em passos de5°C (solo para D, ambiente para os demais)."
                )
            if method in {"D", "G"} and group != 1:
                pending.append(
                    "D/G somente circuito único neste modelo; fatores de feixe da Tabela42 não se aplicam a esses arranjos."
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
            temperature_table = (
                SOIL_TEMPERATURE["90" if thermoset else "PVC70"]
                if method == "D"
                else (THERMOSET_TEMPERATURE if thermoset else TEMPERATURE)
            )
            tf = temperature_table[temperature]
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
            rho, reactance = D(".0225"), D(".00008")
            if thermoset or method in {"D", "E", "F", "G"}:
                # Conduit/PVC70 impedance is not transferable to90°C or free air.
                drop_ack = (
                    drop_ack
                    and all(
                        circuit.get(key) is not None
                        for key in (
                            "hot_resistivity_ohm_mm2_m",
                            "reactance_ohm_m",
                            "impedance_source",
                        )
                    )
                    and bool(circuit.get("impedance_source"))
                )
                if drop_ack:
                    rho = D(str(circuit["hot_resistivity_ohm_mm2_m"]))
                    reactance = D(str(circuit["reactance_ohm_m"]))
            terminal_limit = D(4)
            if total_limit is not None and upstream is not None:
                terminal_limit = min(terminal_limit, total_limit - D(str(upstream)))
            chosen = None
            three_phase = circuit.get("configuration") == "balanced_three_phase_without_neutral"
            capacities = (
                (THERMOSET_THREE_LOADED_CAPACITIES if three_phase else THERMOSET_CAPACITIES)
                if thermoset
                else (THREE_LOADED_CAPACITIES if three_phase else CAPACITIES)
            )
            method_capacities = capacities.get(method)
            if three_phase and ((method == "F" and layout == "flat_touching") or method == "G"):
                method_capacities = AIR_THREE_CAPACITIES["90" if thermoset else "PVC70"][layout]
            for section, base in zip(SECTIONS, method_capacities):
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
                    voltage_drop(current, pf, D(str(length)), section, three_phase, rho, reactance)
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
                        "Queda pendente: informe comprimento e confirme o modelo de cálculo. XLPE/EPR ou método D/E/F/G exige resistividade na temperatura de serviço, reatância e fonte do cabo/percurso, sem reutilizar parâmetros do modelo PVC70 em conduto."
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
                circuit.get("protections"), row["phase_section_mm2"], row["breaker_a"], short
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
