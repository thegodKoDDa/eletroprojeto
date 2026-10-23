"""RMS current; balanced three-phase uses line-to-line voltage.

This mathematical utility is not conductor or protection sizing.
"""

from decimal import Decimal, localcontext

from .power import positive


def current_from_active(
    power_w: Decimal, voltage_v: Decimal, power_factor: Decimal, configuration: str
) -> Decimal:
    positive(voltage_v, "Tensão")
    positive(power_w, "Potência", zero=True)
    positive(power_factor, "Fator de potência")
    if power_factor > 1:
        raise ValueError("Fator de potência deve ser menor ou igual a 1")
    if configuration == "single_phase":
        with localcontext() as ctx:
            ctx.prec = 40
            return power_w / (voltage_v * power_factor)
    if configuration == "balanced_three_phase":
        with localcontext() as ctx:
            ctx.prec = 40
            return power_w / (Decimal(3).sqrt() * voltage_v * power_factor)
    raise ValueError("Configuração de fases não suportada")
