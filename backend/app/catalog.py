"""Primary-source model references and explicitly estimated utility references.

Model variants are never presented as exact ratings for a generic category.
"""

from .equipment_relevance import recommended_rooms
from .schemas import CatalogItem

VERIFIED_ON = "2026-10-21"
ENEL = "https://www.eneldistribuicao.com.br/Equipamentos.aspx"


def reference(
    id,
    name,
    category,
    equipment_type,
    power,
    source_url,
    document,
    *,
    brand=None,
    model=None,
    voltage=None,
    voltage_range=None,
    pf=None,
    technology="",
    rating="nominal",
    parameters=None,
    note=None,
):
    return CatalogItem(
        id=id,
        name=name,
        category=category,
        equipment_type=equipment_type,
        kind="lighting" if equipment_type == "lighting" else "specific_use",
        reference_power_w=power,
        voltage_v=voltage,
        voltage_range=voltage_range,
        power_factor=pf,
        technology=technology,
        brand=brand,
        model=model,
        power_rating=rating,
        source=brand or "Enel — referência genérica de equipamento",
        source_url=source_url,
        document=document,
        verified_on=VERIFIED_ON,
        status="verified",
        parameters=parameters or {},
        note=note
        or "Parâmetros declarados para este modelo e variante. Confirme a placa; todos os valores são editáveis.",
    ).model_dump(mode="json")


