"""NDU001v7 table16/notes, ESS 220/127V, individual residence ≤75kW.

Table breaker values are BAND UPPER REFERENCES, never a selected protection.
Minimum entry sections do not waive voltage drop or installation checks.
"""

from decimal import Decimal, localcontext

D = Decimal
# category, upper band[kW or kVA], PVC phase/neutral, 90°C embedded/subterranean
BANDS = {
    1: [
        ("M1", "3.8", (6, 6), (6, 6), (6, 6), 6, 6, (30, 32)),
        ("M2", "6.3", (10, 10), (6, 6), (6, 6), 10, 10, (50,)),
        ("M3", "8.8", (16, 16), (10, 10), (10, 10), 16, 16, (70,)),
    ],
    2: [
        ("B1", "10.1", (10, 10), (10, 10), (10, 10), 10, 10, (50,)),
        ("B2", "12.7", (16, 16), (10, 10), (16, 16), 16, 16, (60, 63)),
        ("B3", "17.7", (25, 25), (16, 16), (25, 25), 16, 16, (80,)),
    ],
    3: [
        ("T1", "15.2", (10, 10), (6, 6), (10, 10), 10, 10, (40,)),
        ("T2", "19.0", (16, 16), (10, 10), (10, 10), 16, 16, (50,)),
        ("T3", "26.6", (25, 25), (16, 16), (25, 25), 16, 16, (70,)),
        ("T4", "38.1", None, (25, 25), (35, 25), 16, 16, (100,)),
        ("T5", "57.1", None, (50, 25), (70, 35), 25, 35, (150,)),
        ("T6", "81.5", None, (95, 50), (95, 50), 50, 50, (200,)),
    ],
}
REFERENCE = "Energisa NDU001v7.0,§6.6, pp.22–23, tabela16 p.73 e notas pp.74–75; exemplarSHA940b4aab66afc741e2f1f20d88ef2630672dcac2499928af31d807ac8d7442e2."


def service_entry(project, installed_w, unknown_ids, demand):
    settings = project.get("service_entry")
    if settings is None:
        return None
    row = dict(
        status="pending",
        category=None,
        phases=None,
        basis_value=None,
        basis_unit=None,
        minimum_phase_mm2=None,
        minimum_neutral_mm2=None,
        minimum_earthing_mm2=None,
        band_breaker_references_a=[],
        pending_checks=[],
        reference=REFERENCE,
    )
    pending = row["pending_checks"]
    if (
        project.get("utility") != "energisa_sul_sudeste"
        or project.get("state") != "SP"
        or settings.get("network") != "220_127"
    ):
        row["status"] = "out_of_scope"
        pending.append("Somente ESS/SP, rede220/127V, tabela16 conferida.")
        return row
    if not settings.get("scope_confirmed") or not settings.get("special_loads_reviewed"):
        pending.append(
            "Confirme unidade residencial individual, rede e avaliação das cargas especiais/limites de motores e solda de§6.6."
        )
    if unknown_ids or installed_w is None or installed_w <= 0:
        pending.append(
            "Carga instalada completa e positiva é necessária; subtotal não enquadra entrada."
        )
    if installed_w is not None and installed_w > 75000:
        row["status"] = "out_of_scope"
        pending.append("Carga acima de75kW fora deste método.")
    if settings.get("route") == "unknown" or settings.get("insulation") == "unknown":
        pending.append("Informe percurso embutido/subterrâneo e isolação.")
    if settings.get("route") == "underground" and settings.get("insulation") == "PVC70":
        pending.append(
            "NotaIX exige HEPR/XLPE/EPR0,6/1kV no ramal subterrâneo; PVC não habilitado."
        )
    if pending:
        return row
    with localcontext() as ctx:
        ctx.prec = 40
        power = installed_w / 1000
        if any(
            load.get("voltage_v") is not None and D(str(load["voltage_v"])) not in {D(127), D(220)}
            for room in project["environments"]
            for load in room["loads"]
        ):
            pending.append("Tensão cadastrada fora da rede127/220V conferida.")
            return row
        requires220 = any(
            load.get("voltage_v") is not None and D(str(load["voltage_v"])) > 127
            for room in project["environments"]
            for load in room["loads"]
        )
        if any(
            load.get("voltage_v") is None
            for room in project["environments"]
            for load in room["loads"]
        ):
            pending.append(
                "Confirme tensões de todas as cargas para verificar a modalidade de fornecimento."
            )
            return row
        phases = settings.get("requested_phases") or (
            1 if power <= D("8.8") and not requires220 else 2 if power <= D("17.7") else 3
        )
        row["phases"] = phases
        if phases == 1 and requires220:
            pending.append("Rede127V fase-neutro não alimenta a carga220V cadastrada.")
            return row
        if phases == 3:
            if demand is None or demand.get("value") is None or demand.get("pending_checks"):
                pending.append("Trifásico exige demanda NDU completa, atual e revisada em kVA.")
                return row
            basis = D(str(demand["value"]))
            unit = "kVA"
            if basis <= 0:
                pending.append("Demanda trifásica deve ser positiva.")
                return row
        else:
            basis = power
            unit = "kW"
        band = next((b for b in BANDS[phases] if basis <= D(b[1])), None)
        if band is None:
            pending.append("Carga/demanda acima da modalidade solicitada; consultar Energisa.")
            return row
        category, upper, pvc, embedded, underground, earth_e, earth_u, breakers = band
        section = (
            pvc
            if settings["insulation"] == "PVC70"
            else underground
            if settings["route"] == "underground"
            else embedded
        )
        if section is None:
            pending.append("PVC não aplicável à categoria nesta tabela.")
            return row
        row.update(
            status="estimated",
            category=category,
            basis_value=basis,
            basis_unit=unit,
            minimum_phase_mm2=D(section[0]),
            minimum_neutral_mm2=D(section[1]),
            minimum_earthing_mm2=D(earth_u if settings["route"] == "underground" else earth_e),
            band_breaker_references_a=[D(x) for x in breakers],
        )
        pending.extend(
            [
                "Seções são mínimos da tabela, não substituem queda de tensão, capacidade térmica e condições reais.",
                "Disjuntores listados correspondem ao limite superior da faixa (notaVII), não à proteção de projeto; calcular pela demanda e dados do produto.",
                "Localização, caixa, poste, eletroduto, aterramento, responsabilidade e aprovação dependem da distribuidora e do projeto físico.",
            ]
        )
        return row
