"""Small A4 PDF writer using an embedded, licensed monospaced TrueType font.

No network, HTML execution or viewer-dependent printing. Text wraps by glyph
width, tables split across pages, and ToUnicode preserves Portuguese extraction.
This renderer does not execute or accept technical results from the browser.
"""

import struct
import textwrap
from decimal import ROUND_HALF_UP, Decimal, localcontext
from functools import lru_cache
from pathlib import Path

from .summary import build_summary


@lru_cache(maxsize=1)
def font():
    data = (Path(__file__).parent / "assets/DejaVuSansMono.ttf").read_bytes()
    tables = {}
    for i in range(struct.unpack_from(">H", data, 4)[0]):
        tag, _, offset, size = struct.unpack_from(">4sIII", data, 12 + 16 * i)
        tables[tag.decode()] = data[offset : offset + size]
    cmap = tables["cmap"]
    subtables = []
    for i in range(struct.unpack_from(">H", cmap, 2)[0]):
        _, _, offset = struct.unpack_from(">HHI", cmap, 4 + 8 * i)
        if struct.unpack_from(">H", cmap, offset)[0] == 4:
            subtables.append(cmap[offset:])
    mapping = {}
    sub = subtables[0]
    n = struct.unpack_from(">H", sub, 6)[0] // 2
    end, start, delta, ranges = 14, 16 + 2 * n, 16 + 4 * n, 16 + 6 * n
    for i in range(n):
        last = struct.unpack_from(">H", sub, end + 2 * i)[0]
        first = struct.unpack_from(">H", sub, start + 2 * i)[0]
        diff = struct.unpack_from(">h", sub, delta + 2 * i)[0]
        location = ranges + 2 * i
        relative = struct.unpack_from(">H", sub, location)[0]
        for code in range(first, last + 1):
            if code == 65535:
                continue
            glyph = (
                struct.unpack_from(">H", sub, location + relative + 2 * (code - first))[0]
                if relative
                else code
            )
            glyph = (glyph + diff) & 65535 if glyph or not relative else 0
            if glyph:
                mapping[chr(code)] = glyph
    units = struct.unpack_from(">H", tables["head"], 18)[0]
    width = struct.unpack_from(">H", tables["hmtx"], 0)[0] * 1000 / units
    return data, mapping, width


def printable(value):
    mapping = font()[1]
    return "".join(
        c if c in mapping else "\n" if c == "\n" else f"[U+{ord(c):04X}]" for c in str(value)
    )


