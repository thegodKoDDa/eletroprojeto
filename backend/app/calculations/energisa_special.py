"""NDU-0017.0 §9.1 notes I/VI/VII and tables12–14 (pp.56–57/68–70).

Table values are individual kVA, never W; table cos is used only for this
normative motor-demand procedure, not assigned to the load/nameplate.
"""

from decimal import Decimal as D

# cv label: (table cos, individual demand kVA for 1 / 2 / 3–5 / >5 motors).
MOTORS = {
    "single_phase": {
        "1/3": (".71", ".74", ".59", ".51", ".44"),
        "1/2": (".72", ".91", ".73", ".64", ".55"),
        "3/4": (".72", "1.24", ".99", ".87", ".74"),
        "1": (".74", "1.48", "1.19", "1.04", ".89"),
        "1.5": (".82", "1.92", "1.54", "1.35", "1.15"),
        "2": (".85", "2.44", "1.95", "1.71", "1.46"),
        "3": (".96", "3.19", "2.56", "2.24", "1.92"),
        "4": (".96", "4.14", "3.32", "2.90", "2.49"),
        "5": (".94", "5.22", "4.18", "3.65", "3.13"),
        "7.5": (".94", "7.94", "6.35", "5.55", "4.76"),
        "10": (".94", "10.04", "8.03", "7.03", "6.02"),
    },
    "three_phase": {
        "1/6": (".67", ".37", ".30", ".26", ".22"),
        "1/4": (".69", ".48", ".39", ".34", ".29"),
        "1/3": (".74", ".55", ".44", ".39", ".33"),
        "1/2": (".79", ".72", ".57", ".50", ".43"),
        "2/3": (".76", "1.08", ".87", ".76", ".65"),
        "1": (".82", "1.38", "1.10", ".97", ".83"),
        "1.5": (".78", "2.02", "1.62", "1.42", "1.21"),
        "2": (".81", "2.39", "1.91", "1.67", "1.43"),
        "3": (".80", "3.63", "2.91", "2.54", "2.18"),
        "4": (".77", "4.97", "3.97", "3.48", "2.98"),
        "5": (".85", "5.62", "4.50", "3.94", "3.37"),
        "6": (".84", "6.49", "5.19", "4.54", "3.89"),
        "7.5": (".85", "8.12", "6.49", "5.68", "4.87"),
        "10": (".90", "10.76", "8.61", "7.53", "6.46"),
        "12.5": (".98", "12.04", "9.63", "8.42", "7.22"),
        "15": (".91", "14.98", "11.98", "10.48", "8.99"),
        "20": (".89", "20.67", "16.54", "14.47", "12.40"),
        "25": (".91", "24.66", "19.73", "17.26", "14.79"),
        "30": (".91", "29.59", "23.67", "20.71", "17.75"),
    },
}


def positive(value):
    if value is None:
        return None
    value = D(str(value))
    return value if value.is_finite() and value > 0 else None


def component(item, table, va, pf, factor=None, quantity=None, *, source):
    quantity = item["quantity"] if quantity is None else quantity
    return dict(
        name=item["name"],
        quantity=quantity,
        table=table,
        unit_apparent_demand_va=va,
        power_factor=pf,
        factor=factor,
        demand_w=va * pf * quantity * (factor if factor is not None else D(1)),
        source=source,
    )


def motor_components(items):
    """Count all active d6 motors, select each exact row; never interpolate."""
    count = sum(item["quantity"] for item in items)
    column = 1 if count == 1 else 2 if count == 2 else 3 if count <= 5 else 4
    rows = []
    for item in items:
        motor = item.get("motor") or {}
        values = MOTORS.get(motor.get("configuration"), {}).get(motor.get("shaft_power_cv"))
        if values is None or not motor.get("source"):
            return (
                [],
                "d6: informe fases, potência de eixo em cv de uma linha exata das Tabelas12/13 e fonte. Fora das linhas, consulte a concessionária; não interpolar.",
            )
        table = "12" if motor["configuration"] == "single_phase" else "13"
        rows.append(
            component(item, table, D(values[column]) * 1000, D(values[0]), source=motor["source"])
        )
    return rows, None


def central_components(items):
    rows = []
    for item in items:
        central = item.get("central") or {}
        values = [
            positive(central.get(key))
            for key in ("voltage_v", "maximum_total_current_a", "power_factor")
        ]
        config = central.get("configuration")
        if (
            None in values
            or not central.get("source")
            or values[2] > 1
            or values[0] > 1000
            or config not in ("single_phase", "balanced_three_phase")
        ):
            return (
                [],
                "d5 central: informe corrente máxima total do fabricante, tensão, configuração mono/trifásica equilibrada, FP do mesmo regime e fonte; não usar corrente de partida ou MCA.",
            )
        voltage, current, pf = values
        va = voltage * current * (D(3).sqrt() if config == "balanced_three_phase" else D(1))
        rows.append(component(item, "§9.1 nota I (100%)", va, pf, D(1), source=central["source"]))
    return rows, None


def special_components(items):
    rows = []
    categories = {}
    for item in items:
        special = item.get("special") or {}
        category, connection = special.get("equipment_type"), special.get("connection")
        va, pf = (
            positive(special.get("input_apparent_power_va")),
            positive(special.get("power_factor")),
        )
        if (
            category not in {"arc_welder", "resistance_welder", "x_ray", "galvanization"}
            or va is None
            or pf is None
            or pf > 1
            or not special.get("source")
            or connection not in {"standard", "inverted_v_v", "not_applicable"}
        ):
            return (
                [],
                "d7: informe tipo, ligação, potência aparente elétrica absorvida em VA, FP do mesmo regime e fonte. Solda motor-gerador pertence a d6.",
            )
        welding = category in {"arc_welder", "resistance_welder"}
        if (welding and connection == "not_applicable") or (
            not welding and connection != "not_applicable"
        ):
            return (
                [],
                "d7: confirme ligação normal/V-V invertida para solda; raios-X/galvanização usam não aplicável.",
            )
        # §9.1 note VII doubles the equivalent input for inverted V-V welders.
        va *= 2 if connection == "inverted_v_v" else 1
        # Arc welding and galvanization share the same row in table14.
        key = "arc" if category in {"arc_welder", "galvanization"} else category
        categories.setdefault(key, []).append((va * pf, va, pf, item))
    for category, entries in categories.items():
        # §9.1 defines d7 in kW: rank the adjusted electrical active powers.
        entries.sort(key=lambda row: row[0], reverse=True)
        if any(entries[i][1] < entries[i + 1][1] for i in range(len(entries) - 1)):
            return (
                [],
                "d7: a ordem das potências W e VA diverge neste grupo. A Tabela14 não explicita esse caso; exige esclarecimento da concessionária.",
            )
        rank = 0
        factors = [D(1), D(".7"), D(".4")] if category == "arc" else [D(1)]
        rest = (
            D(".3")
            if category == "arc"
            else D(".6")
            if category == "resistance_welder"
            else D(".7")
        )
        for _, va, pf, item in entries:
            remaining = item["quantity"]
            while remaining:
                # Split only rank changes; avoid expanding 100000 equal units.
                quantity = 1 if rank < len(factors) else remaining
                factor = factors[rank] if rank < len(factors) else rest
                rows.append(
                    component(
                        item,
                        "14 / §9.1 nota VII",
                        va,
                        pf,
                        factor,
                        quantity,
                        source=item["special"]["source"],
                    )
                )
                remaining -= quantity
                rank += quantity
    return rows, None
