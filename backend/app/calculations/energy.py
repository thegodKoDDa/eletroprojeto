"""Energy arithmetic with explicit units, schedules and provenance; no assumed habits."""

from decimal import Decimal, localcontext

from .power import positive, validate_quantity

ENERGY_SOURCE = "https://www.eia.gov/energyexplained/electricity/measuring-electricity.php"


def monthly_energy(power_w: Decimal, hours_per_day: Decimal, days: int) -> Decimal:
    positive(power_w, "Potência", zero=True)
    positive(hours_per_day, "Horas por dia", zero=True)
    if hours_per_day > 24:
        raise ValueError("Horas por dia devem estar entre 0 e 24")
    if isinstance(days, bool) or not isinstance(days, int) or not 0 <= days <= 31:
        raise ValueError("Dias por mês devem ser inteiros entre 0 e 31")
    with localcontext() as ctx:
        ctx.prec = 40
        return power_w * hours_per_day * days / Decimal(1000)


def energy_cost(energy_kwh: Decimal, tariff_brl_per_kwh: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return positive(energy_kwh, "Energia", zero=True) * positive(
            tariff_brl_per_kwh, "Tarifa", zero=True
        )


def total_energy_kwh(quantity: int, unit_energy_kwh: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return validate_quantity(quantity) * positive(unit_energy_kwh, "Energia", zero=True)


def resolve_energy(load: dict, power_w: Decimal | None) -> dict:
    params = load.get("parameters") or {}
    stated, annual = params.get("monthly_energy_kwh"), params.get("annual_energy_kwh")
    minutes_mode = params.get("usage_time_unit") == "minutes"
    duration = params.get("usage_minutes_per_day" if minutes_mode else "usage_hours_per_day")
    days, quantity = params.get("usage_days_per_month"), load["quantity"]
    with localcontext() as ctx:
        ctx.prec = 40
        if stated is not None:
            total = total_energy_kwh(quantity, Decimal(str(stated)))
            yearly = total * 12
            basis = "stated"
            formula = "E_mês = quantidade × energia mensal unitária"
            substitution = f"{quantity} × {stated} kWh = {total} kWh"
            assumption = "Consumo mensal informado por unidade; prevalece sobre consumo anual e horários. Condições da etiqueta/medição podem diferir do uso real."
        elif annual is not None:
            yearly = total_energy_kwh(quantity, Decimal(str(annual)))
            total = yearly / 12
            basis = "annual_stated"
            formula = "E_mês médio = quantidade × energia anual unitária / 12"
            substitution = f"{quantity} × {annual} kWh/ano / 12 = {total} kWh/mês médio"
            assumption = "Média mensal do consumo anual informado; não prevê sazonalidade. Prevalece sobre horários, sem inferir potência elétrica."
        else:
            if duration is None or days is None or power_w is None or power_w <= 0:
                return dict(
                    monthly_energy_kwh=None,
                    annual_energy_kwh=None,
                    energy_basis="pending",
                    energy_step=None,
                )
            duration = positive(Decimal(str(duration)), "Tempo de uso", zero=True)
            if minutes_mode and duration > 1440:
                raise ValueError("Minutos por dia devem estar entre 0 e 1440")
            # Divide after multiplying the explicit inputs, avoiding rounded fractional hours.
            unit = monthly_energy(power_w, duration if not minutes_mode else Decimal(1), days)
            total = total_energy_kwh(quantity, unit)
            if minutes_mode:
                total = total * duration / 60
            yearly = total * 12
            basis = "schedule"
            formula = (
                "E_mês = quantidade × P_W × minutos/dia × dias / 60000"
                if minutes_mode
                else "E_mês = quantidade × P_W × horas/dia × dias / 1000"
            )
            substitution = f"{quantity} × {power_w} W × {duration} {'min/dia' if minutes_mode else 'h/dia'} × {days} dias / {60000 if minutes_mode else 1000} = {total} kWh"
            assumption = "Potência constante no tempo efetivo informado. Sem ciclos, standby ou simultaneidade presumidos. Projeção anual repete este uso por 12 meses, sem sazonalidade."
        return dict(
            monthly_energy_kwh=total,
            annual_energy_kwh=yearly,
            energy_basis=basis,
            energy_step=dict(
                calculation="monthly_energy",
                formula=formula,
                substituted=substitution,
                value=total,
                unit="kWh",
                source=ENERGY_SOURCE,
                assumptions=assumption,
            ),
        )


def energy_breakdown(
    load_results: list[dict], rooms: dict, categories: dict, tariff: Decimal | None
) -> dict:
    """Known subtotals only. Percentages of a zero total are undefined, never invented zero."""
    with localcontext() as ctx:
        ctx.prec = 40
        known = [item for item in load_results if item["monthly_energy_kwh"] is not None]
        total = sum((item["monthly_energy_kwh"] for item in known), Decimal(0))
        annual = sum((item["annual_energy_kwh"] for item in known), Decimal(0)) if known else None
        partial = len(known) != len(load_results)
        status = "pending" if partial else "estimated"

        def value(amount, unit):
            return dict(value=amount, unit=unit, status=status) if amount is not None else None

        return dict(
            annual_energy=value(annual, "kWh"),
            annual_cost=value(energy_cost(annual, tariff), "BRL")
            if annual is not None and tariff is not None
            else None,
            energy_cost_by_environment_brl={
                key: energy_cost(amount, tariff) for key, amount in rooms.items()
            }
            if tariff is not None
            else {},
            energy_cost_by_category_brl={
                key: energy_cost(amount, tariff) for key, amount in categories.items()
            }
            if tariff is not None
            else {},
            energy_share_by_load_pct={
                item["load_id"]: item["monthly_energy_kwh"] * 100 / total if total > 0 else None
                for item in known
            },
            energy_ranked_load_ids=[
                item["load_id"]
                for item in sorted(
                    known, key=lambda item: (-item["monthly_energy_kwh"], item["load_id"])
                )
            ],
            energy_known_load_count=len(known),
            energy_pending_load_count=len(load_results) - len(known),
        )