class Document:
    """A4 layout with positioned cells, repeated headers and rows kept together."""

    def __init__(self):
        self.pages = [[]]
        self.boxes = [[]]
        self.y = 784

    def page(self):
        self.pages.append([])
        self.boxes.append([])
        self.y = 784

    def reserve(self, height):
        if self.y - height < 64:
            self.page()
            return True
        return False

    def text(self, text, x=44, size=9):
        self.pages[-1].append((text, size, int(x), int(self.y)))

    def wrapped(self, value, width=505, size=9):
        limit = max(1, int(width / (font()[2] * size / 1000)))
        return [
            line
            for paragraph in printable(value).split("\n")
            for line in (textwrap.wrap(paragraph, width=limit, replace_whitespace=False) or [""])
        ]

    def line(self, value="", heading=False):
        size = 12 if heading else 9
        for text in self.wrapped(value, size=size):
            self.reserve(15)
            self.text(text, size=size)
            self.y -= 15 if heading else 12

    def section(self, title):
        self.reserve(130)
        self.y -= 10
        self.boxes[-1].append((44, self.y - 6, 507, 23, 0.92))
        self.line(title, heading=True)
        self.y -= 10

    def block(self, title, lines):
        height = (
            len(self.wrapped(title)) * 12 + sum(len(self.wrapped(line)) * 12 for line in lines) + 5
        )
        self.reserve(height if height <= 680 else 140)
        self.line(title)
        for line in lines:
            self.line(line)
        self.y -= 5

    def table(self, headers, rows, widths, caption=None):
        total = sum(widths)
        sizes = [507 * w / total for w in widths]

        def layout(row):
            return [self.wrapped(cell, width=width - 12, size=9) for cell, width in zip(row, sizes)]

        def draw(columns, shade=None):
            height = max(map(len, columns)) * 13 + 10
            if shade is not None:
                self.boxes[-1].append((44, self.y - height + 7, 507, height, shade))
            top, x = self.y, 44
            for lines, width in zip(columns, sizes):
                for index, line in enumerate(lines):
                    self.y = top - index * 13
                    self.text(line, x + 6)
                x += width
            self.y = top - height

        header = layout(headers)
        header_height = max(map(len, header)) * 13 + 10
        first_height = max(map(len, layout(rows[0]))) * 13 + 10 if rows else 35
        self.reserve(min(header_height + first_height + (24 if caption else 0), 680))
        if caption:
            self.line(caption)
        draw(header, 0.88)
        for index, row in enumerate(rows):
            columns = layout(row)
            height = max(map(len, columns)) * 13 + 10
            if self.reserve(min(height, 640)):
                if caption:
                    self.line(caption + " · continuação")
                draw(header, 0.88)
            # Oversized cells can continue, but normal rows are never split.
            while max(map(len, columns)) * 13 + 10 > self.y - 64:
                count = max(1, int((self.y - 74) / 13))
                draw([column[:count] for column in columns], 0.97 if index % 2 == 0 else None)
                columns = [column[count:] or [""] for column in columns]
                self.page()
                draw(header, 0.88)
            draw(columns, 0.97 if index % 2 == 0 else None)
        self.y -= 8

    def bytes(self):
        data, mapping, width = font()
        footers = [
            f"EletroProjeto · Consumo e cargas · Página {i + 1}/{len(self.pages)}"
            for i in range(len(self.pages))
        ]
        chars = sorted(
            set("".join(text for page in self.pages for text, _, _, _ in page) + "".join(footers))
        )
        codes = {c: i + 1 for i, c in enumerate(chars)}

        def encoded(text):
            return "".join(f"{codes[c]:04X}" for c in text)

        objects = []

        def obj(value):
            objects.append(value.encode("ascii") if isinstance(value, str) else value)
            return len(objects)

        def stream(value, extra=""):
            return obj(
                f"<< /Length {len(value)} {extra} >>\nstream\n".encode() + value + b"\nendstream"
            )

        root = obj("")
        pages = obj("")
        file_id = stream(data, f"/Length1 {len(data)}")
        descriptor = obj(
            f"<< /Type /FontDescriptor /FontName /DejaVuSansMono /Flags 33 /FontBBox [-600 -400 1500 1100] /ItalicAngle 0 /Ascent 930 /Descent -240 /CapHeight 730 /StemV 80 /FontFile2 {file_id} 0 R >>"
        )
        glyph_map = stream(b"\0\0" + b"".join(struct.pack(">H", mapping[c]) for c in chars))
        cidfont = obj(
            f"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /DejaVuSansMono /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor {descriptor} 0 R /DW {width:.4f} /CIDToGIDMap {glyph_map} 0 R >>"
        )
        unicode_lines = [
            "/CIDInit /ProcSet findresource begin",
            "12 dict begin",
            "begincmap",
            "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def",
            "/CMapName /EletroUnicode def",
            "/CMapType 2 def",
            "1 begincodespacerange",
            "<0000> <FFFF>",
            "endcodespacerange",
        ]
        for start in range(0, len(chars), 100):
            chunk = chars[start : start + 100]
            unicode_lines += (
                [f"{len(chunk)} beginbfchar"]
                + [f"<{codes[c]:04X}> <{c.encode('utf-16-be').hex()}>" for c in chunk]
                + ["endbfchar"]
            )
        unicode_lines += ["endcmap", "CMapName currentdict /CMap defineresource pop", "end", "end"]
        unicode_id = stream("\n".join(unicode_lines).encode())
        font_id = obj(
            f"<< /Type /Font /Subtype /Type0 /BaseFont /DejaVuSansMono /Encoding /Identity-H /DescendantFonts [{cidfont} 0 R] /ToUnicode {unicode_id} 0 R >>"
        )
        page_ids = []
        for index, page in enumerate(self.pages):
            commands = []
            for x, y, w, h, shade in self.boxes[index]:
                commands.append(f"q {shade} g {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f Q")
            for text, size, x, y in page:
                commands.append(f"BT /F1 {size} Tf 1 0 0 1 {x} {y} Tm <{encoded(text)}> Tj ET")
            commands.append(f"BT /F1 8 Tf 1 0 0 1 44 35 Tm <{encoded(footers[index])}> Tj ET")
            content = stream("\n".join(commands).encode())
            page_ids.append(
                obj(
                    f"<< /Type /Page /Parent {pages} 0 R /MediaBox [0 0 595.28 841.89] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content} 0 R >>"
                )
            )
        objects[root - 1] = f"<< /Type /Catalog /Pages {pages} 0 R >>".encode()
        objects[pages - 1] = (
            f"<< /Type /Pages /Count {len(page_ids)} /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] >>".encode()
        )
        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, value in enumerate(objects):
            offsets.append(len(output))
            output.extend(f"{i + 1} 0 obj\n".encode() + value + b"\nendobj\n")
        xref = len(output)
        output.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode())
        output.extend(
            f"trailer\n<< /Size {len(offsets)} /Root {root} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        )
        return bytes(output)


def render_report(project, result, project_version=None):
    """Concise results only; computation and provenance stay in the application."""
    summary = build_summary(project, result, project_version=project_version)
    doc = Document()
    labels = {
        "calculated": "Calculado",
        "estimated": "Estimado",
        "pending": "Pendente",
        "invalid": "Inválido",
        "out_of_scope": "Fora do escopo",
        "awaiting_technical_validation": "Indisponível",
    }

    def val(value):
        if value is None:
            return "Não disponível"
        with localcontext() as ctx:
            ctx.prec = 50
            original = Decimal(str(value))
            number = original.quantize(Decimal("0.001"))
            if original != 0 and number == 0:
                return "<0,001"
            return (
                format(number, "f").rstrip("0").rstrip(".").replace(".", ",")
                if "." in format(number, "f")
                else format(number, "f")
            )

    def row(label, item):
        item = item or {}
        value = val(item.get("value"))
        if item.get("value") is not None:
            value = (
                "R$ "
                + format(
                    Decimal(str(item["value"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    ".2f",
                ).replace(".", ",")
                if item.get("unit") == "BRL"
                else value + " " + item.get("unit", "")
            )
        return label, value, labels.get(item.get("status"), "Pendente")

    rooms = project["environments"]
    doc.line(project.get("name") or "Projeto sem nome", heading=True)
    doc.line("Consumo residencial e resumo de cargas · estudo preliminar")
    doc.line(" · ".join(filter(None, [project.get("municipality"), project.get("state")])))
    doc.line("Emissão: " + summary["emissao"]["data_hora"] + " · Horário de Brasília")
    if project_version is not None:
        doc.line(f"Revisão salva do projeto: {project_version}")
    doc.line("Distribuidora informada: " + summary["projeto"]["distribuidora"])
    doc.line("Área construída: " + val(project.get("built_area_m2")) + " m²")
    if project.get("residence_type"):
        doc.line("Tipo de residência: " + project["residence_type"])
    if project.get("floors") is not None:
        doc.line("Pavimentos: " + str(project["floors"]))
    doc.line(
        f"Ambientes: {len(rooms)} · Equipamentos: {summary['consumo']['cargas_cadastradas']} cadastros / {summary['consumo']['unidades_cadastradas']} unidades"
    )
    doc.section("Resultados gerais")
    doc.table(
        ["Resultado", "Valor", "Situação"],
        [
            row(
                "Consumo mensal conhecido"
                if summary["consumo"]["situacao"] == "parcial"
                else "Consumo mensal estimado",
                result.get("monthly_energy"),
            ),
            row("Custo mensal estimado da energia", result.get("monthly_cost")),
            row("Projeção de consumo em 12 meses", result.get("annual_energy")),
            row("Projeção de custo em 12 meses", result.get("annual_cost")),
            row(
                "Potência conhecida (total incompleto)"
                if result.get("unknown_load_ids")
                else "Potência instalada",
                result["installed_power"],
            ),
            row("Potência instalada em kW", result["installed_power_kw"]),
            row("Iluminação nominal incluída no total", result["lighting_nominal"]),
            row("Potência aparente (soma escalar)", result.get("apparent_power")),
            row("Potência aparente em kVA", result.get("apparent_power_kva")),
        ],
        [45, 25, 30],
    )
    coverage = summary["consumo"]
    if coverage["cargas_cadastradas"]:
        doc.line(
            f"Cobertura do consumo: {coverage['cargas_com_estimativa']} de {coverage['cargas_cadastradas']} cargas cadastradas com estimativa."
        )
    else:
        doc.line("Sem equipamentos cadastrados; o consumo da residência ainda não foi estimado.")
    if coverage["situacao"] == "parcial":
        doc.line("Consumo parcial: o subtotal conhecido não representa o total da residência.")
    elif coverage["situacao"] == "nao_estimado" and coverage["cargas_cadastradas"]:
        doc.line(
            "Consumo não estimado: faltam dados de uso. Potência instalada não equivale a consumo mensal."
        )
    doc.line(
        "Tarifa informada: "
        + (
            val(coverage["tarifa_brl_por_kwh"]) + " BRL/kWh"
            if coverage["tarifa_brl_por_kwh"] is not None
            else "não informada; custo não estimado."
        )
    )
    doc.line(
        "Consumo mensal em kWh para os hábitos informados; não é medição. Custo pela tarifa informada; não é fatura completa, sem encargos fixos ou tributos adicionais."
    )
    if result.get("annual_energy") is not None:
        doc.line(
            "Projeção de 12 meses: repete o uso mensal ou usa a energia anual declarada. Sem sazonalidade ou reajuste de tarifa presumidos; subtotal quando há pendências."
        )
    if result.get("apparent_power") is None:
        doc.line(
            "VA indisponível: confira potência elétrica e fator de potência dos equipamentos. Esses dados não impedem a estimativa de consumo em kWh quando há dados suficientes de uso."
        )
    doc.section("Consumo por ambiente")
    doc.table(
        ["Ambiente", "kWh/mês", "Custo BRL/mês", "Cobertura"],
        [
            (
                r["nome"],
                val(r["consumo_mensal_kwh"]),
                val(r.get("custo_mensal_brl")),
                "Não estimado"
                if r["consumo_mensal_kwh"] is None
                else "Parcial"
                if r["consumo_incompleto"]
                else "Cargas cadastradas",
            )
            for r in summary["ambientes"]
        ],
        [34, 20, 22, 24],
    )
    doc.section("Potência por ambiente")
    doc.table(
        ["Ambiente", "Área m²", "Perímetro m", "Luz/TUG", "Potência conhecida (W)"],
        [
            (
                room["name"],
                val(room.get("area_m2")),
                val(room.get("perimeter_m")),
                f"{room.get('lighting_points') if room.get('lighting_points') is not None else '—'} / {room.get('outlets') if room.get('outlets') is not None else '—'}",
                val(result["by_environment_w"].get(room["id"]))
                + (
                    " (parcial)"
                    if any(
                        load["id"] in result.get("unknown_load_ids", []) for load in room["loads"]
                    )
                    else ""
                ),
            )
            for room in rooms
        ],
        [28, 14, 16, 14, 28],
    )
    doc.line(
        "Luz/TUG: pontos de luz e tomadas cadastrados; não representam mínimos normativos. W parcial é somente o subtotal conhecido, não o total do ambiente."
    )
    if result.get("normative_environments"):
        doc.section("Previsão residencial por ambiente")
        doc.table(
            ["Ambiente", "Luz VA", "Mín. luz", "Mín. TUG", "TUG VA"],
            [
                (
                    r["name"],
                    val(r["lighting_va"]),
                    str(r["minimum_lighting_points"] or "—"),
                    str(r["minimum_outlet_points"] or "—"),
                    val(r["outlets_va"]),
                )
                for r in result["normative_environments"]
            ],
            [32, 17, 17, 17, 17],
        )
        for room in summary["previsao_residencial_por_ambiente"]:
            if (
                room["faltam_pontos_de_luz"]
                or room["faltam_pontos_tug"]
                or room["dados_faltantes"]
                or room["situacao"] == "out_of_scope"
            ):
                doc.line(
                    room["nome"]
                    + ": "
                    + (
                        "faltam " + str(room["faltam_pontos_de_luz"]) + " ponto(s) de luz; "
                        if room["faltam_pontos_de_luz"]
                        else ""
                    )
                    + (
                        "faltam " + str(room["faltam_pontos_tug"]) + " ponto(s) TUG; "
                        if room["faltam_pontos_tug"]
                        else ""
                    )
                    + (
                        "informar " + ", ".join(room["dados_faltantes"])
                        if room["dados_faltantes"]
                        else ""
                    )
                    + (room["motivo"] if room["situacao"] == "out_of_scope" else "")
                )
        doc.line(
            "TUG considera o maior entre os pontos cadastrados e o mínimo previsto. VA separado de W. Localização, distribuição e proteção não verificadas."
        )
    if summary["equipamentos"]:
        doc.section("Equipamentos e uso considerado")
        offset = 0
        for room in rooms:
            items = summary["equipamentos"][offset : offset + len(room["loads"])]
            offset += len(room["loads"])
            if not items:
                continue
            doc.table(
                ["Equipamento / uso", "Qtd.", "W/un.", "W total", "kWh/mês"],
                [
                    (
                        item["nome"]
                        + " · "
                        + (
                            val(item["consumo_unitario_informado_kwh"])
                            + " kWh/mês por unidade informado"
                            if item["consumo_unitario_informado_kwh"] is not None
                            else val(item.get("consumo_anual_unitario_informado_kwh"))
                            + " kWh/ano/un. (média)"
                            if item.get("consumo_anual_unitario_informado_kwh") is not None
                            else val(item.get("minutos_por_dia"))
                            + " min/dia × "
                            + str(item["dias_por_mes"])
                            + " dias"
                            if item.get("minutos_por_dia") is not None
                            else val(item["horas_por_dia"])
                            + " h/dia; "
                            + str(item["dias_por_mes"])
                            + " dias/mês"
                            if item["horas_por_dia"] is not None
                            else "uso não informado"
                        )
                        + (
                            " · " + item["tipo_potencia"]
                            if item["classificacao_potencia"] in ("maximum", "manual", "estimated")
                            else ""
                        ),
                        str(item["quantidade"]),
                        val(item["potencia_unitaria_w"]),
                        val(item["potencia_total_w"]),
                        val(item["consumo_mensal_kwh"]),
                    )
                    for item in items
                ],
                [43, 8, 16, 16, 17],
                caption=room["name"],
            )
        doc.line(
            "Consumo e potência total da quantidade cadastrada. Consumo mensal informado por unidade prevalece sobre horários. A estimativa por horários considera potência constante no funcionamento efetivo; não presume ciclos, standby ou aparelhos ausentes. Potências de referência não são universais; valores manuais foram mantidos."
        )
    if summary["pendencias_consumo"]:
        doc.section("Para completar a estimativa de consumo")
        doc.table(
            ["Ambiente / equipamento", "O que informar"],
            [
                (p["ambiente"] + " / " + p["equipamento"], p["necessario"])
                for p in summary["pendencias_consumo"]
            ],
            [38, 62],
        )
    doc.section("Potência por categoria")
    doc.table(
        ["Categoria", "Potência conhecida (W)", "Consumo conhecido kWh/mês"],
        [
            (item["nome"], val(item["potencia_conhecida_w"]), val(item["consumo_mensal_kwh"]))
            for item in summary["categorias"]
        ],
        [36, 32, 32],
    )
    doc.section("Cobertura normativa")
    doc.table(
        ["Resultado", "Valor", "Situação"],
        [
            row(title, result["normative"][key])
            for key, title in [
                ("lighting", "Iluminação mínima"),
                ("outlets", "Previsão de tomadas"),
                ("demand", "Demanda da distribuidora"),
            ]
        ],
        [45, 25, 30],
    )
    if project.get("analysis_scope") != "normative":
        doc.line("Previsão residencial de iluminação/TUG não solicitada neste estudo.")
    doc.line(
        "Previsões normativas indisponíveis neste estudo não indicam falhas no cadastro. Valores nulos não representam zero."
    )
    regional = result.get("energisa_demand")
    if regional:
        doc.section("Demanda revisada — NDU-001 7.0")
        doc.line(
            "Estimativa d1–d7; inventário e classificação declarados. Não dimensiona a instalação."
        )
        declarations = regional["declarations"]
        unit_labels = {
            "individual_residential": "Residência individual",
            "grouped": "Unidades agrupadas",
            "non_residential": "Não residencial",
            "unconfirmed": "Não confirmado",
        }

        def answer(value):
            return "Sim" if value is True else "Não" if value is False else "Não confirmado"

        doc.line(
            "Unidade declarada: " + unit_labels.get(declarations.get("unit_type"), "Não confirmado")
        )
        doc.line(
            "Letreiros/vitrines: "
            + answer(declarations.get("has_signage_or_display_lighting"))
            + "; uso simultâneo de luz/TUG: "
            + answer(declarations.get("simultaneous_lighting_outlets"))
        )
        doc.line(
            "Reservas não entram na demanda; suas potências permanecem na conferência do limite de carga instalada."
        )
        doc.line(
            "Grupos confirmados ausentes: "
            + ", ".join(declarations.get("confirmed_absent_groups", []))
        )
        doc.line(
            "Inventário revisado: "
            + ("Sim" if regional["inventory_reviewed"] else "Não / confirmação desatualizada")
        )
        doc.table(
            ["Ambiente / equipamento", "Grupo", "Reserva", "Quantidade", "W/unidade"],
            [
                (
                    f"{item['environment']} / {item['name']}",
                    item["group"] or "Pendente",
                    "Sim" if item["reserve"] else "Não",
                    str(item["quantity"]),
                    val(item["unit_power_w"]),
                )
                for item in regional["inventory"]
            ],
            [44, 12, 12, 14, 18],
        )
        if regional["groups"]:
            doc.table(
                ["Grupo", "Quantidade", "Instalada W", "Demanda W"],
                [
                    (
                        item["group"],
                        str(item["quantity"]),
                        val(item["installed_power_w"]),
                        val(item["demand_w"]),
                    )
                    for item in regional["groups"]
                ],
                [20, 20, 30, 30],
            )
        for group in regional["groups"]:
            if group["factor"] is not None:
                doc.line(group["group"] + " — fator por quantidade: " + val(group["factor"]))
            if group["bands"]:
                doc.line(group["group"] + " — parcelas de iluminação/TUG ou AC individual")
                doc.table(
                    ["Faixa W", "Fator", "Demanda W"],
                    [
                        (val(band["installed_band_w"]), val(band["factor"]), val(band["demand_w"]))
                        for band in group["bands"]
                    ],
                    [35, 30, 35],
                )
            for component in group.get("components", []):
                doc.line(
                    component["name"]
                    + " — "
                    + str(component["quantity"])
                    + " unidade(s); referência "
                    + component["table"]
                    + "; VA/unidade="
                    + val(component["unit_apparent_demand_va"])
                    + "; FP="
                    + val(component["power_factor"])
                    + "; fator="
                    + val(component["factor"])
                    + "; demanda W="
                    + val(component["demand_w"])
                    + "; fonte: "
                    + component["source"]
                )
        for message in regional["pending_checks"] + regional["limitations"]:
            doc.line(message)
        doc.line(
            "Referência: "
            + regional["reference"]["title"]
            + "; "
            + regional["reference"]["section"]
        )
    if result.get("bathroom_geometry_results"):
        doc.section("Localização — volumes de chuveiro (estudo condicionado)")
        for room in result["bathroom_geometry_results"]:
            doc.line(room["name"] + " — " + room["status"])
            for point in room["points"]:
                doc.line(
                    point["name"]
                    + "; volume="
                    + (point["volume"] or "pendente")
                    + "; distância horizontal mínima="
                    + val(point["nearest_horizontal_distance_m"])
                    + " m"
                )
                for message in point["pending_checks"]:
                    doc.line(message)
            for message in room["pending_checks"] + room["limitations"]:
                doc.line(message)
            doc.line(room["reference"])
    if result.get("circuit_results"):
        doc.section("Estudo de circuitos — seleção condicionada")
        for circuit in result["circuit_results"]:
            doc.line(circuit["name"])
            for condition in circuit.get("study_conditions", []):
                doc.line(condition)
            doc.line(
                "Ib="
                + val(circuit["design_current_a"])
                + " A; In="
                + val(circuit["breaker_a"])
                + " A; fase="
                + val(circuit["phase_section_mm2"])
                + " mm²; PE="
                + val(circuit["pe_section_mm2"])
                + " mm²"
            )
            doc.line(
                "Queda estimada="
                + val(circuit["voltage_drop_percent"])
                + "%; total="
                + val(circuit["total_drop_percent"])
                + "%"
            )
            for check in circuit["pending_checks"]:
                doc.line("Pendente: " + check)
            for check in circuit.get("protection_checks", []):
                doc.line(
                    check["label"]
                    + ": "
                    + (
                        "atende ao critério informado"
                        if check["passed"] is True
                        else "não atende"
                        if check["passed"] is False
                        else "pendente"
                    )
                    + "; "
                    + check["reason"]
                )
            doc.line(circuit["reference"])
    entry = result.get("service_entry")
    if entry is not None:
        doc.section("Entrada de energia — referência limitada")
        doc.line(
            "Categoria=" + (entry["category"] or "Pendente") + "; fases=" + val(entry["phases"])
        )
        doc.line(
            "Mínimos fase/neutro/terra: "
            + val(entry["minimum_phase_mm2"])
            + "/"
            + val(entry["minimum_neutral_mm2"])
            + "/"
            + val(entry["minimum_earthing_mm2"])
            + " mm²"
        )
        for check in entry["pending_checks"]:
            doc.line(check)
        doc.line(entry["reference"])
    doc.section("Para conversar com a distribuidora")
    doc.line(summary["atendimento_distribuidora"]["situacao"])
    if not summary["atendimento_distribuidora"]["demanda_disponivel"]:
        doc.line(summary["atendimento_distribuidora"]["motivo"])
    doc.line(summary["atendimento_distribuidora"]["cobertura_territorial"])
    doc.line(summary["atendimento_distribuidora"]["orientacao"])
    doc.line(
        "Estudo preliminar de cargas; não constitui dimensionamento final nem aprovação do pedido de ligação."
    )
    if project.get("notes"):
        doc.section("Observações do projeto")
        doc.line(project["notes"])
    return doc.bytes()
