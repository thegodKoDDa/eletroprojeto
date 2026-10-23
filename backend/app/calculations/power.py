"""Pure arithmetic in W and VA. No normative coefficients are assumed."""

from decimal import Decimal, localcontext


def positive(value: Decimal, name: str, *, zero: bool = False) -> Decimal:
    if not value.is_finite() or (value < 0 if zero else value <= 0):
        raise ValueError(
            f"{name}: valor finito {'não negativo' if zero else 'positivo'} obrigatório"
        )
    return value


def validate_quantity(quantity: int) -> int:
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise ValueError("Quantidade deve ser um inteiro positivo")
    return quantity


def installed_power(quantity: int, unit_power_w: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return validate_quantity(quantity) * positive(unit_power_w, "Potência", zero=True)


def watts_to_kw(power_w: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 40
        return positive(power_w, "Potência", zero=True) / Decimal(1000)


def apparent_power(power_w: Decimal, power_factor: Decimal) -> Decimal:
    positive(power_w, "Potência", zero=True)
    positive(power_factor, "Fator de potência")
    if power_factor > 1:
        raise ValueError("Fator de potência deve ser menor ou igual a 1")
    with localcontext() as ctx:
        ctx.prec = 40
        return power_w / power_factor
