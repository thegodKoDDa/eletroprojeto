"""Collect official INDGER/IBGE evidence, immutable private local files only."""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.municipalities import IBGE_SOURCE, SOURCE, build_index  # noqa: E402

CKAN = "https://dadosabertos.aneel.gov.br/api/3/action/package_show?id=indger-indicadores-gerenciais-da-distribuicao"


def collect():
    folder = (
        ROOT
        / "references"
        / "municipalities"
        / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )
    folder.mkdir(parents=True, mode=0o700)
    folder.parent.chmod(0o700)
    report = dict(
        source=SOURCE,
        consulted_on=datetime.now(timezone.utc).isoformat(),
        validated=False,
        automatic_assignment=False,
    )

    def save(name, raw):
        path = folder / name
        path.write_bytes(raw)
        path.chmod(0o600)
        return hashlib.sha256(raw).hexdigest()

    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            response = client.get(CKAN)
            response.raise_for_status()
            report["metadata_sha256"] = save("metadata.json", response.content)
            metadata = response.json()
            if metadata.get("success") is not True:
                raise ValueError("Resposta CKAN inválida.")
            resource = next(
                r
                for r in metadata["result"]["resources"]
                if r["url"].endswith("/indger-dados-comerciais.csv")
            )
            url = resource["url"]
            if not url.startswith("https://dadosabertos.aneel.gov.br/"):
                raise ValueError("Origem INDGER inesperada.")
            report["csv_url"] = url
            with client.stream("GET", url) as response:
                response.raise_for_status()
                path = folder / "indger.csv"
                size = 0
                with path.open("xb") as target:
                    os.chmod(path, 0o600)
                    for block in response.iter_bytes():
                        size += len(block)
                        if size > 300_000_000:
                            raise ValueError("INDGER excede limite de coleta.")
                        target.write(block)
                if resource.get("size") and size != resource["size"]:
                    raise ValueError(
                        "Tamanho diverge dos metadados; recoletar após estabilização da fonte."
                    )
            report["csv_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            response = client.get(IBGE_SOURCE)
            response.raise_for_status()
            report["ibge_sha256"] = save("ibge.json", response.content)
            with path.open(encoding="utf-8-sig", newline="") as source:
                index = build_index(source, response.json())
        report["index_sha256"] = save(
            "index.json", (json.dumps(index, ensure_ascii=False, sort_keys=True) + "\n").encode()
        )
        report.update(
            validated=True,
            rows=index["rows"],
            municipality_count=len(index["municipalities"]),
            unassigned_rows=index["unassigned_rows"],
            generation_dates=index["generation_dates"],
            unmatched_ibge_codes=index["unmatched_ibge_codes"],
        )
    except (httpx.HTTPError, ValueError, KeyError, StopIteration) as exc:
        report["error"] = str(exc)
    save("report.json", (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    print(json.dumps({**report, "local_evidence": str(folder)}, ensure_ascii=False, indent=2))
    return 0 if report["validated"] else 1


if __name__ == "__main__":
    raise SystemExit(collect())
