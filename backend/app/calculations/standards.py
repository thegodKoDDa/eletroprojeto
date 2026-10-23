"""Reviewed normative procedures and explicit evidence for remaining gaps."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ResearchEvidence:
    title: str
    url: str
    finding: str
    access: str
    consulted_on: str = "2026-10-22"
    section: str | None = None
    file_name: str | None = None
    sha256: str | None = None


ENERGISA_V7_EVIDENCE = ResearchEvidence(
    title="Energisa NDU-001 versão 7.0 — exemplar enviado pelo usuário",
    url="https://www.energisa.com.br/sites/energisa/files/media/documents/2025-02/NDU%20001%20-%20Fornecimento%20de%20energia%20el%C3%A9trica%20em%20tens%C3%A3o%20secund%C3%A1ria%20a%20edifica%C3%A7%C3%B5es%20individuais%20ou%20agrupadas%20em%20at%C3%A9%20tr%C3%AAs%20unidades%20consumidoras.pdf",
    finding="Exemplar local de 162 páginas identifica Energisa, versão 7.0/novembro2024; §§1/2/6/9.1 e tabelas/notas conferidos. Hash identifica o arquivo enviado, sem afirmar igualdade binária com download oficial bloqueado.",
    access="user_supplied_full_text",
    consulted_on="2026-10-23",
    section="§§1/2,9.1 pp.56–57; tabelas5–8/10 pp.63–67; método residencial limitado d1–d5",
    file_name="NDU 001 - Fornecimento de energia elétrica em tensão secundária a edificações individuais ou agrupadas em até três unidades consumidoras.pdf",
    sha256="940b4aab66afc741e2f1f20d88ef2630672dcac2499928af31d807ac8d7442e2",
)


@dataclass(frozen=True)
class Rule:
    code: str
    document: str
    edition: str | None
    effective_date: str | None
    clause: str | None
    source: str
    status: str
    reason: str
    inputs: tuple[str, ...]
    procedure: str | None = None
    limits: str = "Não habilitada para cálculo normativo"
    tests: tuple[str, ...] = ()
    label: str = ""
    purpose: str = ""
    evidence: tuple[ResearchEvidence, ...] = ()
    pending_checks: tuple[str, ...] = ()


ABNT_EVIDENCE = ResearchEvidence(
    title="Catálogo oficial ABNT",
    url="https://www.abntcatalogo.com.br/",
    finding="Identificação da ABNT NBR 5410:2004, versão corrigida de 2008. O catálogo não disponibilizou o texto autorizado completo para esta revisão.",
    access="official_metadata",
)
# Exact residential clauses reviewed in the government-hosted original, the
# corrected edition hosted by PUC Goiás and PF's authored engineering guidance.
RESIDENTIAL_EVIDENCE = (
    ABNT_EVIDENCE,
    ResearchEvidence(
        title="NBR 5410 — acervo público IPAAM/AM",
        url="https://www.ipaam.am.gov.br/wp-content/uploads/2021/01/NBR-05410-05-Instala%C3%A7%C3%B5es-El%C3%A9tricas-de-baixa-Tens%C3%A3o.pdf",
        finding="Texto integral de 2004 consultado: escopo residencial, critérios de iluminação e pontos/cargas de tomadas. Sem redistribuição do documento pelo aplicativo.",
        access="institutional_full_text",
        section="9.5.1 e 9.5.2.1–9.5.2.2, pp. 182–184",
    ),
    ResearchEvidence(
        title="NBR 5410 corrigida em 2008 — acervo docente PUC Goiás",
        url="https://professor.pucgoias.edu.br/SiteDocente/admin/arquivosUpload/18451/material/nbr_5410.pdf",
        finding="Capa e prefácio identificam correção de 17/03/2008; critérios residenciais cotejados com o original. Hospedagem institucional não representa licença de redistribuição.",
        access="institutional_full_text",
        section="9.5.1–9.5.2.2, pp. 182–184",
    ),
    ResearchEvidence(
        title="Polícia Federal — Diretrizes de instalações elétricas 2021a",
        url="https://www.gov.br/pf/pt-br/assuntos/licitacoes/2022/distrito-federal/tomadas-de-precos/tomada-de-precos-no-1-2022-sr-pf-df/edital-da-tomada-de-precos-no-1-2022-sr-pf-df-uasg-200228/1-1-7-anexo-vii-do-pb-diretrizes-projeto-executivo-e-obra-de-instalacoes-eletricas.pdf",
        finding="Seções residenciais corroboram critérios; fatores próprios dos ambientes de trabalho da PF não foram incorporados.",
        access="official_full_text",
        section="5.1 e 5.3.2, pp. 17–21",
    ),
)

RULES = (
    Rule(
        code="lighting",
        document="ABNT NBR 5410",
        edition="2004, versão corrigida 2008",
        effective_date="2005-03-31",
        clause="9.5.1; 9.5.2.1.1–9.5.2.1.2",
        source="https://www.abntcatalogo.com.br/",
        status="calculated",
        reason="Procedimento de previsão residencial implementado e testado no escopo indicado; não certifica a instalação.",
        inputs=("environment.type", "environment.area_m2", "environment.lighting_points"),
        procedure="app.calculations.residential.lighting_minimum",
        limits="Opt-in pelo escopo residencial. Ambientes internos classificados; externo/outro sem inferência. Somente quantidades/cargas em VA; sem localização, lux, circuitos ou conformidade integral.",
        tests=("tests/test_residential.py",),
        label="Previsão mínima de iluminação",
        purpose="Previsão de carga e pontos de iluminação por ambiente; distinta da soma das lâmpadas cadastradas e de estudo de iluminância em lux.",
        evidence=RESIDENTIAL_EVIDENCE,
    ),
    Rule(
        code="outlets",
        document="ABNT NBR 5410",
        edition="2004, versão corrigida 2008",
        effective_date="2005-03-31",
        clause="9.5.1; 9.5.2.2.1–9.5.2.2.2",
        source="https://www.abntcatalogo.com.br/",
        status="calculated",
        reason="Procedimento de previsão residencial implementado e testado no escopo indicado; não certifica a instalação.",
        inputs=(
            "environment.type",
            "environment.area_m2",
            "environment.perimeter_m",
            "environment.outlets",
        ),
        procedure="app.calculations.residential.outlet_minimum/outlet_load",
        limits="Opt-in residencial, ambientes internos classificados. Quantidade de pontos e VA; sem verificação de localização, distribuição ou circuitos. Método básico sem redução opcional para conjunto de áreas molhadas.",
        tests=("tests/test_residential.py",),
        label="Previsão de tomadas",
        purpose="Previsão de pontos e cargas de tomadas por ambiente; distinta da lista de eletrodomésticos cadastrados.",
        evidence=RESIDENTIAL_EVIDENCE,
    ),
    Rule(
        "demand",
        "Energisa NDU-001",
        "7.0",
        "2024-11-01",
        "§9.1, Tabelas5–8/10",
        "https://www.energisa.com.br/normas-tecnicas",
        "estimated",
        "Método residencial §9.1 d1–d5 integrado ao cadastro mediante classificação e revisão explícitas; grupos especiais presentes exigem revisão própria.",
        ("utility", "state", "energisa_demand", "environments.loads.energisa_demand"),
        procedure="app.calculations.project_demand.project_energisa_demand",
        limits="Somente residência individual Energisa Sul-Sudeste/SP até75kW, d1–d5, inventário explicitamente classificado/revisado. Grupos d6/d7 ou centrais presentes fora do escopo; sem dimensionamento final.",
        tests=("tests/test_energisa.py", "tests/test_project_demand.py", "tests/test_api.py"),
        label="Demanda da distribuidora",
        purpose="Estimativa de potência demandada pelo método da distribuidora; não é potência instalada nem consumo mensal.",
        evidence=(
            ENERGISA_V7_EVIDENCE,
            ResearchEvidence(
                title="Portal oficial de normas Energisa",
                url="https://www.energisa.com.br/normas-tecnicas",
                finding="Portal indexado identifica NDU-001 versão 7.0, vigência 01/11/2024.",
                access="official_index",
            ),
            ResearchEvidence(
                title="Energisa NDU-001 — PDF oficial",
                url="https://www.energisa.com.br/sites/energisa/files/media/documents/2025-11/NDU%20001%20-%20Fornecimento%20de%20Energia%20El%C3%A9trica%20em%20Tens%C3%A3o%20Secund%C3%A1ria%20a%20Edifica%C3%A7%C3%B5es%20Individuais_0.pdf",
                finding="Indexação identifica conceitos de carga instalada/demanda e método com sete parcelas por grupos. A leitura integral foi bloqueada; não autoriza executar fatores.",
                access="official_index",
                section="5.7/5.11 (p. 14) e 9.1 (p. 56), identificadas na indexação",
            ),
        ),
        pending_checks=(
            "No método parametrizado, declarar inventário completo e classificação explícita, ausência dos grupos e reservas; base W distinta das previsões VA.",
            "Revisar grupos d6/d7 e unidades centrais de ar-condicionado antes de ampliar o escopo.",
            "Revisar o inventário do projeto; selecionar a distribuidora sozinho não confirma classificação nem escopo.",
        ),
    ),
)


def pending_rule(code: str) -> dict:
    rule = next(rule for rule in RULES if rule.code == code)
    return {
        "value": None,
        "unit": "kVA" if code == "demand" else "VA",
        "status": "pending" if rule.procedure or code == "demand" else rule.status,
        "reference": asdict(rule),
        "reason": "Ative o painel de demanda e revise classificação, inventário e escopo para usar a NDU-001 7.0 d1–d5."
        if code == "demand"
        else rule.reason,
    }
