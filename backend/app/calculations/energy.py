"""Energy arithmetic; no assumed schedules, cycling factors or tariffs.

A stated monthly energy per unit takes precedence over a constant-power schedule.
It never supplies electrical input power, apparent power or circuit current.
"""

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
        return validate_quantity(quantity) * positive(unit_energy_kwh, "Energia mensal", zero=True)


def resolve_energy(load: dict, power_w: Decimal | None) -> dict:
    params = load.get("parameters") or {}
    stated = params.get("monthly_energy_kwh")
    hours, days = params.get("usage_hours_per_day"), params.get("usage_days_per_month")
    quantity = load["quantity"]
    if stated is not None:
        unit = positive(Decimal(str(stated)), "Energia mensal", zero=True)
        total = total_energy_kwh(quantity, unit)
        return dict(
            monthly_energy_kwh=total,
            energy_basis="stated",
            energy_step=dict(
                calculation="monthly_energy",
                formula="E_mês = quantidade × energia mensal unitária",
                substituted=f"{quantity} × {unit} kWh = {total} kWh",
                value=total,
                unit="kWh",
                source=ENERGY_SOURCE,
                assumptions="Consumo mensal informado por unidade; prevalece sobre horários. Condições da etiqueta/medição podem diferir do uso real.",
            ),
        )
    if hours is None or days is None or power_w is None or power_w <= 0:
        return dict(monthly_energy_kwh=None, energy_basis="pending", energy_step=None)
    unit = monthly_energy(power_w, Decimal(str(hours)), days)
    total = total_energy_kwh(quantity, unit)
    return dict(
        monthly_energy_kwh=total,
        energy_basis="schedule",
        energy_step=dict(
            calculation="monthly_energy",
            formula="E_mês = quantidade × P_W × horas/dia × dias / 1000",
            substituted=f"{quantity} × {power_w} W × {hours} h/dia × {days} dias / 1000 = {total} kWh",
            value=total,
            unit="kWh",
            source=ENERGY_SOURCE,
            assumptions="Estimativa com potência constante durante as horas informadas. Não presume ciclos, standby ou simultaneidade.",
        ),
    )
