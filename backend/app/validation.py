"""Field dependencies for presentation and calculation diagnostics (no formulas)."""

from decimal import Decimal

# Required means necessary for the named operation, not a blanket ban on drafts.
REQUIREMENTS = {
    "project.name": ("Nome do projeto", "salvar projeto", None),
    "project.municipality": ("Município", "salvar projeto", None),
    "project.utility": ("Concessionária", "demanda da distribuidora", None),
    "project.state": ("Estado", "localização", None),
    "project.built_area_m2": ("Área construída (m²)", "salvar projeto", None),
    "project.residence_type": ("Tipo de residência", "salvar projeto", None),
    "project.floors": ("Pavimentos", "salvar projeto", None),
    "project.reference_voltage_v": ("Tensão de referência (V)", "salvar projeto", None),
    "environment.name": ("Nome", "identificar ambiente", None),
    "environment.type": ("Tipo", "previsão normativa", None),
    "environment.area_m2": ("Área (m²)", "previsão normativa de iluminação", None),
    "environment.perimeter_m": ("Perímetro (m)", "previsão normativa de tomadas", None),
    "environment.lighting_points": ("Pontos de luz", "conferir pontos cadastrados", None),
    "environment.outlets": ("Pontos de tomadas", "conferir pontos cadastrados", None),
    "load.name": ("Identificação da carga", "identificar carga", None),
    "load.category": ("Categoria", "agrupamento cadastral", None),
    "load.source": ("Fonte técnica", "rastreabilidade", None),
    "load.quantity": ("Quantidade", "potência instalada", None),
    "load.unit_power_w": (
        "Potência unitária (W)",
        "potência instalada",
        {"power_mode": "electrical"},
    ),
    "load.parameters.mechanical_power": (
        "Potência mecânica de saída",
        "entrada elétrica do motor",
        {"power_mode": "mechanical"},
    ),
    "load.parameters.efficiency": (
        "Rendimento do motor (0 a 1)",
        "entrada elétrica do motor",
        {"power_mode": "mechanical"},
    ),
    "load.voltage_v": ("Tensão nominal (V)", "corrente", None),
    "load.parameters.configuration": ("Configuração para corrente", "corrente", None),
    "load.power_factor": ("Fator de potência", "VA e corrente", {"assume_resistive": False}),
}


OPTIONAL_FIELDS = {
    "load.parameters.annual_energy_kwh": ("Consumo de energia (kWh/ano)", None, 0),
    "load.parameters.usage_minutes_per_day": ("Minutos de uso por dia", None, 0),
    "project.energy_tariff_brl_per_kwh": ("Tarifa de energia (R$/kWh)", None, 0),
    "load.parameters.usage_hours_per_day": ("Horas de uso por dia", None, 0),
    "load.parameters.usage_days_per_month": ("Dias de uso por mês", None, 0),
    "project.notes": ("Observações", 10000, None),
    "load.technology": ("Tecnologia / tipo", 100, None),
    "load.parameters.cooling_capacity_btu_h": ("Capacidade térmica (BTU/h)", None, 0.000001),
    "load.parameters.screen_inches": ("Tamanho da tela (polegadas)", None, 0.000001),
    "load.parameters.monthly_energy_kwh": ("Consumo de energia (kWh/mês)", None, 0),
    "load.parameters.maximum_power_w": ("Potência máxima informada (W)", None, 0),
    "load.parameters.microwave_output_w": ("Potência de saída para aquecimento (W)", None, 0),
    "load.parameters.nameplate_current_a": ("Corrente nominal da ficha/placa (A)", None, 0),
    "load.parameters.starting_current_a": ("Corrente de partida informada (A)", None, 0),
    "load.parameters.maximum_current_a": ("Corrente máxima da ficha (A)", None, 0),
}
for key, (label, _, _) in OPTIONAL_FIELDS.items():
    REQUIREMENTS[key] = (label, "consistência de parâmetro opcional", None)


