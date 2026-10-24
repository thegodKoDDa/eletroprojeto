"""Explicit-data checks, NBR5410 §§5.1.2.2.4.2/.3,5.1.3.2 and5.3.5.5.2.

No default fault current, cable k, product curve, earthing resistance or DR type.
"""

from decimal import Decimal as D

TN_TIMES = {D(127): (D(".8"), D(".35")), D(220): (D(".4"), D(".2"))}


def protection_checks(data, section, breaker):
    data = data or {}
    checks = []

    def check(code, label, value, passed, reason):
        checks.append(dict(code=code, label=label, value=value, passed=passed, reason=reason))

    source = bool(data.get("source"))
    same = (
        source
        and data.get("device_rated_a") is not None
        and D(str(data["device_rated_a"])) == breaker
    )
    k = data.get("cable_k")
    energy = data.get("let_through_a2s")
    duration = data.get("short_duration_s")
    thermal = (
        section is not None
        and same
        and k is not None
        and energy is not None
        and duration is not None
        and D(str(duration)) <= 5
    )
    maximum = (D(str(k)) * section) ** 2 if thermal else None
    check(
        "thermal_short",
        "Curto térmico da fase: I²t ≤ k²S²",
        maximum,
        D(str(energy)) <= maximum if thermal else None,
        "Dados do mesmo disjuntor na faixa de curto avaliada, k do cabo e duração≤5s; verificar também curto mínimo e curva completa.",
    )
    system = data.get("earthing_system")
    voltage = data.get("phase_earth_voltage_v")
    situation = data.get("tn_situation")
    loop = data.get("fault_loop_ohm")
    trip = data.get("trip_current_a")
    time = data.get("trip_time_s")
    if system == "TN":
        ready = (
            same
            and voltage is not None
            and D(str(voltage)) in TN_TIMES
            and situation in (1, 2)
            and loop is not None
            and trip is not None
            and time is not None
        )
        limit = TN_TIMES[D(str(voltage))][situation - 1] if ready else None
        value = D(str(loop)) * D(str(trip)) if ready else None
        check(
            "shock_tn",
            "TN: Zs×Ia≤U0 e tempo da tabela25",
            value,
            value <= D(str(voltage)) and D(str(time)) <= limit if ready else None,
            "Exige impedância de laço, tensão fase-terra, situação do anexoC e corrente/tempo assegurados pelo produto identificado. Não abrange TN-C ou exceção5s.",
        )
    elif system == "TT":
        ra = data.get("tt_ra_ohm")
        sensitivity = data.get("rcd_sensitivity_ma")
        ul = data.get("touch_limit_v")
        ready = (
            source
            and ra is not None
            and sensitivity is not None
            and ul is not None
            and data.get("rcd_type_compatible_confirmed") is True
        )
        value = D(str(ra)) * D(str(sensitivity)) / 1000 if ready else None
        check(
            "shock_tt",
            "TT: RA×IΔn≤UL",
            value,
            value <= D(str(ul)) if ready else None,
            "RA inclui eletrodo e PE;UL deve ser o menor aplicável às influências externas. DR obrigatório e tipo compatível, sem certificar ensaio/tempo.",
        )
    else:
        check(
            "shock",
            "Proteção contra choque",
            None,
            None,
            "Informe esquema TN ouTT e dados medidos/documentados. Outros esquemas não abrangidos.",
        )
    sensitivity = data.get("rcd_sensitivity_ma")
    required = data.get("rcd_additional_required")
    ready = (
        source
        and required is True
        and sensitivity is not None
        and data.get("rcd_type_compatible_confirmed") is True
    )
    check(
        "additional_rcd",
        "DR adicional de alta sensibilidade",
        D(str(sensitivity)) if ready else None,
        D(str(sensitivity)) <= 30 if ready else None,
        "Confirmar exigência de§5.1.3.2, tipologia, polos, corrente nominal, coordenação e instruções dos aparelhos. Não presumir dispensa de DR.",
    )
    return checks
