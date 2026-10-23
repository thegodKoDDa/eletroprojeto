"""Adapt project snapshots to the already-reviewed NDU method, without inference."""

import hashlib
import json

from .energisa import calculate_energisa_demand


def project_energisa_demand(project: dict) -> dict | None:
    settings = project.get("energisa_demand") or {}
    if not settings.get("enabled"):
        return None
    inventory, loads, unclassified = [], [], []
    for room in project.get("environments", []):
        for load in room.get("loads", []):
            classification = load.get("energisa_demand") or {}
            group = classification.get("group")
            item = dict(
                load_id=str(load["id"]),
                environment_id=str(room["id"]),
                environment=room["name"],
                name=load["name"],
                group=group,
                quantity=load["quantity"],
                unit_power_w=load.get("unit_power_w"),
                reserve=classification.get("reserve", False),
                air_conditioning_type=classification.get("air_conditioning_type", "unconfirmed"),
            )
            # Mechanical output, BTU/h and VA are never silently treated as electrical W.
            if (load.get("parameters") or {}).get("power_mode") == "mechanical":
                item["unit_power_w"] = None
            inventory.append(item)
            if group is None:
                unclassified.append(str(load["id"]))
            loads.append({**item, "group": group or "__unclassified__"})
    unit_type = settings.get("unit_type", "unconfirmed")
    payload = dict(
        utility=project["utility"],
        state=project.get("state", "SP"),
        unit_type=unit_type,
        has_signage_or_display_lighting=settings.get("has_signage_or_display_lighting"),
        simultaneous_lighting_outlets=settings.get("simultaneous_lighting_outlets"),
        confirmed_absent_groups=settings.get("confirmed_absent_groups", []),
        inventory=inventory,
    )
    digest = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
        ).encode()
    ).hexdigest()
    reviewed = settings.get("reviewed_inventory_digest") == digest
    # An unknown group is non-executable but still contributes W to the scope check.
    # Missing declarations are pending; they are never a confirmation of scope.
    result = calculate_energisa_demand(
        {
            **payload,
            "loads": loads,
            "inventory_reviewed": reviewed,
            "unit_type": "individual_residential" if unit_type == "unconfirmed" else unit_type,
            "has_signage_or_display_lighting": settings.get("has_signage_or_display_lighting")
            is True,
        }
    )
    pending = []
    if not inventory:
        pending.append("Cadastre as cargas do inventário antes de revisar a demanda.")
    if unclassified:
        pending.append(
            "Classifique todas as cargas, inclusive reservas, nos grupos da NDU; nenhuma classificação é inferida pelo nome ou catálogo."
        )
    if unit_type == "unconfirmed":
        pending.append("Confirme o tipo de unidade consumidora.")
    if settings.get("has_signage_or_display_lighting") is None:
        pending.append("Confirme a presença ou ausência de letreiros/vitrines.")
    if pending:
        result.update(value=None, demanded_power_kw=None, groups=[])
        if result["status"] != "out_of_scope":
            result["status"] = "pending"
        result["pending_checks"] = pending + result["pending_checks"]
    result.update(
        declarations=settings,
        inventory_digest=digest,
        inventory_reviewed=reviewed,
        unclassified_load_ids=unclassified,
        inventory=inventory,
    )
    return result
