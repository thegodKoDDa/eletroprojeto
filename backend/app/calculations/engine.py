import hashlib
import json
from decimal import Decimal, localcontext

from ..version import APP_VERSION, ENGINE_VERSION
from .energy import energy_cost, resolve_energy
from .equipment import resolve_equipment
from .power import installed_power, watts_to_kw
from .residential import residential_prevision
from .standards import pending_rule
from .units import va_to_kva


def calculate(project: dict) -> dict:
    """Validated JSON inputs → pure, deterministic, traceable results.

    Installed and apparent values are known subtotals when coverage is incomplete.
    Each load is counted once; thermal/mechanical/energy values are never added.
    """
    from ..technical import applicability, normative_capabilities, registry_version
    from ..validation import field_issues

    context = applicability(project["utility"], project.get("state", "SP"))
    context["app_version"] = APP_VERSION
    context["registry_version"] = registry_version()
    calculation_inputs = {
        key: project.get(key)
        for key in (
            "analysis_scope",
            "state",
            "municipality",
            "utility",
            "environments",
            "energy_tariff_brl_per_kwh",
        )
    }
    digest = hashlib.sha256(
        json.dumps(
            calculation_inputs, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode()
    ).hexdigest()
    with localcontext() as ctx:
        ctx.prec = 40
        total = lighting = apparent = energy_total = Decimal(0)
        energy_unknown, energy_rooms, energy_categories = [], {}, {}
        energy_count = 0
        tariff = project.get("energy_tariff_brl_per_kwh")
        tariff = Decimal(str(tariff)) if tariff is not None else None
        all_pf = True
        estimated = lighting_estimated = lighting_pending = False
        by_room, by_category, memory, warnings, unknown, load_results = {}, {}, [], [], [], []
        room_terms, category_terms, lighting_terms, apparent_terms, aggregates = {}, {}, [], [], []
        for room in project["environments"]:
            subtotal = Decimal(0)
            room_terms[room["id"]] = []
            for load in room["loads"]:
                technical = resolve_equipment(load)
                energy = resolve_energy(load, technical["electrical_input_w"])
                technical.update(
                    {key: energy[key] for key in ("monthly_energy_kwh", "energy_basis")}
                )
                technical["monthly_cost_brl"] = None
                if energy["monthly_energy_kwh"] is None:
                    energy_unknown.append(load["id"])
                else:
                    amount = energy["monthly_energy_kwh"]
                    energy_count += 1
                    energy_total += amount
                    energy_rooms[room["id"]] = energy_rooms.get(room["id"], Decimal(0)) + amount
                    energy_categories[load["category"]] = (
                        energy_categories.get(load["category"], Decimal(0)) + amount
                    )
                    technical["steps"].append(energy["energy_step"])
                    if tariff is not None:
                        technical["monthly_cost_brl"] = energy_cost(amount, tariff)
                        technical["steps"].append(
                            dict(
                                calculation="monthly_cost",
                                formula="C_mês = E_mês × tarifa",
                                substituted=f"{amount} kWh × {tariff} BRL/kWh = {technical['monthly_cost_brl']} BRL",
                                value=technical["monthly_cost_brl"],
                                unit="BRL",
                                source=None,
                                assumptions="Parcela de energia pela tarifa informada; não representa fatura completa, tributos ou encargos fixos.",
                            )
                        )
                load_results.append(technical)
                warnings.extend(f"{load['name']}: {warning}" for warning in technical["warnings"])
                power = technical["electrical_input_w"]
                pending = technical["status"] == "pending"
                if pending:
                    unknown.append(load["id"])
                if technical["apparent_power_va"] is None or pending:
                    all_pf = False
                else:
                    apparent_item = installed_power(
                        load["quantity"], technical["apparent_power_va"]
                    )
                    apparent += apparent_item
                    apparent_terms.append(apparent_item)
                if load["kind"] == "lighting":
                    lighting_estimated |= technical["status"] == "estimated"
                    lighting_pending |= pending
                if power is None:
                    continue
                result = installed_power(load["quantity"], power)
                subtotal += result
                room_terms[room["id"]].append(result)
                category = load["category"]
                by_category[category] = by_category.get(category, Decimal(0)) + result
                category_terms.setdefault(category, []).append(result)
                if load["kind"] == "lighting":
                    lighting += result
                    lighting_terms.append(result)
                estimated |= technical["status"] == "estimated"
                memory.append(
                    {
                        "rule_id": "installed_power",
                        "rule_version": ENGINE_VERSION,
                        "power_origin": load.get("power_origin"),
                        "manual_override": load.get("manual_override", False),
                        "catalog_reference": load.get("catalog_reference"),
                        "calculation": "installed_power",
                        "load_id": load["id"],
                        "environment_id": room["id"],
                        "name": load["name"],
                        "inputs": {"quantity": load["quantity"], "unit_power_w": str(power)},
                        "formula": "quantity * unit_power_w",
                        "result": {"value": str(result), "unit": "W"},
                        "status": technical["status"],
                        "reference": None,
                        "source": load["source"],
                    }
                )
            by_room[room["id"]] = subtotal
            total += subtotal
        if not project["environments"]:
            warnings.append("Projeto sem ambientes; total representa apenas as cargas cadastradas.")
        if unknown:
            warnings.append(
                "Potência instalada incompleta: exibindo subtotal conhecido. Existem cargas sem potência confirmada."
            )
        status = "pending" if unknown else "estimated" if estimated else "calculated"

        def summation(
            label,
            terms,
            result,
            unit="W",
            assumptions="Soma das instâncias cadastradas, sem fatores de demanda.",
        ):
            aggregates.append(
                dict(
                    calculation=label,
                    formula="total = soma das parcelas conhecidas",
                    substituted=f"{' + '.join(map(str, terms)) or '0'} = {result} {unit}",
                    value=result,
                    unit=unit,
                    source=None,
                    assumptions=assumptions,
                )
            )

        for room in project["environments"]:
            summation(
                f"Ambiente: {room.get('name', room['id'])}",
                room_terms[room["id"]],
                by_room[room["id"]],
            )
        for category, terms in category_terms.items():
            summation(f"Categoria: {category}", terms, by_category[category])
        summation(
            "Potência instalada cadastrada",
            list(by_room.values()),
            total,
            assumptions="Subtotal conhecido; cargas pendentes impedem total completo."
            if unknown
            else "Soma dos ambientes; cada carga contada uma vez.",
        )
        summation(
            "Iluminação nominal cadastrada",
            lighting_terms,
            lighting,
            assumptions="Subconjunto já incluído na instalada; não é previsão normativa.",
        )
        aggregates.append(
            dict(
                calculation="Conversão W/kW",
                formula="P_kW = P_W / 1000",
                substituted=f"{total} W / 1000 = {watts_to_kw(total)} kW",
                value=watts_to_kw(total),
                unit="kW",
                source=None,
                assumptions="Conversão de unidade; mesma cobertura da potência instalada.",
            )
        )
        if all_pf:
            summation(
                "Potência aparente cadastrada",
                apparent_terms,
                apparent,
                "VA",
                "Soma escalar de quantidade × (P/FP); não é demanda nem análise vetorial.",
            )
            aggregates.append(
                dict(
                    calculation="Conversão VA/kVA",
                    formula="S_kVA = S_VA / 1000",
                    substituted=f"{apparent} VA / 1000 = {va_to_kva(apparent)} kVA",
                    value=va_to_kva(apparent),
                    unit="kVA",
                    source=None,
                    assumptions="Somente quando todas as cargas possuem potência e FP suficientes.",
                )
            )

        def value(number, unit, state=status):
            return {"value": number, "unit": unit, "status": state}

        residential, normative_rooms = residential_prevision(project)
        output = {
            "normative_environments": normative_rooms,
            "normative_capabilities": normative_capabilities(
                project["utility"], project.get("state", "SP")
            ),
            "field_issues": field_issues(project),
            "input_digest": digest,
            "engine_version": ENGINE_VERSION,
            "technical_context": context,
            "status": "awaiting_technical_validation",
            "installed_power": value(total, "W"),
            "installed_power_kw": value(watts_to_kw(total), "kW"),
            "lighting_nominal": value(
                lighting,
                "W",
                "pending"
                if lighting_pending
                else "estimated"
                if lighting_estimated
                else "calculated",
            ),
            "monthly_energy": value(
                energy_total, "kWh", "pending" if energy_unknown else "estimated"
            )
            if energy_count
            else None,
            "monthly_cost": value(
                energy_cost(energy_total, tariff),
                "BRL",
                "pending" if energy_unknown else "estimated",
            )
            if energy_count and tariff is not None
            else None,
            "energy_unknown_load_ids": energy_unknown,
            "energy_by_environment_kwh": energy_rooms,
            "energy_by_category_kwh": energy_categories,
            "by_environment_w": by_room,
            "by_category_w": by_category,
            "apparent_power": value(apparent, "VA") if all_pf else None,
            "apparent_power_kva": value(va_to_kva(apparent), "kVA") if all_pf else None,
            "normative": {
                **residential,
                "demand": pending_rule("demand")
                if project["utility"] == "energisa_sul_sudeste"
                and project.get("state", "SP") == "SP"
                else {
                    "value": None,
                    "unit": "kVA",
                    "status": context["status"],
                    "reference": context["documents"],
                    "reason": context["reason"],
                },
            },
            "memory": memory,
            "aggregate_steps": aggregates,
            "load_results": load_results,
            "unknown_load_ids": unknown,
            "warnings": warnings,
            "counting_policy": "Cada instância é somada uma vez. Iluminação é subconjunto da potência instalada. Previsão TUG/iluminação normativa e demanda são bases separadas. BTU/h, kWh/mês e saída do micro-ondas não são potências elétricas de entrada. Valores W com cargas pendentes são subtotais conhecidos; VA é soma escalar, não análise vetorial.",
        }

        from ..validation import notifications

        output["notifications"] = notifications(project, output)
        return output