def requirements():
    bounds = {
        "project.built_area_m2": (0.000001, None, False),
        "project.reference_voltage_v": (0.000001, None, False),
        "project.floors": (1, 100, True),
        "environment.area_m2": (0.000001, None, False),
        "environment.perimeter_m": (0.000001, None, False),
        "environment.lighting_points": (0, None, True),
        "environment.outlets": (0, None, True),
        "load.quantity": (1, 100000, True),
        "load.unit_power_w": (0.000001, None, False),
        "load.voltage_v": (0.000001, None, False),
        "load.power_factor": (0.000001, 1, False),
        "load.parameters.efficiency": (0.000001, 1, False),
        "load.parameters.mechanical_power": (0.000001, None, False),
    }
    # Geometry/utility are saved metadata until their normative operation is available.
    scopes = {
        "project.utility": [],
        "project.built_area_m2": [],
        "project.residence_type": [],
        "project.floors": [],
        "project.reference_voltage_v": [],
        "environment.type": [],
        "environment.area_m2": [],
        "environment.perimeter_m": [],
        "environment.lighting_points": [],
        "environment.outlets": [],
        "load.voltage_v": ["current"],
        "load.parameters.configuration": ["current"],
        "load.power_factor": ["apparent", "current"],
    }
    result = {}
    for key, (label, purpose, when) in REQUIREMENTS.items():
        minimum, maximum, integer = bounds.get(key, (None, None, False))
        max_length = (
            1000
            if key == "load.source"
            else 200
            if key
            in (
                "project.name",
                "project.municipality",
                "project.residence_type",
                "environment.name",
                "load.name",
                "load.category",
            )
            else None
        )
        result[key] = dict(
            label=label,
            purpose=purpose,
            when=when,
            minimum=minimum,
            maximum=maximum,
            integer=integer,
            max_length=max_length,
            required_for=scopes.get(key, ["installed", "apparent", "current", "normative"]),
        )
    for key, (_, maximum_length, minimum) in OPTIONAL_FIELDS.items():
        result[key].update(required_for=[], max_length=maximum_length, minimum=minimum)
    result["load.parameters.usage_hours_per_day"].update(maximum=24)
    result["load.parameters.usage_minutes_per_day"].update(maximum=1440)
    result["load.parameters.usage_days_per_month"].update(maximum=31, integer=True)
    return result


def field_issues(project):
    issues = []
    rules = requirements()
    operation = project.get("analysis_scope", "installed")
    location = ["Projeto"]

    def check(path, field, value, *, zero=False, unknown=False, required=False):
        label, purpose, _ = REQUIREMENTS[field]
        missing = (
            value is None
            or (isinstance(value, str) and not value.strip())
            or (unknown and value in ("unknown", "unconfirmed"))
        )
        invalid = False
        if isinstance(value, (int, float, Decimal)) or field.rsplit(".", 1)[-1] in (
            "unit_power_w",
            "mechanical_power",
        ):
            if not missing:
                try:
                    number = Decimal(str(value))
                    invalid = not number.is_finite() or number < 0 or (not zero and number == 0)
                except Exception:
                    invalid = True
        if missing and not required and operation not in rules[field]["required_for"]:
            return
        parts = path.split(".")
        target = (
            path
            if path.startswith("project.")
            else f"load.{parts[3]}." + ".".join(parts[4:])
            if ".loads." in path
            else f"room.{parts[1]}." + ".".join(parts[2:])
        )
        if missing or invalid:
            issues.append(
                dict(
                    path=path,
                    field=field,
                    label=label,
                    purpose=purpose,
                    status="pending" if missing else "invalid",
                    target_id=target,
                    location=list(location),
                    solution=f"Informe {label.lower()} válido no campo indicado.",
                    affected_results={
                        "load.unit_power_w": [
                            "Potência instalada",
                            "Potência aparente",
                            "Corrente",
                        ],
                        "load.parameters.mechanical_power": [
                            "Entrada elétrica",
                            "Potência instalada",
                            "Corrente",
                        ],
                        "load.parameters.efficiency": [
                            "Entrada elétrica",
                            "Potência instalada",
                            "Corrente",
                        ],
                        "load.power_factor": ["Potência aparente", "Corrente"],
                    }.get(field, [purpose]),
                    message=f"{label}: {'preenchimento necessário' if missing else 'informe um valor válido maior que zero'} para {purpose}.",
                )
            )

    check("project.utility", "project.utility", project.get("utility", "unconfirmed"), unknown=True)
    for key in ("name", "municipality"):
        check(f"project.{key}", f"project.{key}", project.get(key))
    for room in project["environments"]:
        location = [room.get("name") or "Ambiente sem nome"]
        prefix = f"environments.{room['id']}"
        from .calculations.residential import INDOOR

        residential = operation == "normative" and room.get("type", "other") in INDOOR
        for key in ("area_m2", "perimeter_m"):
            needs_perimeter = room.get("type", "other") in (
                "living",
                "bedroom",
                "kitchen",
                "laundry",
            ) or (
                room.get("type", "other") not in ("bathroom",)
                and room.get("area_m2") is not None
                and Decimal(str(room["area_m2"])) > 6
            )
            required = residential and (key == "area_m2" or needs_perimeter)
            check(f"{prefix}.{key}", f"environment.{key}", room.get(key), required=required)
        for load in room["loads"]:
            location = [
                room.get("name") or "Ambiente sem nome",
                load.get("name") or "Carga sem nome",
            ]
            base = f"{prefix}.loads.{load['id']}"
            params = load.get("parameters") or {}
            if params.get("power_mode", "electrical") == "mechanical":
                for key in ("mechanical_power", "efficiency"):
                    check(f"{base}.parameters.{key}", f"load.parameters.{key}", params.get(key))
            else:
                check(f"{base}.unit_power_w", "load.unit_power_w", load.get("unit_power_w"))
            if not params.get("assume_resistive"):
                check(f"{base}.power_factor", "load.power_factor", load.get("power_factor"))
            check(f"{base}.voltage_v", "load.voltage_v", load.get("voltage_v"))
            check(
                f"{base}.parameters.configuration",
                "load.parameters.configuration",
                params.get("configuration", "unknown"),
                unknown=True,
            )
    return issues


