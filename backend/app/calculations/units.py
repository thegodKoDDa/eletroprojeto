"""Dimension-specific conversions. Sources: NIST SP 1038/LLNL units.

Btu here is International Table; hp is mechanical (550 ft·lbf/s), cv metric.
These conversions do not infer consumption from energy or thermal capacity.
"""

from decimal import Decimal, localcontext

from .power import positive

BTU_IT_J = Decimal("1055.05585262")
CV_W = Decimal("735.49875")
HP_W = Decimal("745.69987158227022")
CONVERSION_SOURCE = "https://github.com/LLNL/units/blob/main/units/unit_definitions.hpp"


def btu_h_to_thermal_w(capacity: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return positive(capacity, "Capacidade térmica", zero=True) * BTU_IT_J / Decimal(3600)


def mechanical_to_w(power: Decimal, unit: str) -> Decimal:
    factors = {"cv": CV_W, "hp": HP_W}
    if unit not in factors:
        raise ValueError("Unidade mecânica deve ser cv ou hp mecânico")
    with localcontext() as ctx:
        ctx.prec = 40
        return positive(power, "Potência mecânica", zero=True) * factors[unit]


def motor_input_w(power: Decimal, unit: str, efficiency: Decimal) -> Decimal:
    positive(efficiency, "Rendimento")
    if efficiency > 1:
        raise ValueError("Rendimento deve ser menor ou igual a 1")
    with localcontext() as ctx:
        ctx.prec = 40
        return mechanical_to_w(power, unit) / efficiency


def va_to_kva(power: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return positive(power, "Potência aparente", zero=True) / Decimal(1000)


def wh_to_kwh(energy: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return positive(energy, "Energia", zero=True) / Decimal(1000)