CATALOG = [
    reference(
        "philips-led-929001195311",
        "LED Philips 9 W · E27",
        "Iluminação",
        "lighting",
        "9",
        "https://www.assets.lighting.philips.com/is/content/PhilipsLighting/fp929001195311-pss-pt_br",
        "Ficha 929001195311, 29/04/2023, dados elétricos",
        brand="Philips/Signify",
        model="LEDBulb9-60W E27 3000K 929001195311",
        pf="0.7",
        voltage_range="100–240 V",
        technology="LED",
    ),
    reference(
        "samsung-tv43-au7700",
        "Televisor LED 43″ · Samsung AU7700",
        "Outros",
        "television",
        "130",
        "https://www.samsung.com/br/tvs/uhd-4k-tv/au7000-uhd-4k-smart-tv-2021-43-inch-un43au7700gxzd/",
        "Especificações: alimentação e recursos Eco, consumo máximo",
        brand="Samsung",
        model="UN43AU7700GXZD",
        voltage_range="100–240 V",
        technology="LED",
        rating="maximum",
        parameters={"screen_inches": "43", "maximum_power_w": "130"},
        note="130 W é o consumo máximo publicado deste modelo, não o consumo típico de qualquer TV de 43″.",
    ),
    reference(
        "lg-ac-12000-s3w12ja33b",
        "Ar-condicionado 12.000 BTU/h · LG",
        "Climatização",
        "air_conditioner",
        "1130",
        "https://www.lg.com/br/ar-condicionado-residencial/dual-inverter-split/s3-w12ja33b/",
        "Especificações gerais: entrada elétrica nominal em resfriamento",
        brand="LG",
        model="S3-W12JA33B / S3UW12JA33B",
        voltage="220",
        technology="Dual Inverter",
        parameters={
            "ac_type": "split",
            "compressor": "inverter",
            "cooling_capacity_btu_h": "12000",
        },
        note="1.130 W em refrigeração nominal; aquecimento 1.030 W. Não é potência máxima nem capacidade térmica.",
    ),
    reference(
        "mondial-airfryer-afn40bi",
        "Air fryer · Mondial AFN-40-BI",
        "Cozinha",
        "appliance",
        "1500",
        "https://www.mondial.com.br/fritadeira-sem-oleo-air-fryer-4-litros-afn-40-bi-mondial/p",
        "Informações técnicas AFN-40-BI",
        brand="Mondial",
        model="AFN-40-BI",
        voltage_range="Variantes 127 V ou 220 V; não bivolt",
    ),
    reference(
        "mondial-liquidificador-l99fb",
        "Liquidificador · Mondial L-99-FB",
        "Cozinha",
        "appliance",
        "550",
        "https://www.mondial.com.br/liquidificador-mondial-turbo-power-l-99-fb/p",
        "Página oficial Turbo Power L-99-FB",
        brand="Mondial",
        model="L-99-FB",
    ),
    reference(
        "mondial-ventilador-vsp40w",
        "Ventilador · Mondial VSP-40-W",
        "Climatização",
        "appliance",
        "140",
        "https://www.mondial.com.br/ventilador-de-mesa-mondial-6-pas-vsp-40-w/p",
        "Página oficial Super Power VSP-40-W: informações técnicas, potência 140 W",
        brand="Mondial",
        model="VSP-40-W",
    ),
    reference(
        "mondial-cafeteira-c34ji15x",
        "Cafeteira · Mondial C-34-JI-15X",
        "Cozinha",
        "appliance",
        "550",
        "https://paginadeproduto.emondial.com/HTML-C-34-JI-15X/index.html",
        "Informações técnicas C-34-JI-15X",
        brand="Mondial",
        model="C-34-JI-15X",
        voltage_range="Variantes 127 V ou 220 V; não bivolt",
    ),
    reference(
        "mondial-cooktop-cti03",
        "Cooktop indução 4 bocas · Mondial",
        "Cozinha",
        "appliance",
        "7000",
        "https://www.mondial.com.br/cooktop-por-inducao-4-bocas-mondial-preto-7000w-220v-cti-03/p",
        "Potência total CTI-03; não somar potências turbo das zonas",
        brand="Mondial",
        model="CTI-03",
        voltage="220",
        technology="Indução",
    ),
    reference(
        "midea-microondas-mra22",
        "Micro-ondas · Midea MRA_22 20 L",
        "Cozinha",
        "microwave",
        "1050",
        "https://www.midea.com/br/wp-content/uploads/2021/03/MRA_USER-MANUAL-2020-09_Rev.04_view.pdf",
        "Manual MRA Rev.04: nominal 1050 W / saída 700 W",
        brand="Midea",
        model="MRA_22 (família do manual)",
        voltage="220",
        parameters={"microwave_output_w": "700"},
    ),
    reference(
        "electrolux-lavaloucas-le08s220",
        "Lava-louças · Electrolux LE08S 220 V",
        "Cozinha",
        "appliance",
        "1400",
        "https://api.electrolux-medialibrary.com/asset/4a931378-e358-4c4f-ab38-88d1c66822cd/E4RM3Q/4eb5e9ec-fde6-4e9b-9ded-be5bf762843c/PDF/4eb5e9ec-fde6-4e9b-9ded-be5bf762843c.pdf",
        "Ficha LE08S: especificações técnicas",
        brand="Electrolux",
        model="LE08S",
        voltage="220",
        parameters={"nameplate_current_a": "6.36"},
    ),
]
next(item for item in CATALOG if item["id"] == "mondial-ventilador-vsp40w")["verified_on"] = (
    "2026-10-22"
)
CATALOG.append(
    reference(
        "lg-ac-9000-s3q09aa33a",
        "Ar-condicionado 9.000 BTU/h · LG",
        "Climatização",
        "air_conditioner",
        "800",
        "https://www.lg.com/br/ar-condicionado-residencial/dual-inverter-split/s3-q09aa33a/",
        "Especificações gerais: entrada elétrica nominal de resfriamento 800 W; capacidade 9000 BTU/h",
        brand="LG",
        model="S3-Q09AA33A / S3NQ09AA33A + S3UQ09AA33A",
        voltage="220",
        technology="Dual Inverter",
        parameters={"ac_type": "split", "compressor": "inverter", "cooling_capacity_btu_h": "9000"},
        note="800 W é entrada elétrica nominal deste conjunto em refrigeração; 150 W é o mínimo publicado. Não representa todo aparelho de 9000 BTU/h.",
    )
)
for voltage, power in (("127", "5500"), ("220", "6400"), ("220", "7500")):
    CATALOG.append(
        reference(
            f"lorenzetti-advanced-{voltage}-{power}",
            f"Chuveiro Advanced · {power} W / {voltage} V",
            "Aquecimento de água",
            "shower",
            power,
            "https://www.lorenzetti.com.br/produto/advanced-multitemperaturas/",
            "Advanced Multitemperaturas: tabela potência/tensão",
            brand="Lorenzetti",
            model="Advanced Multitemperaturas",
            voltage=voltage,
            rating="maximum",
            note="Potência máxima da variante multitemperaturas. Corrente exige configuração e FP ou hipótese resistiva explícita.",
        )
    )
for id, name, model, power, url in (
    (
        "loren-easy-220",
        "Torneira elétrica · Loren Easy 220 V",
        "Loren Easy para parede",
        "5500",
        "https://www.lorenzetti.com.br/produto/loren-easy-parede",
    ),
    (
        "versatil-220",
        "Aquecedor de água · Versátil 220 V",
        "Aquecedor Versátil",
        "5500",
        "https://www.lorenzetti.com.br/produto/aquecedor-versatil",
    ),
):
    CATALOG.append(
        reference(
            id,
            name,
            "Aquecimento de água",
            "appliance",
            power,
            url,
            "Tabela de potência/tensão do produto",
            brand="Lorenzetti",
            model=model,
            voltage="220",
        )
    )

