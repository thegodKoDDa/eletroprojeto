"""Read-only local ANEEL geometry reference, never an automatic utility assignment.

Original snapshots stay outside Git. No network or project/database mutation on
lookup; polygon topology/temporal currency and premise supply remain conditional.
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal as D
from decimal import localcontext
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "references" / "territory"
SOURCE = "https://sigel.aneel.gov.br/arcgis/rest/services/Hosted/AREA_ATUACAO/FeatureServer/5"
NOTICE = "Consulta pontual de referência ANEEL/SIGEL; não confirma município inteiro, atendimento do imóvel, sucessão empresarial ou vigência jurídica atual. Nenhuma distribuidora é selecionada automaticamente."


@lru_cache(maxsize=1)
def load_snapshot(folder, digest):
    raw = (folder / "geometry.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Hash da coleta territorial divergente.")
    data = json.loads(raw)
    if data.get("exceededTransferLimit") or data.get("spatialReference", {}).get("wkid") != 4674:
        raise ValueError("Coleta territorial incompleta/referencial não conferido.")
    indexed = []
    for feature in data["features"]:
        rings = feature["geometry"]["rings"]
        coords = [point for ring in rings for point in ring]
        bounds = (
            min(p[0] for p in coords),
            min(p[1] for p in coords),
            max(p[0] for p in coords),
            max(p[1] for p in coords),
        )
        indexed.append((feature["attributes"], rings, bounds))
    return indexed


def snapshot():
    if not ROOT.exists():
        return None
    for report in sorted(ROOT.glob("*/report.json"), reverse=True):
        try:
            data = json.loads(report.read_text())
            checks = data.get("checks", [])
            if not checks or not all(item["ok"] for item in checks):
                continue
            geometry = next(item for item in checks if item["name"] == "geometry")
            return data, load_snapshot(report.parent, geometry["sha256"])
        except (OSError, ValueError, KeyError, StopIteration):
            continue
    return None


def relation(longitude, latitude, rings):
    """Even–odd Esri rings; exact Decimal segment boundary, independent of winding."""
    with localcontext() as context:
        context.prec = 60
        inside = False
        for ring in rings:
            previous = ring[-1]
            x1, y1 = D(str(previous[0])), D(str(previous[1]))
            for point in ring:
                x2, y2 = D(str(point[0])), D(str(point[1]))
                cross = (longitude - x1) * (y2 - y1) - (latitude - y1) * (x2 - x1)
                if (
                    cross == 0
                    and min(x1, x2) <= longitude <= max(x1, x2)
                    and min(y1, y2) <= latitude <= max(y1, y2)
                ):
                    return "boundary"
                if (y1 > latitude) != (y2 > latitude):
                    intersection = x1 + (latitude - y1) * (x2 - x1) / (y2 - y1)
                    if longitude < intersection:
                        inside = not inside
                x1, y1 = x2, y2
        return "inside" if inside else "outside"


def lookup(latitude, longitude):
    result = dict(
        status="pending",
        source=SOURCE,
        consulted_on=None,
        snapshot_sha256=None,
        automatic_assignment=False,
        candidates=[],
        notice=NOTICE,
        reason="Sem coleta local completa e verificada; confirmação manual da distribuidora permanece necessária.",
    )
    selected = snapshot()
    if selected is None:
        return result
    data, features = selected
    result.update(
        consulted_on=data["consulted_on"],
        snapshot_sha256=next(c["sha256"] for c in data["checks"] if c["name"] == "geometry"),
        status="awaiting_technical_validation",
    )
    x, y = D(str(longitude)), D(str(latitude))
    now = datetime.now(timezone.utc).timestamp() * 1000
    for attrs, rings, bounds in features:
        if not bounds[0] <= float(x) <= bounds[2] or not bounds[1] <= float(y) <= bounds[3]:
            continue
        location = relation(x, y, rings)
        if location == "outside":
            continue
        start, end = attrs.get("ini_vigencia"), attrs.get("fim_vigencia")
        temporal = (
            "ended"
            if end is not None and end <= now
            else "not_started"
            if start is not None and start > now
            else "within_recorded_period"
            if end is not None
            else "no_end_recorded"
        )
        result["candidates"].append(
            dict(
                object_id=attrs["objectid"],
                name=attrs["razao_social"],
                acronym=attrs["sigla"],
                cnpj=attrs["cnpj"],
                state=attrs["uf"],
                legal_act=attrs["ato_legal"],
                relation=location,
                temporal_status=temporal,
                recorded_start=datetime.fromtimestamp(start / 1000, timezone.utc).date().isoformat()
                if start is not None
                else None,
                recorded_end=datetime.fromtimestamp(end / 1000, timezone.utc).date().isoformat()
                if end is not None
                else None,
            )
        )
    result["reason"] = (
        "Feições encontradas na coleta oficial; conferir registros encerrados, fronteiras, data da fonte e atendimento do imóvel com a distribuidora."
        if result["candidates"]
        else "Nenhuma feição encontrada nesta coleta para o ponto. Isso não comprova ausência de distribuidora ou de atendimento."
    )
    return result
