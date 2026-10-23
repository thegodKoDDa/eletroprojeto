"""Residential quantity/load prevision, NBR 5410 §9.5 (2004/correction 2008).

Only explicitly selected residential studies. No placement, protection, lux,
conformity certification or utility demand. Each environment stays independent.
The optional wet-room reduction is deliberately not applied: the basic method
(three 600 VA points per room) remains applicable regardless of total count.
"""

from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, localcontext

from .standards import pending_rule

INDOOR = frozenset(
    ("living", "bedroom", "kitchen", "bathroom", "laundry", "garage", "corridor", "office")
)
WET = frozenset(("kitchen", "laundry", "bathroom"))


def lighting_minimum(area_m2: Decimal) -> Decimal:
    if not area_m2.is_finite() or area_m2 <= 0:
        raise ValueError("Área deve ser positiva e finita")
    with localcontext() as ctx:
        ctx.prec = 40
        blocks = (max(area_m2 - Decimal(6), Decimal(0)) / Decimal(4)).to_integral_value(
            rounding=ROUND_FLOOR
        )
        return Decimal(100) + Decimal(60) * blocks


def outlet_minimum(kind: str, area_m2: Decimal | None, perimeter_m: Decimal | None) -> int | None:
    for value in (area_m2, perimeter_m):
        if value is not None and (not value.is_finite() or value <= 0):
            raise ValueError("Geometria deve ser positiva e finita")
    if kind not in INDOOR:
        return None
    if kind == "bathroom":
        return 1
    divisor = Decimal("3.5") if kind in WET else Decimal(5)
    if kind not in ("living", "bedroom", "kitchen", "laundry"):
        if area_m2 is None:
            return None
        if area_m2 <= 6:
            return 1
    if perimeter_m is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 40
        return int((perimeter_m / divisor).to_integral_value(rounding=ROUND_CEILING))


def outlet_load(kind: str, points: int) -> Decimal:
    if kind not in INDOOR:
        raise ValueError("Tipo de ambiente fora do escopo residencial implementado")
    if points < 0:
        raise ValueError("Quantidade não pode ser negativa")
    high = min(points, 3) if kind in WET else 0
    return Decimal(600) * high + Decimal(100) * (points - high)


def residential_prevision(project: dict) -> tuple[dict, list[dict]]:
    results = {key: pending_rule(key) for key in ("lighting", "outlets")}
    if project.get("analysis_scope") != "normative":
        for item in results.values():
            item.update(
                status="pending",
                reason="Selecione Previsão residencial (luz/TUG) para aplicar os critérios a ambientes de habitação.",
            )
        return results, []
    rooms = []
    with localcontext() as ctx:
        ctx.prec = 40
        for room in project["environments"]:
            kind = room["type"]
            supported = kind in INDOOR
            area = Decimal(str(room["area_m2"])) if room.get("area_m2") is not None else None
            perimeter = (
                Decimal(str(room["perimeter_m"])) if room.get("perimeter_m") is not None else None
            )
            light = lighting_minimum(area) if supported and area is not None else None
            points = outlet_minimum(kind, area, perimeter) if supported else None
            basis = max(points, room["outlets"]) if points is not None else None
            missing = []
            if supported:
                if area is None:
                    missing.append("area_m2")
                if (
                    points is None
                    and (kind in ("living", "bedroom", "kitchen", "laundry") or area is not None)
                    and perimeter is None
                ):
                    missing.append("perimeter_m")
            notes = [
                "Somente quantidades e previsão em VA; distribuição, localização, proteção e circuitos exigem revisão do projeto."
            ]
            if kind in ("kitchen", "laundry"):
                notes.append(
                    "Acima da pia: pelo menos duas tomadas de corrente, que podem compartilhar um ponto. Não são dois pontos adicionais automáticos."
                )
            if kind == "bathroom":
                notes.append(
                    "Ponto próximo ao lavatório; posicionamento sujeito às restrições dos volumes do banheiro (§9.1)."
                )
            if kind not in ("living", "bedroom", "kitchen", "laundry", "bathroom") and supported:
                notes.append(
                    "Aplicado o critério dos demais cômodos internos de habitação; até 2,25 m² o ponto pode ficar fora, a até 0,80 m da porta."
                )
            if kind in WET:
                notes.append(
                    "Método básico: até três pontos de 600 VA por ambiente; excedentes de 100 VA. A redução opcional do conjunto não foi aplicada."
                )
            rooms.append(
                dict(
                    environment_id=room["id"],
                    name=room["name"],
                    status="out_of_scope"
                    if not supported
                    else "pending"
                    if missing
                    else "calculated",
                    lighting_va=light,
                    minimum_lighting_points=1 if supported else None,
                    registered_lighting_points=room["lighting_points"],
                    lighting_points_missing=max(1 - room["lighting_points"], 0)
                    if supported
                    else None,
                    minimum_outlet_points=points,
                    registered_outlet_points=room["outlets"],
                    outlet_points_missing=max(points - room["outlets"], 0)
                    if points is not None
                    else None,
                    outlet_basis_points=basis,
                    outlets_va=outlet_load(kind, basis) if basis is not None else None,
                    missing_fields=missing,
                    notes=notes,
                    reason="Área externa ou tipo não classificado: este procedimento não se aplica automaticamente."
                    if not supported
                    else "Previsão residencial; os valores cadastrados foram preservados.",
                )
            )
        for key, field in (("lighting", "lighting_va"), ("outlets", "outlets_va")):
            complete = bool(rooms) and all(room[field] is not None for room in rooms)
            results[key].update(
                value=sum((room[field] for room in rooms), Decimal(0)) if complete else None,
                status="calculated" if complete else "pending",
                reason="Previsão residencial em VA, separada das cargas em W; não atesta conformidade integral."
                if complete
                else "Total indisponível: confira os dados e o escopo de cada ambiente. Nenhum subtotal é apresentado como total.",
            )
    return results, rooms
