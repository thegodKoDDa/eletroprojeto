"""Read-only official ANEEL probe; preserve evidence locally, never infer a map.

Run with backend/.venv/bin/python scripts/territory.py. Attribute metadata is
insufficient: an ArcGIS HTTP200 error is a failure, not a validated territory.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PORTAL = (
    "https://sigel.aneel.gov.br/portal/sharing/rest/content/items/70c2bd1464c04484add79a7a6691ec53"
)
SERVICE = "https://sigel.aneel.gov.br/arcgis/rest/services/Hosted/AREA_ATUACAO/FeatureServer/5"


def checked_json(response):
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or data.get("error"):
        raise ValueError(
            "Resposta ArcGIS inválida ou com erro: "
            + str(data.get("error") if isinstance(data, dict) else "objeto ausente")
        )
    return data


def validate_features(data, count, *, geometry):
    features = data.get("features")
    if (
        data.get("exceededTransferLimit")
        or not isinstance(features, list)
        or len(features) != count
        or count < 1
    ):
        raise ValueError("Coleta incompleta; contagem/paginação não conferida.")
    identifiers = set()
    for feature in features:
        attrs = feature.get("attributes") or {}
        oid = attrs.get("objectid")
        if (
            oid is None
            or oid in identifiers
            or not all(attrs.get(key) for key in ("cnpj", "sigla", "uf", "ato_legal"))
        ):
            raise ValueError("Identidade/proveniência da feição incompleta ou duplicada.")
        identifiers.add(oid)
        if geometry:
            rings = (feature.get("geometry") or {}).get("rings")
            if not rings or any(len(ring) < 4 or ring[0] != ring[-1] for ring in rings):
                raise ValueError("Polígono ausente/aberto; não habilitar associação territorial.")
    if geometry and data.get("spatialReference", {}).get("wkid") != 4674:
        raise ValueError("Referencial SIRGAS2000 não confirmado.")
    return identifiers


def probe():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "references" / "territory" / stamp
    folder.mkdir(parents=True, mode=0o700)
    os.chmod(folder.parent, 0o700)
    report = dict(
        consulted_on=datetime.now(timezone.utc).isoformat(),
        service=SERVICE,
        portal_item=PORTAL,
        territorial_mapping="pending",
        automatic_assignment=False,
        checks=[],
        limitations=[
            "Metadados/atributos não comprovam polígonos, atualidade, associação municipal ou atendimento de um imóvel."
        ],
    )
    with httpx.Client(timeout=20, follow_redirects=False) as client:
        count = None
        for name, url, params in [
            ("portal", PORTAL, {"f": "json"}),
            ("layer", SERVICE, {"f": "json"}),
            ("count", SERVICE + "/query", {"f": "json", "where": "1=1", "returnCountOnly": "true"}),
            (
                "attributes",
                SERVICE + "/query",
                {"f": "json", "where": "1=1", "outFields": "*", "returnGeometry": "false"},
            ),
            (
                "geometry",
                SERVICE + "/query",
                {"f": "json", "where": "1=1", "outFields": "*", "returnGeometry": "true"},
            ),
        ]:
            try:
                response = client.get(url, params=params)
                raw = response.content
                path = folder / (name + ".json")
                path.write_bytes(raw)
                path.chmod(0o600)
                data = checked_json(response)
                if name == "count":
                    count = data.get("count")
                    if not isinstance(count, int) or count < 1:
                        raise ValueError("Contagem ausente.")
                if name in {"attributes", "geometry"}:
                    validate_features(data, count, geometry=name == "geometry")
                report["checks"].append(
                    dict(name=name, ok=True, sha256=hashlib.sha256(raw).hexdigest(), count=count)
                )
                if name == "geometry":
                    # Even a valid polygon snapshot needs temporal/legal and spatial audit.
                    report["territorial_mapping"] = "awaiting_spatial_and_temporal_review"
            except (httpx.HTTPError, ValueError) as exc:
                report["checks"].append(dict(name=name, ok=False, error=str(exc)))
    path = folder / "report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    path.chmod(0o600)
    print(json.dumps({**report, "local_evidence": str(folder)}, ensure_ascii=False, indent=2))
    return 0 if all(item["ok"] for item in report["checks"]) else 1


if __name__ == "__main__":
    raise SystemExit(probe())
