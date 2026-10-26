"""NDU-001 v7 §9.1: explicitly classified individual residential inventory.

Reviewed tables 5/6/7/8/10/12–14 and central AC note I.
Absent groups must be explicitly confirmed. No catalog inference,
BTU-to-input conversion, intermediate rounding or supply-category sizing.
"""

from decimal import Decimal, localcontext

from .energisa_special import central_components, motor_components, special_components

GROUPS = ("d1", "d2", "d3", "d4", "d5", "d6", "d7")
TABLES = {
    "d1": "5, notas I–IV",
    "d2": "6",
    "d3": "7",
    "d4": "8",
    "d5": "10 / §9.1 nota I",
    "d6": "12/13",
    "d7": "14",
}
WATER_FACTORS = (
    100,
    75,
    70,
    66,
    62,
    59,
    56,
    53,
    51,
    49,
    47,
    45,
    43,
    41,
    40,
    39,
    38,
    37,
    36,
    35,
    34,
    33,
    32,
    31,
)
COUNT_FACTORS = {
    "d3": ((1, 100), (4, 70), (6, 60), (9, 50), (None, 45)),
    "d4": (
        (1, 100),
        (2, 60),
        (3, 48),
        (4, 40),
        (5, 37),
        (6, 35),
        (7, 33),
        (8, 32),
        (9, 31),
        (11, 30),
        (15, 28),
        (20, 27),
        (25, 26),
        (None, 25),
    ),
    "d5": (
        (1, 100),
        (2, 88),
        (3, 82),
        (4, 78),
        (5, 76),
        (6, 74),
        (7, 72),
        (8, 71),
        (11, 70),
        (14, 68),
        (16, 67),
        (22, 66),
        (30, 65),
        (50, 64),
        (None, 62),
    ),
}


def count_factor(group: str, count: int) -> Decimal:
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("Quantidade deve ser inteira e positiva")
    if group == "d2":
        percentage = WATER_FACTORS[count - 1] if count <= 24 else 30
    elif group in COUNT_FACTORS:
        percentage = next(
            value for upper, value in COUNT_FACTORS[group] if upper is None or count <= upper
        )
    else:
        raise ValueError("Grupo sem fator por quantidade implementado")
    return Decimal(percentage) / Decimal(100)


def lighting_outlets_bands(power_w: Decimal, simultaneous: bool) -> list[dict]:
    if not power_w.is_finite() or not Decimal(0) <= power_w <= Decimal(75000):
        raise ValueError("Carga da Tabela 5 fora de 0–75000 W")
    if not isinstance(simultaneous, bool):
        raise ValueError("Simultaneidade deve ser explicitamente confirmada")
    with localcontext() as context:
        context.prec = 40
        if simultaneous:
            return [dict(installed_band_w=power_w, factor=Decimal(1), demand_w=power_w)]
        # Note III: each 1 kW band up to 10 kW is accumulated, not a single
        # multiplier applied to the full installed load.
        remaining, bands = power_w, []
        for percentage in (86, 75, 66, 59, 52, 45, 40, 35, 31, 27):
            band = min(remaining, Decimal(1000))
            if band > 0:
                factor = Decimal(percentage) / Decimal(100)
                bands.append(dict(installed_band_w=band, factor=factor, demand_w=band * factor))
            remaining -= band
        if remaining > 0:
            bands.append(
                dict(
                    installed_band_w=remaining,
                    factor=Decimal(".24"),
                    demand_w=remaining * Decimal(".24"),
                )
            )
        return bands


def lighting_outlets_demand_w(power_w: Decimal, simultaneous: bool) -> Decimal:
    with localcontext() as context:
        context.prec = 40
        return sum(
            (band["demand_w"] for band in lighting_outlets_bands(power_w, simultaneous)), Decimal(0)
        )


