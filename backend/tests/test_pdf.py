"""Independent structural/text checks, without using the writer's encoding helpers."""

import re
from decimal import Decimal

from app.calculations.engine import calculate
from app.reports.pdf import render_report
from app.schemas import CalculationInput, CalculationResult


def extract_pages(pdf):
    # Interpret ToUnicode bfchar pairs, then the hexadecimal Tj text operators.
    cmap = re.search(rb"begincmap(.*?)endcmap", pdf, re.S).group(1)
    mapping = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", cmap, re.S):
        for code, unicode in re.findall(rb"<([A-Fa-f0-9]+)>\s+<([A-Fa-f0-9]+)>", block):
            mapping[int(code, 16)] = bytes.fromhex(unicode.decode()).decode("utf-16-be")
    pages = []
    for stream in re.findall(rb"stream\n(.*?)\nendstream", pdf, re.S):
        if b"BT /F1" not in stream:
            continue
        lines = []
        positions = []
        for size, x, y, text in re.findall(
            rb"BT /F1 ([0-9]+) Tf 1 0 0 1 ([0-9]+) ([0-9]+) Tm <([0-9A-F]*)> Tj ET", stream
        ):
            line = "".join(mapping[int(text[i : i + 4], 16)] for i in range(0, len(text), 4))
            lines.append(line)
            positions.append((int(size), int(x), int(y), line))
        # 602.05/1000 em is independently documented for DejaVu Sans Mono.
        for size, x, y, line in positions:
            assert x >= 40 and 30 <= y <= 800
            assert x + len(line) * size * Decimal("0.602051") < 555
        # Same-row cells are legitimate. Check their actual horizontal intervals.
        for y in {position[2] for position in positions}:
            row = sorted(
                (x, x + len(line) * size * Decimal("0.602051"))
                for size, x, baseline, line in positions
                if baseline == y and line
            )
            assert all(left[1] <= right[0] for left, right in zip(row, row[1:]))
        pages.append("\n".join(lines))
    return pages


def sample(rooms=1):
    project = CalculationInput(
        name="Residência São José",
        municipality="São Paulo",
        built_area_m2="60",
        environments=[
            dict(
                name=f"Quarto {i}",
                area_m2=None,
                perimeter_m=None,
                loads=[
                    dict(
                        name="Lâmpada LED (A) \\ referência " + "texto muito longo " * 8,
                        quantity=4,
                        unit_power_w="9",
                        source="Fonte oficial: " + "https://example.org/" + "a" * 300,
                    )
                ],
            )
            for i in range(rooms)
        ],
    )
    inputs = project.model_dump(mode="json")
    result = CalculationResult.model_validate(calculate(inputs)).model_dump(mode="json")
    return inputs, result


def test_summary_results_unicode_and_structure():
    inputs, result = sample()
    pdf = render_report(inputs, result)
    text = "\n".join(extract_pages(pdf))
    assert "Residência São José" in text
    assert "36 W" in text and "0,036 kW" in text
    assert "Pendente" in text and "Não disponível" in text
    for omitted in [
        "Referências utilizadas",
        result["input_digest"],
    ]:
        assert omitted not in text
    xref = int(re.search(rb"startxref\n(\d+)", pdf).group(1))
    assert pdf[xref : xref + 4] == b"xref"
    for index, offset in enumerate(re.findall(rb"\n(\d{10}) 00000 n ", pdf[xref:]), 1):
        assert pdf[int(offset) :].startswith(f"{index} 0 obj\n".encode())


def test_large_summary_paginates_without_losing_rooms():
    inputs, result = sample(120)
    pages = extract_pages(render_report(inputs, result))
    assert len(pages) > 2
    text = "\n".join(pages)
    assert "Quarto 119" in text and "4320 W" in text
    assert sum("Potência conhecida (W)" in page for page in pages) > 1


def test_missing_power_stays_incomplete():
    inputs, _ = sample()
    inputs["environments"][0]["loads"][0]["unit_power_w"] = None
    result = CalculationResult.model_validate(calculate(inputs)).model_dump(mode="json")
    text = "\n".join(extract_pages(render_report(inputs, result)))
    assert "total incompleto" in text
    assert "Não disponível" in text


def test_notes_are_preserved():
    inputs, result = sample()
    inputs["notes"] = "Conferir cozinha após reforma."
    text = "\n".join(extract_pages(render_report(inputs, result)))
    assert inputs["notes"] in text
    assert "kWh/mês" in text  # consumption columns remain explicit even when unavailable


def test_dimensions_points_and_brasilia_time():
    inputs, result = sample()
    inputs["environments"][0].update(area_m2="12.5", perimeter_m="15", lighting_points=2, outlets=4)
    text = "\n".join(extract_pages(render_report(inputs, result)))
    assert "12,5" in text
    assert "Luz/TUG" not in text and "Perímetro" not in text
    assert "Área construída: 60 m²" in text
    assert "Horário de Brasília" in text and " UTC" not in text


def test_utc_history_is_converted_without_changing_instant():
    from datetime import datetime, timedelta, timezone

    from app.projects import brasilia_time

    utc = datetime(2026, 10, 22, 1, 30, tzinfo=timezone.utc)
    local = brasilia_time(utc)
    assert local.isoformat() == "2026-10-21T22:30:00-03:00"
    assert local == utc
    assert brasilia_time(utc.replace(tzinfo=None)) == utc
    assert local.utcoffset() == timedelta(hours=-3)


def test_energy_results_export_without_formulas_and_with_incomplete_coverage():
    project = CalculationInput(
        name="Consumo mensal",
        municipality="Cidade",
        energy_tariff_brl_per_kwh="0.8",
        environments=[
            dict(
                name="Sala",
                loads=[
                    dict(
                        name="LED",
                        quantity=4,
                        unit_power_w="9",
                        parameters=dict(usage_hours_per_day="5", usage_days_per_month=30),
                    ),
                    dict(name="Sem uso informado", unit_power_w="100"),
                ],
            )
        ],
    ).model_dump(mode="json")
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    text = "\n".join(extract_pages(render_report(project, result)))
    assert "Consumo mensal conhecido" in text
    assert "5,4 kWh" in text
    assert "R$ 4,32" in text
    assert "não é fatura completa" in text
    assert "E_mês" in text


def test_money_has_two_decimals_and_sections_stay_with_content():
    from app.reports.pdf import Document

    project = CalculationInput(
        name="Centavos",
        municipality="Cidade",
        energy_tariff_brl_per_kwh="1",
        environments=[
            dict(
                name="Sala",
                loads=[
                    dict(
                        name="Aparelho",
                        unit_power_w="1000",
                        parameters=dict(monthly_energy_kwh="377.408"),
                    )
                ],
            )
        ],
    ).model_dump(mode="json")
    result = CalculationResult.model_validate(calculate(project)).model_dump(mode="json")
    text = "\n".join(extract_pages(render_report(project, result)))
    assert "R$ 377,41" in text
    assert "R$ 377,408" not in text
    assert result["monthly_cost"]["value"] == "377.408"
    doc = Document()
    doc.line("Página anterior")
    doc.y = 140
    doc.section("Seção com tabela")
    doc.table(["Nome", "Valor"], [("Sala", "100")], [50, 50])
    pages = extract_pages(doc.bytes())
    assert "Seção com tabela" not in pages[0]
    assert "Seção com tabela" in pages[1] and "Sala" in pages[1]