# Exact listed kW values converted to W. Motor rows labelled cv are excluded:
# they do not document electrical input or motor efficiency.
for id, name, category, type_, power, row, technology in (
    (
        "incandescent",
        "Incandescente · referência 60 W",
        "Iluminação",
        "lighting",
        "60",
        "Incandescente 60 W: 0,06 kW",
        "Incandescente",
    ),
    (
        "fluorescent",
        "Fluorescente · referência 60 W",
        "Iluminação",
        "lighting",
        "60",
        "Fluorescente de 60 W: 0,06 kW",
        "Fluorescente",
    ),
    (
        "halogen",
        "Halógena · referência 20 W",
        "Iluminação",
        "lighting",
        "20",
        "Halógena 20 W: 0,02 kW",
        "Halógena",
    ),
    (
        "fridge",
        "Geladeira 2 portas · referência genérica",
        "Cozinha",
        "refrigeration",
        "130",
        "Geladeira 2 portas: 0,13 kW",
        "",
    ),
    (
        "freezer",
        "Freezer · referência genérica",
        "Cozinha",
        "refrigeration",
        "260",
        "Freezer: 0,26 kW",
        "",
    ),
    (
        "heater",
        "Aquecedor de ambiente · referência genérica",
        "Climatização",
        "appliance",
        "1550",
        "Aquecedor de ambiente: 1,55 kW",
        "",
    ),
    (
        "oven",
        "Forno elétrico · referência genérica",
        "Cozinha",
        "appliance",
        "2000",
        "Forno elétrico: 2,00 kW",
        "",
    ),
    (
        "washer",
        "Máquina de lavar sem aquecedor · referência",
        "Lavanderia",
        "appliance",
        "600",
        "Lavadora sem aquecedor: 0,60 kW",
        "",
    ),
    (
        "dryer",
        "Secadora · referência genérica",
        "Lavanderia",
        "appliance",
        "2000",
        "Secadora de roupa: 2,00 kW",
        "",
    ),
    (
        "computer",
        "Computador CPU · referência sem monitor",
        "Outros",
        "appliance",
        "300",
        "Microcomputador CPU: 0,30 kW",
        "",
    ),
    (
        "gate",
        "Motor de portão · referência genérica",
        "Outros",
        "motor",
        "370",
        "Portão eletrônico: 0,37 kW",
        "",
    ),
):
    CATALOG.append(
        reference(
            f"enel-{id}",
            name,
            category,
            type_,
            power,
            ENEL,
            row,
            technology=technology,
            rating="estimated",
            note="Estimativa da tabela pública Enel, sem modelo, tensão ou FP verificados. Não é critério normativo Energisa. Substitua pela placa quando disponível.",
        )
    )
CATALOG.append(
    CatalogItem(
        id="pump-custom",
        name="Bomba · dados de placa / potência mecânica",
        category="Outros",
        kind="specific_use",
        equipment_type="motor",
        note="Entrada elétrica desconhecida. Informe W de entrada ou cv/HP e rendimento do motor. Não usar rendimento hidráulico da bomba.",
    ).model_dump(mode="json")
)
CATALOG.append(
    CatalogItem(
        id="custom",
        name="Equipamento personalizado",
        category="Outros",
        kind="specific_use",
        equipment_type="custom",
        note="Sem referência: informe potência elétrica de entrada, sem confundir W com kWh.",
    ).model_dump(mode="json")
)