def notifications(project, result):
    notices = []
    for issue in result["field_issues"]:
        notices.append(
            dict(
                id=issue["path"],
                category="error",
                location=issue["location"],
                problem=issue["message"],
                solution=issue["solution"],
                affected_results=issue["affected_results"],
                target_id=issue["target_id"],
            )
        )
    for room in result.get("normative_environments", []):
        for field, deficit, label in (
            ("lighting_points", room["lighting_points_missing"], "ponto(s) de luz"),
            ("outlets", room["outlet_points_missing"], "ponto(s) de tomada"),
        ):
            if deficit:
                notices.append(
                    dict(
                        id=f"residential.{room['environment_id']}.{field}",
                        category="technical",
                        location=[room["name"]],
                        problem=f"Quantidade cadastrada abaixo da previsão residencial: faltam {deficit} {label}.",
                        solution="Revise os pontos previstos no ambiente e sua distribuição. O cadastro não foi alterado automaticamente.",
                        affected_results=["Previsão residencial de pontos"],
                        target_id=f"room.{room['environment_id']}.{field}",
                    )
                )
    for room in project["environments"]:
        for load in room["loads"]:
            location = [room.get("name") or room["id"], load["name"]]

            def add(suffix, category, problem, solution, affected, field=None):
                notices.append(
                    dict(
                        id=f"{load['id']}.{suffix}",
                        category=category,
                        location=location,
                        problem=problem,
                        solution=solution,
                        affected_results=affected,
                        target_id=f"load.{load['id']}.{field}" if field else None,
                    )
                )

            params = load.get("parameters") or {}
            if params.get("assume_resistive"):
                add(
                    "resistive",
                    "technical",
                    "FP=1 adotado por hipótese resistiva explícita.",
                    "Confirme se a hipótese descreve a carga; caso contrário, informe o FP documentado.",
                    ["Potência aparente", "Corrente"],
                    "power_factor",
                )
            ref = load.get("catalog_reference") or {}
            if (
                ref.get("voltage_v")
                and load.get("voltage_v")
                and Decimal(str(ref["voltage_v"])) != Decimal(str(load["voltage_v"]))
            ):
                add(
                    "voltage",
                    "technical",
                    f"Tensão informada ({load['voltage_v']} V) difere da referência ({ref['voltage_v']} V). A potência não foi alterada.",
                    "Confira a variante e a placa. Se a tensão real for outra, mantenha o valor confirmado e revise a referência.",
                    ["Compatibilidade do equipamento", "Corrente"],
                    "voltage_v",
                )
            if ref.get("voltage_range") and load.get("voltage_v"):
                import re

                bounds = re.fullmatch(r"(\d+)\s*[–-]\s*(\d+)\s*V", ref["voltage_range"])
                if bounds and not Decimal(bounds[1]) <= Decimal(str(load["voltage_v"])) <= Decimal(
                    bounds[2]
                ):
                    add(
                        "voltage_range",
                        "technical",
                        f"Tensão informada fora da faixa documentada ({ref['voltage_range']}).",
                        "Confira a placa e a alimentação; os resultados matemáticos não atestam compatibilidade do aparelho.",
                        ["Compatibilidade", "Corrente"],
                        "voltage_v",
                    )
            original_capacity = (ref.get("parameters") or {}).get("cooling_capacity_btu_h")
            if (
                original_capacity
                and params.get("cooling_capacity_btu_h")
                and Decimal(str(original_capacity))
                != Decimal(str(params["cooling_capacity_btu_h"]))
                and load.get("unit_power_w") is not None
            ):
                add(
                    "capacity",
                    "technical",
                    "Capacidade informada difere da referência utilizada para a potência elétrica; confirme se o valor em W continua aplicável.",
                    "Confirme a potência elétrica para a capacidade atual ou restaure uma sugestão documentada compatível.",
                    ["Origem da potência elétrica"],
                    "unit_power_w",
                )
    return notices


