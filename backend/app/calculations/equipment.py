"""Resolve equipment input power and trace derived quantities without guessing."""

from decimal import Decimal

from .current import current_from_active
from .power import apparent_power
from .units import CONVERSION_SOURCE, btu_h_to_thermal_w, motor_input_w


def resolve_equipment(load: dict) -> dict:
    params = load.get("parameters") or {}
    power = Decimal(str(load["unit_power_w"])) if load.get("unit_power_w") is not None else None
    warnings, steps = [], []
    status = "estimated" if load.get("power_origin") == "user_estimate" else "calculated"

    def step(code, formula, substituted, number, unit, assumptions, source=None):
        steps.append(
            dict(
                calculation=code,
                formula=formula,
                substituted=substituted,
                value=number,
                unit=unit,
                assumptions=assumptions,
                source=source,
            )
        )

    if params.get("power_mode") == "mechanical":
        mechanical, efficiency = params.get("mechanical_power"), params.get("efficiency")
        power = None
        if mechanical is None or efficiency is None:
            warnings.append(
                "Potência mecânica e rendimento são necessários para obter a entrada elétrica."
            )
        else:
            unit = params.get("mechanical_unit", "cv")
            power = motor_input_w(Decimal(str(mechanical)), unit, Decimal(str(efficiency)))
            status = "estimated"
            step(
                "motor_input",
                "P_entrada = P_mecânica × conversão / rendimento",
                f"{mechanical} {unit} / η={efficiency} → {power} W",
                power,
                "W",
                "Rendimento informado; hp mecânico ou cv métrico. Não inclui corrente de partida.",
                CONVERSION_SOURCE,
            )
    thermal = None
    if params.get("cooling_capacity_btu_h") is not None:
        capacity = Decimal(str(params["cooling_capacity_btu_h"]))
        thermal = btu_h_to_thermal_w(capacity)
        step(
            "thermal_capacity",
            "Q_térmica = BTU_IT/h × 1055.05585262 / 3600",
            f"{capacity} BTU/h → {thermal} W térmicos",
            thermal,
            "W",
            "Capacidade térmica: não participa da potência elétrica instalada.",
            CONVERSION_SOURCE,
        )
    if power is None:
        status = "pending"
        warnings.append(
            "Potência elétrica de entrada desconhecida. Carga excluída do subtotal conhecido; total incompleto."
        )
    elif power == 0:
        status = "pending"
        warnings.append(
            "Potência zero informada; confirme o preenchimento antes de usar os totais."
        )
    pf = load.get("power_factor")
    if params.get("assume_resistive"):
        pf = "1"
        warnings.append(
            "Corrente/aparente usam hipótese explícita de carga resistiva (FP=1), declarada pelo usuário."
        )
    apparent = current = None
    if power is not None and power > 0 and pf is not None:
        apparent = apparent_power(power, Decimal(str(pf)))
        step(
            "apparent_power",
            "S = P / FP",
            f"{power} W / {pf} = {apparent} VA",
            apparent,
            "VA",
            "Por unidade; FP informado, sem fator de demanda.",
        )
        voltage, configuration = load.get("voltage_v"), params.get("configuration", "unknown")
        if voltage is not None and configuration != "unknown":
            current = current_from_active(
                power, Decimal(str(voltage)), Decimal(str(pf)), configuration
            )
            formula = (
                "I = P / (V × FP)"
                if configuration == "single_phase"
                else "I = P / (√3 × V_linha × FP)"
            )
            step(
                "current",
                formula,
                f"P={power} W; V={voltage} V; FP={pf}; I={current} A",
                current,
                "A",
                "Corrente por equipamento, em regime. Trifásico pressupõe equilíbrio; não dimensiona proteção ou condutor.",
            )
    if load.get("catalog_reference") and load.get("manual_override"):
        warnings.append(
            "Parâmetros substituídos manualmente; referência original preservada no projeto."
        )
    return dict(
        load_id=load["id"],
        name=load["name"],
        electrical_input_w=power,
        thermal_capacity_w=thermal,
        apparent_power_va=apparent,
        unit_current_a=current,
        status=status,
        steps=steps,
        warnings=warnings,
    )