def calculate_energisa_demand(data: dict) -> dict:
    with localcontext() as context:
        context.prec = 40
        loads = data.get("loads", [])
        active = [item for item in loads if not item.get("reserve", False)]
        absent = set(data.get("confirmed_absent_groups", []))
        pending, groups = [], []
        installed = Decimal(0)
        installed_known = True
        for item in loads:
            power = item.get("unit_power_w")
            if power is None or Decimal(str(power)) <= 0:
                installed_known = False
            else:
                installed += Decimal(str(power)) * item["quantity"]
        out_of_scope = (
            data["utility"] != "energisa_sul_sudeste"
            or data["state"] != "SP"
            or data["unit_type"] != "individual_residential"
            or data.get("has_signage_or_display_lighting") is not False
            or installed > 75000  # a known subtotal above the limit already excludes the scope
        )
        if out_of_scope:
            pending.append(
                "Escopo implementado: residência individual sem letreiros/vitrines, Energisa Sul-Sudeste/SP, até75kW, grupos d1–d7 com dados próprios e fontes; exclui carga industrial."
            )
            return dict(
                value=None,
                unit="kVA",
                status="out_of_scope",
                installed_power_w=installed if installed_known else None,
                demanded_power_kw=None,
                groups=[],
                pending_checks=pending,
                ignored_reserve_loads=[
                    item["name"] for item in loads if item.get("reserve", False)
                ],
                limitations=["Nenhum fator Energisa foi aplicado fora do escopo implementado."],
            )
        if not data.get("inventory_reviewed"):
            pending.append(
                "Confirme inventário completo, classificação e aparelhos de reserva antes de usar o método."
            )
        if not installed_known:
            pending.append(
                "Há potência desconhecida ou zero; não foi possível conferir a carga instalada e o limite de 75 kW, inclusive das reservas."
            )
        for group in GROUPS:
            selected = [item for item in active if item["group"] == group]
            count = sum(item["quantity"] for item in selected)
            known = all(item.get("unit_power_w") is not None for item in selected)
            base = (
                sum(
                    (Decimal(str(item["unit_power_w"])) * item["quantity"] for item in selected),
                    Decimal(0),
                )
                if known
                else None
            )
            factor, demand, reason, bands = None, None, None, []
            components = []
            if not selected:
                if group in absent:
                    base, demand = Decimal(0), Decimal(0)
                else:
                    base = None
                    reason = f"{group}: ausência de cargas não confirmada."
            elif group in absent:
                reason = f"{group}: inventário contradiz a declaração de ausência."
            elif not known or any(Decimal(str(item["unit_power_w"])) <= 0 for item in selected):
                reason = f"{group}: informe potência elétrica positiva para todas as cargas; ausência não é zero."
            elif group in ("d6", "d7"):
                components, reason = (motor_components if group == "d6" else special_components)(
                    selected
                )
                if reason is None:
                    demand = sum((row["demand_w"] for row in components), Decimal(0))
            elif group == "d1":
                simultaneous = data.get("simultaneous_lighting_outlets")
                if simultaneous is None:
                    reason = "d1: confirme se a iluminação/TUG será usada simultaneamente (Tabela 5, nota I)."
                elif base > 75000:
                    reason = "d1: carga fora do limite da Tabela 5."
                else:
                    bands = lighting_outlets_bands(base, simultaneous)
                    demand = sum((band["demand_w"] for band in bands), Decimal(0))
            elif group == "d5":
                if any(
                    item.get("air_conditioning_type")
                    not in ("window_or_individual", "central_unit")
                    for item in selected
                ):
                    reason = "d5: confirme janela/individual ou unidade central para cada carga."
                else:
                    individual = [
                        item
                        for item in selected
                        if item.get("air_conditioning_type") == "window_or_individual"
                    ]
                    central = [
                        item
                        for item in selected
                        if item.get("air_conditioning_type") == "central_unit"
                    ]
                    components, reason = central_components(central)
                    if reason is None:
                        individual_count = sum(item["quantity"] for item in individual)
                        individual_base = sum(
                            (
                                Decimal(str(item["unit_power_w"])) * item["quantity"]
                                for item in individual
                            ),
                            Decimal(0),
                        )
                        individual_factor = (
                            count_factor("d5", individual_count) if individual_count else None
                        )
                        demand = sum((row["demand_w"] for row in components), Decimal(0))
                        if individual_factor is not None:
                            demand += individual_base * individual_factor
                            bands = [
                                dict(
                                    installed_band_w=individual_base,
                                    factor=individual_factor,
                                    demand_w=individual_base * individual_factor,
                                )
                            ]
                        factor = (
                            individual_factor
                            if not central
                            else Decimal(1)
                            if not individual
                            else None
                        )
            else:
                factor = count_factor(group, count)
                demand = base * factor
            if reason:
                pending.append(reason)
            groups.append(
                dict(
                    group=group,
                    quantity=count,
                    installed_power_w=base,
                    factor=factor,
                    demand_w=demand,
                    table=TABLES[group],
                    reason=reason,
                    bands=bands,
                    components=components,
                )
            )
        complete = not pending
        demanded_kw = (
            sum((item["demand_w"] for item in groups), Decimal(0)) / Decimal(1000)
            if complete
            else None
        )
        return dict(
            value=demanded_kw / Decimal("0.92") if demanded_kw is not None else None,
            unit="kVA",
            status="out_of_scope" if out_of_scope else "estimated" if complete else "pending",
            installed_power_w=installed if installed_known else None,
            demanded_power_kw=demanded_kw,
            groups=groups,
            pending_checks=pending,
            ignored_reserve_loads=[item["name"] for item in loads if item.get("reserve", False)],
            limitations=[
                "Escopo residencial d1–d7; motores somente nas linhas exatas das Tabelas12/13. Partida/instalação não verificadas pela demanda.",
                "Classificação e potências declaradas; não converte VA de previsão residencial, BTU/h ou kWh em W.",
                "Não determina categoria de fornecimento, cabos, disjuntor, aprovação ou dimensionamento final.",
                "Distribuidora/UF declaradas; não valida município, endereço ou cobertura territorial.",
            ],
        )
