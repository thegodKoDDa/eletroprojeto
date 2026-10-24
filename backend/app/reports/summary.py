"""One concise export contract for JSON and PDF, without electrical formulas."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from ..technical import UTILITIES

POWER_ORIGINS = {
    "nameplate": "Placa informada",
    "manufacturer": "Referência do fabricante",
    "user_estimate": "Estimativa do usuário",
}
ENERGY_BASES = {
    "stated": "Consumo mensal informado por unidade",
    "schedule": "Potência e horários informados",
    "pending": "Dados de consumo insuficientes",
}
POWER_RATINGS = {
    "nominal": "Potência nominal de referência",
    "maximum": "Potência máxima de referência; não é consumo típico",
    "estimated": "Estimativa genérica; confirmar o equipamento",
    "unknown": "Referência sem potência confirmada",
}


def build_summary(project: dict, result: dict, project_version: int | None = None) -> dict:
    """Map already-calculated results. No schedules, tariffs or factors are inferred."""

    def measurement(item, unit):
        return dict(
            valor=(item or {}).get("value"),
            unidade=(item or {}).get("unit") or unit,
            situacao=(item or {}).get("status", "pending"),
        )

    technical = {item["load_id"]: item for item in result.get("load_results", [])}
    powers = {item["load_id"]: item["result"]["value"] for item in result["memory"]}
    unknown_power = set(result.get("unknown_load_ids", []))
    rooms, equipment, pending = [], [], []
    for room in project["environments"]:
        unknown_energy, known_energy = 0, 0
        for load in room["loads"]:
            resolved = technical.get(load["id"], {})
            params = load.get("parameters") or {}
            energy = resolved.get("monthly_energy_kwh")
            basis = resolved.get("energy_basis", "pending")
            reference = load.get("catalog_reference") or {}
            adopted, suggested = load.get("unit_power_w"), reference.get("reference_power_w")
            custom_power = bool(load.get("power_user_edited")) or (
                adopted is not None
                and suggested is not None
                and Decimal(str(adopted)) != Decimal(str(suggested))
            )
            if energy is None:
                unknown_energy += 1
                needed = []
                if (
                    resolved.get("electrical_input_w") is None
                    or resolved.get("status") == "pending"
                ):
                    needed.append("potência elétrica")
                if params.get("usage_hours_per_day") is None:
                    needed.append("horas de uso por dia")
                if params.get("usage_days_per_month") is None:
                    needed.append("dias de uso por mês")
                pending.append(
                    dict(
                        ambiente=room["name"],
                        equipamento=load["name"],
                        necessario="Informe consumo mensal por unidade ou complete: "
                        + ", ".join(needed)
                        + ".",
                    )
                )
            else:
                known_energy += 1
            equipment.append(
                dict(
                    id=load["id"],
                    ambiente_id=room["id"],
                    ambiente=room["name"],
                    nome=load["name"],
                    categoria=load["category"],
                    quantidade=load["quantity"],
                    potencia_unitaria_w=resolved.get("electrical_input_w")
                    if resolved.get("status") != "pending"
                    else None,
                    potencia_total_w=powers.get(load["id"])
                    if resolved.get("status") != "pending"
                    else None,
                    origem_potencia=POWER_ORIGINS.get(
                        load.get("power_origin"), "Referência cadastrada"
                    ),
                    potencia_personalizada=custom_power,
                    dados_personalizados=bool(load.get("manual_override")),
                    classificacao_potencia="manual"
                    if custom_power
                    else reference.get("power_rating", "unknown"),
                    tipo_potencia="Potência adotada manualmente"
                    if custom_power
                    else POWER_RATINGS.get(reference.get("power_rating"), "Potência informada"),
                    tensao_v=load.get("voltage_v"),
                    fator_de_potencia_informado=load.get("power_factor"),
                    hipotese_resistiva_declarada=bool(params.get("assume_resistive")),
                    corrente_unitaria_a=resolved.get("unit_current_a"),
                    consumo_mensal_kwh=energy,
                    custo_mensal_brl=resolved.get("monthly_cost_brl"),
                    base_consumo=ENERGY_BASES[basis],
                    premissa_consumo="Consumo mensal informado; as condições da etiqueta ou medição podem diferir do uso real."
                    if basis == "stated"
                    else "Potência constante nas horas efetivas informadas; ciclos, standby e variação de potência não são presumidos."
                    if basis == "schedule"
                    else "Consumo ainda não estimado.",
                    consumo_unitario_informado_kwh=params.get("monthly_energy_kwh")
                    if basis == "stated"
                    else None,
                    horas_por_dia=params.get("usage_hours_per_day")
                    if basis == "schedule"
                    else None,
                    dias_por_mes=params.get("usage_days_per_month")
                    if basis == "schedule"
                    else None,
                    situacao_potencia=resolved.get("status", "pending"),
                )
            )
        rooms.append(
            dict(
                id=room["id"],
                nome=room["name"],
                area_m2=room.get("area_m2"),
                perimetro_m=room.get("perimeter_m"),
                pontos_de_luz=room.get("lighting_points"),
                tug=room.get("outlets"),
                potencia_conhecida_w=result["by_environment_w"].get(room["id"]),
                potencia_incompleta=any(load["id"] in unknown_power for load in room["loads"]),
                cargas_sem_potencia=sum(load["id"] in unknown_power for load in room["loads"]),
                consumo_mensal_kwh=result.get("energy_by_environment_kwh", {}).get(room["id"]),
                cargas_com_consumo=known_energy,
                cargas_sem_consumo=unknown_energy,
                consumo_incompleto=bool(unknown_energy),
            )
        )
    known = sum(room["cargas_com_consumo"] for room in rooms)
    unknown = sum(room["cargas_sem_consumo"] for room in rooms)
    available = result.get("monthly_energy") is not None
    coverage = "parcial" if available and unknown else "estimado" if available else "nao_estimado"
    utility = next(
        (item["name"] for item in UTILITIES if item["id"] == project["utility"]), "Não confirmada"
    )
    demand = result["normative"]["demand"]
    demand_available = demand.get("value") is not None and demand.get("status") in (
        "calculated",
        "estimated",
    )
    demand_reason = (
        "Demanda sujeita à revisão do projeto e aos requisitos locais."
        if demand_available
        else "Distribuidora ainda não confirmada."
        if project["utility"] == "unconfirmed"
        else "Localidade/distribuidora fora da cobertura validada neste estudo."
        if result.get("technical_context", {}).get("status") == "out_of_scope"
        else demand.get("reason")
        or "Procedimento de demanda desta distribuidora ainda indisponível neste estudo."
    )
    return dict(
        formato_versao="1.4",
        circuitos=result.get("circuit_results", []),
        entrada_de_energia=result.get("service_entry"),
        emissao=dict(
            data_hora=datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y, %H:%M:%S"),
            fuso="America/Sao_Paulo",
        ),
        projeto=dict(
            area_construida_m2=project.get("built_area_m2"),
            pavimentos=project.get("floors"),
            tipo_residencia=project.get("residence_type"),
            nome=project["name"],
            municipio=project["municipality"],
            uf=project["state"],
            observacoes=project.get("notes", ""),
            distribuidora=utility,
            distribuidora_id=project["utility"],
            revisao_salva=project_version,
        ),
        aviso="Estudo preliminar de cargas; não constitui dimensionamento final. Valores nulos não representam zero.",
        resultados=dict(
            consumo_mensal=measurement(result.get("monthly_energy"), "kWh"),
            custo_mensal_estimado=measurement(result.get("monthly_cost"), "BRL"),
            consumo_incompleto=bool(unknown),
            total_incompleto=bool(result.get("unknown_load_ids")),
            potencia_instalada=measurement(result["installed_power"], "W"),
            potencia_instalada_kw=measurement(result["installed_power_kw"], "kW"),
            iluminacao_nominal_incluida_no_total=measurement(result["lighting_nominal"], "W"),
            potencia_aparente_soma_escalar=measurement(result.get("apparent_power"), "VA"),
            potencia_aparente_kva=measurement(result.get("apparent_power_kva"), "kVA"),
        ),
        consumo=dict(
            situacao=coverage,
            cargas_cadastradas=known + unknown,
            unidades_cadastradas=sum(item["quantidade"] for item in equipment),
            cargas_com_estimativa=known,
            cargas_sem_estimativa=unknown,
            tarifa_brl_por_kwh=project.get("energy_tariff_brl_per_kwh"),
            alcance="Estimativa mensal para os equipamentos e hábitos de uso informados; não é medição da residência.",
            custo="Parcela estimada pela tarifa informada; não é fatura completa, não inclui encargos fixos ou tributos adicionais.",
        ),
        ambientes=rooms,
        equipamentos=equipment,
        pendencias_consumo=pending,
        previsao_residencial_por_ambiente=[
            dict(
                ambiente_id=r["environment_id"],
                nome=r["name"],
                situacao=r["status"],
                iluminacao_va=r["lighting_va"],
                minimo_pontos_de_luz=r["minimum_lighting_points"],
                minimo_pontos_tug=r["minimum_outlet_points"],
                pontos_tug_considerados=r["outlet_basis_points"],
                previsao_tug_va=r["outlets_va"],
                faltam_pontos_de_luz=r["lighting_points_missing"],
                faltam_pontos_tug=r["outlet_points_missing"],
                dados_faltantes=[
                    "área (m²)" if field == "area_m2" else "perímetro (m)"
                    for field in r["missing_fields"]
                ],
                observacoes=r["notes"],
                motivo=r["reason"],
            )
            for r in result.get("normative_environments", [])
        ],
        categorias=[
            dict(
                nome=name,
                potencia_conhecida_w=value,
                consumo_mensal_kwh=result.get("energy_by_category_kwh", {}).get(name),
            )
            for name, value in {
                **dict.fromkeys(result.get("energy_by_category_kwh", {})),
                **result["by_category_w"],
            }.items()
        ],
        previsoes_normativas={
            key: dict(
                valor=item.get("value"),
                unidade=item.get("unit"),
                situacao=item["status"],
                resultado_disponivel=item.get("value") is not None,
                motivo=demand_reason
                if key == "demand"
                else "Previsão residencial não solicitada neste estudo."
                if project.get("analysis_scope") != "normative"
                else "Confira dimensões e classificação dos ambientes."
                if item.get("value") is None
                else "Previsão quantitativa de ambientes residenciais.",
            )
            for key, item in result["normative"].items()
        },
        demanda_revisada=result.get("energisa_demand"),
        atendimento_distribuidora=dict(
            demanda_disponivel=demand_available,
            situacao="Demanda estimada disponível para revisão"
            if demand_available
            else "Demanda e padrão de entrada ainda exigem revisão",
            motivo=demand_reason,
            cobertura_territorial="Informe e confirme a distribuidora responsável pelo endereço."
            if project["utility"] == "unconfirmed"
            else "Distribuidora selecionada pelo usuário; atendimento ao município ainda não verificado automaticamente.",
            orientacao="kWh/mês expressa consumo. W/kW expressa potência instalada; kVA pode expressar demanda. Consumo mensal não define sozinho o tipo de ligação ou o padrão de entrada. Confirme a distribuidora e seus requisitos locais antes de solicitar ligação ou alteração de carga.",
        ),
    )