def input_error_notifications(errors, body):
    """Translate Pydantic locations into stable form targets, without trusting input."""
    output = []
    data = body if isinstance(body, dict) else {}
    if isinstance(data.get("project"), dict):
        data = data["project"]
    for error in errors:
        parts = list(error["loc"])
        parts = [part for part in parts if part not in ("body", "project")]
        location, target, key = ["Projeto"], None, None
        try:
            if parts[0] == "environments" and isinstance(parts[1], int):
                room = data["environments"][parts[1]]
                location = [str(room.get("name") or "Ambiente sem nome")]
                if len(parts) > 3 and parts[2] == "loads":
                    load = room["loads"][parts[3]]
                    location.append(str(load.get("name") or "Carga sem nome"))
                    suffix = ".".join(map(str, parts[4:]))
                    key, target = "load." + suffix, f"load.{load.get('id')}.{suffix}"
                else:
                    suffix = ".".join(map(str, parts[2:]))
                    key, target = "environment." + suffix, f"room.{room.get('id')}.{suffix}"
            elif parts:
                key, target = "project." + str(parts[0]), "project." + str(parts[0])
        except (KeyError, IndexError, TypeError, AttributeError):
            pass
        label = REQUIREMENTS.get(
            key,
            (
                f"Parâmetro {parts[-1]}" if parts else "Objeto do projeto",
                "validação das entradas",
                None,
            ),
        )[0]
        purpose = REQUIREMENTS.get(key, ("", "validação das entradas", None))[1]
        rule = requirements().get(key, {})
        limits = []
        if rule.get("minimum") is not None:
            limits.append(f"mínimo {rule['minimum']:g}")
        if rule.get("maximum") is not None:
            limits.append(f"máximo {rule['maximum']:g}")
        if rule.get("integer"):
            limits.append("número inteiro")
        if rule.get("max_length"):
            limits.append(f"até {rule['max_length']} caracteres")
        solution = (
            "Corrija o campo indicado"
            + (
                " (" + ", ".join(limits) + ")"
                if limits
                else ", respeitando a unidade e as opções disponíveis"
            )
            + ". Nenhum resultado antigo é considerado atual."
        )
        output.append(
            dict(
                id="invalid." + ".".join(map(str, parts)),
                category="error",
                location=location,
                problem=f"{label}: valor inválido para {purpose}.",
                solution=solution,
                affected_results=[purpose],
                target_id=target if key in REQUIREMENTS else None,
            )
        )
    return output
