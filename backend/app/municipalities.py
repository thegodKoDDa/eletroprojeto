"""Official reported municipality/agent relations, never premise supply or legal title.

INDGER is a monthly declaration, not the geometry/contract authority. All matching
agents are retained. Only local hash-checked snapshots are read during requests.
"""

import csv
import hashlib
import json
import re
from datetime import date
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "references" / "municipalities"
SOURCE = "https://dadosabertos.aneel.gov.br/dataset/indger-indicadores-gerenciais-da-distribuicao"
IBGE_SOURCE = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome"
NOTICE = "Relações declaradas no INDGER/ANEEL no mês indicado, com unidades consumidoras ativas. Não são exclusividade municipal, polígono de concessão, vigência jurídica atual ou confirmação de atendimento do imóvel. A seleção da distribuidora permanece manual."


def build_index(csv_file, municipalities):
    """Reject inconsistent identities and conflicting duplicate monthly statements."""
    places = {}
    for item in municipalities:
        code = str(item["id"])
        region = item.get("microrregiao")
        state = (region or {}).get("mesorregiao", {}).get("UF", {}).get("sigla")
        if not state:
            state = item["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"]
        if (
            not re.fullmatch(r"\d{7}", code)
            or code in places
            or not re.fullmatch(r"[A-Z]{2}", state)
        ):
            raise ValueError("Identidade municipal IBGE inválida/duplicada.")
        places[code] = dict(code=code, name=item["nome"], state=state)
    reader = csv.DictReader(csv_file, delimiter=";")
    fields = {
        "DatGeracaoConjuntoDados",
        "NumCNPJ",
        "SigAgente",
        "NomAgente",
        "NomTipoOutorga",
        "DatReferenciaInformada",
        "CodMunicipioIBGE",
        "QtdUCAtiva",
    }
    if not fields.issubset(reader.fieldnames or []):
        raise ValueError("Cabeçalho INDGER incompleto.")
    records = {}
    rows = 0
    unknown_codes = set()
    unassigned_rows = 0
    generated = set()
    for row in reader:
        rows += 1
        code, cnpj = row["CodMunicipioIBGE"], row["NumCNPJ"]
        if not re.fullmatch(r"\d{14}", cnpj):
            raise ValueError("Código IBGE/CNPJ ausente ou inválido; sem conversão por nome.")
        if code == "0":
            # Source contains declarations without a municipal identity. Quarantine
            # explicitly; never map them to a capital or an agent's other towns.
            unassigned_rows += 1
            continue
        if not re.fullmatch(r"\d{7}", code):
            raise ValueError("Código municipal inválido; sem conversão por nome.")
        period = date.fromisoformat(row["DatReferenciaInformada"])
        generation = date.fromisoformat(row["DatGeracaoConjuntoDados"])
        if period.day != 1 or period > generation:
            raise ValueError("Período mensal INDGER inconsistente.")
        generated.add(generation.isoformat())
        amount = row["QtdUCAtiva"]
        count = int(amount) if re.fullmatch(r"\d+", amount or "") else None
        identity = (row["SigAgente"], row["NomAgente"], row["NomTipoOutorga"], count)
        if not all(identity[:3]):
            raise ValueError("Identificação da distribuidora incompleta.")
        key = (code, period.isoformat(), cnpj)
        if key in records and records[key] != identity:
            raise ValueError("Declarações mensais conflitantes; não escolher uma silenciosamente.")
        records[key] = identity
        if code not in places:
            unknown_codes.add(code)
    if not rows:
        raise ValueError("INDGER vazio.")
    latest = {}
    for (code, period, cnpj), identity in records.items():
        key = (code, cnpj)
        if key not in latest or period > latest[key][0]:
            latest[key] = (period, identity)
    output = {}
    for (code, cnpj), (period, (acronym, name, grant, count)) in latest.items():
        if code not in places:
            continue
        if code not in output:
            output[code] = {**places[code], "reference_month": period, "candidates": []}
        output[code]["reference_month"] = max(period, output[code]["reference_month"])
        # Each company can declare a different month. Missing later declarations
        # do not establish closure or succession; retain its own dated evidence.
        if count is not None and count > 0:
            output[code]["candidates"].append(
                dict(
                    cnpj=cnpj,
                    acronym=acronym,
                    name=name,
                    grant_type=grant,
                    active_units=count,
                    reference_month=period,
                )
            )
    for item in output.values():
        item["candidates"].sort(key=lambda c: c["cnpj"])
    return dict(
        format_version=1,
        municipalities=output,
        rows=rows,
        unassigned_rows=unassigned_rows,
        generation_dates=sorted(generated),
        unmatched_ibge_codes=sorted(unknown_codes),
    )


@lru_cache(maxsize=2)
def load_snapshot(folder, digest):
    raw = (folder / "index.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Hash municipal divergente.")
    return json.loads(raw)


def lookup(code):
    result = dict(
        status="pending",
        source=SOURCE,
        ibge_source=IBGE_SOURCE,
        consulted_on=None,
        snapshot_sha256=None,
        automatic_assignment=False,
        municipality=None,
        reference_month=None,
        candidates=[],
        notice=NOTICE,
        reason="Sem coleta municipal local validada; confirme a distribuidora na fatura/contrato.",
    )
    if not ROOT.exists():
        return result
    for path in sorted(ROOT.glob("*/report.json"), reverse=True):
        try:
            report = json.loads(path.read_text())
            if not report.get("validated"):
                continue
            index = load_snapshot(path.parent, report["index_sha256"])
            if index.get("format_version") != 1:
                continue
            item = index["municipalities"].get(code)
            result.update(
                status="awaiting_technical_validation",
                consulted_on=report["consulted_on"],
                snapshot_sha256=report["index_sha256"],
            )
            if item:
                result.update(
                    municipality={k: item[k] for k in ("code", "name", "state")},
                    reference_month=item["reference_month"],
                    candidates=item["candidates"],
                    reason="Distribuidoras com unidades ativas declaradas nesse município e mês; confirme qual atende o endereço."
                    if item["candidates"]
                    else "Sem relação positiva no último mês desse município. Isso não comprova ausência de atendimento.",
                )
            else:
                result["reason"] = (
                    "Código não encontrado nesta coleta. Isso não comprova ausência de atendimento."
                )
            return result
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return result
