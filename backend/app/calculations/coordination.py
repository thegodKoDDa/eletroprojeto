"""Documented product/engineering requirements, no universal device selection.

Schneider EIG, Coordination between circuit-breakers: installation fault current
must be below the manufacturer's selectivity limit under identical conditions.
NBR5410 §§6.3.5.2.4–.9: SPD properties and installation must be coordinated.
Required SPD ratings are explicitly supplied by the engineering assessment;
this module does not perform a lightning risk assessment or assume a class.
"""

from decimal import Decimal as D

SELECTIVITY_SOURCE = (
    "https://www.electrical-installation.org/enwiki/Coordination_between_circuit-breakers"
)


def coordination_checks(data, breaker, prospective_short_circuit_ka=None):
    data = data or {}
    selectivity = data.get("selectivity") or {}
    ready = (
        all(selectivity.get(key) for key in ("upstream_device", "downstream_device", "source"))
        and selectivity.get("conditions_confirmed") is True
        and selectivity.get("downstream_rated_a") is not None
        and D(str(selectivity["downstream_rated_a"])) == breaker
        and selectivity.get("limit_ka") is not None
        and prospective_short_circuit_ka is not None
    )
    limit = D(str(selectivity["limit_ka"])) if ready else None
    checks = [
        dict(
            code="selectivity_short",
            label="Seletividade de curto: Ik máximo < limite tabelado (kA)",
            value=limit,
            passed=D(str(prospective_short_circuit_ka)) < limit if ready else None,
            reason="Comparação da faixa documentada pelo fabricante para o par exato, tensão, polos, ajustes, tolerâncias e fonte de alimentação confirmados. Igualdade não atesta seletividade. Não verifica sobrecarga, falta à terra, outras fontes ou filiação. Fonte: "
            + (selectivity.get("source") or SELECTIVITY_SOURCE)
            + (
                "; par="
                + str(selectivity.get("upstream_device"))
                + " → "
                + str(selectivity.get("downstream_device"))
                + "; In jusante="
                + str(selectivity.get("downstream_rated_a"))
                + "A; Ik máximo="
                + str(prospective_short_circuit_ka)
                + "kA"
                if ready
                else ""
            ),
        )
    ]
    surge = data.get("surge") or {}
    ready = (
        all(surge.get(key) for key in ("device", "source", "requirements_source"))
        and surge.get("conditions_confirmed") is True
    )
    reason = "Comparação documental com requisitos do estudo identificado, incluindo edição aplicável. Confirmar esquema/modos, TOV, proteção de retaguarda do par, conexões, comprimentos, seções e coordenação em cascata. Não determina necessidade/classe de DPS nem executa análise de risco NBR5419 ou inspeção. "
    if ready:
        reason += "Produto: " + surge["source"] + "; requisitos: " + surge["requirements_source"]
    for code, label, actual, required, maximum in [
        ("spd_uc", "DPS: Uc ≥ mínimo do estudo (V)", "uc_v", "required_uc_v", False),
        (
            "spd_up",
            "DPS: Up efetivo ≤ suportabilidade do equipamento (V)",
            "effective_up_v",
            "withstand_voltage_v",
            True,
        ),
        (
            "spd_discharge",
            "DPS: corrente de descarga/impulso ≥ requisito na mesma onda (kA)",
            "discharge_ka",
            "required_discharge_ka",
            False,
        ),
        (
            "spd_short",
            "DPS: suportabilidade do conjunto ≥ curto presumido (kA)",
            "short_withstand_ka",
            "prospective_short_circuit_ka",
            False,
        ),
    ]:
        requirement = prospective_short_circuit_ka if code == "spd_short" else surge.get(required)
        complete = ready and surge.get(actual) is not None and requirement is not None
        if code == "spd_discharge":
            complete = (
                complete
                and surge.get("waveform") is not None
                and surge.get("waveform") == surge.get("requirement_waveform")
            )
        value = D(str(surge[actual])) if complete else None
        required_value = D(str(requirement)) if complete else None
        passed = (
            (value <= required_value if maximum else value >= required_value) if complete else None
        )
        checks.append(
            dict(
                code=code,
                label=label,
                value=value,
                passed=passed,
                reason=reason + ("; requisito informado=" + str(requirement) if complete else ""),
            )
        )
    return checks