# Selection labels are separate from source/model identities. No ratings change.
CATALOG.append(
    CatalogItem(
        id="motor-custom",
        name="Motor elétrico",
        category="Outros",
        kind="specific_use",
        equipment_type="motor",
        note="Informe entrada elétrica em W ou saída mecânica em cv/HP com rendimento do motor.",
    ).model_dump(mode="json")
)
SELECTION_NAMES = {
    "philips-led-929001195311": "Lâmpada LED",
    "samsung-tv43-au7700": "Televisor",
    "lg-ac-12000-s3w12ja33b": "Ar-condicionado",
    "lg-ac-9000-s3q09aa33a": "Ar-condicionado",
    "mondial-airfryer-afn40bi": "Air fryer",
    "mondial-liquidificador-l99fb": "Liquidificador",
    "mondial-ventilador-vsp40w": "Ventilador",
    "mondial-cafeteira-c34ji15x": "Cafeteira",
    "mondial-cooktop-cti03": "Cooktop elétrico",
    "midea-microondas-mra22": "Micro-ondas",
    "electrolux-lavaloucas-le08s220": "Lava-louças",
    "loren-easy-220": "Torneira elétrica",
    "versatil-220": "Aquecedor de água",
    "enel-incandescent": "Lâmpada incandescente",
    "enel-fluorescent": "Lâmpada fluorescente",
    "enel-halogen": "Lâmpada halógena",
    "enel-fridge": "Geladeira",
    "enel-freezer": "Freezer",
    "enel-heater": "Aquecedor de ambiente",
    "enel-oven": "Forno elétrico",
    "enel-washer": "Máquina de lavar",
    "enel-dryer": "Secadora",
    "enel-computer": "Computador",
    "enel-gate": "Motor de portão",
    "pump-custom": "Bomba de água",
    "motor-custom": "Motor elétrico",
    "custom": "Outros equipamentos",
}
for item in CATALOG:
    if item["equipment_type"] == "shower":
        item["selection_name"] = "Chuveiro elétrico"
        item["selection_default"] = item["id"] == "lorenzetti-advanced-220-7500"
    else:
        item["selection_name"] = SELECTION_NAMES[item["id"]]

# Keep the existing 12000 BTU/h default; capacity matching selects the 9000 reference.
next(item for item in CATALOG if item["id"] == "lg-ac-9000-s3q09aa33a")["selection_default"] = False

# Published electrical input, not thermal W or seasonal kWh/year.
MIDEA_AC_SOURCE = "https://www.midea.com/content/dam/midea-aem/br/climatizacao/hiwall/ar-condicionado-split-springer-midea-xtreme-save-connect-c-9-000-btu-h-quente-frio/Manual%20do%20Usu%C3%A1rio_Xtreme%20Save%20Connect%20C.PDF"
for capacity, suffix, watts in [
    ("18000", "18", "1583"),
    ("24000", "24", "2170"),
    ("30000", "30", "2430"),
]:
    item = reference(
        f"midea-ac-{capacity}-xtreme-c",
        f"Ar-condicionado {capacity} BTU/h · Springer Midea",
        "Climatização",
        "air_conditioner",
        watts,
        MIDEA_AC_SOURCE,
        "Xtreme Save Connect C, setembro/2022, p. 2: dados técnicos, ciclo Frio, potência nominal de refrigeração",
        brand="Springer Midea",
        model=f"42AGVCC{suffix}M5 / 38AGVCC{suffix}M5",
        voltage="220",
        technology="Inverter",
        parameters={
            "ac_type": "split",
            "compressor": "inverter",
            "cooling_capacity_btu_h": capacity,
        },
        note="Entrada elétrica nominal em refrigeração deste conjunto documentado; sugestão de categoria, não valor universal. FP e corrente não publicados nesta ficha permanecem desconhecidos.",
    )
    item.update(verified_on="2026-10-22", selection_name="Ar-condicionado", selection_default=False)
    CATALOG.append(item)

# Generic values explicitly listed in the public utility equipment table.
for identifier, label, category, watts, row in [
    (
        "enel-hairdryer-small",
        "Secador de cabelos pequeno",
        "Higiene",
        "600",
        "SECADOR DE CABELOS PEQUENO: 0,60 kW",
    ),
    ("enel-wall-exhaust", "Exaustor de parede", "Ventilação", "110", "EXAUSTOR PAREDE: 0,11 kW"),
    (
        "enel-phone-charger",
        "Carregador de celular",
        "Eletrônicos",
        "50",
        "CARREGADOR DE CELULAR: 0,05 kW",
    ),
    ("enel-audio", "Aparelho de som", "Eletrônicos", "120", "APARELHO DE SOM: 0,12 kW"),
]:
    item = reference(
        identifier,
        label,
        category,
        "appliance",
        watts,
        ENEL,
        row,
        rating="estimated",
        note="Estimativa da categoria publicada pela Enel, não potência de placa universal nem fator normativo de demanda. Tensão e FP desconhecidos; substitua pela etiqueta do seu aparelho.",
    )
    item.update(verified_on="2026-10-22", selection_name=label)
    if identifier != "enel-wall-exhaust":
        item["kind"] = "general_use"
    CATALOG.append(item)

# Recommendations affect selection only, not permitted installations or math.

for item in CATALOG:
    item["recommended_environments"] = recommended_rooms(item)
