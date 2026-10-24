from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

Nonnegative = Annotated[Decimal, Field(ge=0, allow_inf_nan=False, max_digits=18, decimal_places=6)]
Positive = Annotated[Decimal, Field(gt=0, allow_inf_nan=False, max_digits=18, decimal_places=6)]
Text = Annotated[str, Field(min_length=1, max_length=200)]
Status = Literal[
    "calculated", "estimated", "pending", "invalid", "out_of_scope", "awaiting_technical_validation"
]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


EquipmentType = Literal[
    "lighting",
    "air_conditioner",
    "shower",
    "refrigeration",
    "motor",
    "microwave",
    "television",
    "appliance",
    "custom",
]
Ratio = Annotated[Decimal, Field(gt=0, le=1, allow_inf_nan=False, max_digits=7, decimal_places=6)]


class TechnicalParameters(Schema):
    power_mode: Literal["electrical", "mechanical"] = "electrical"
    cooling_capacity_btu_h: Positive | None = None
    ac_type: Literal["split", "window", "portable", "other"] | None = None
    compressor: Literal["inverter", "conventional", "unknown"] = "unknown"
    screen_inches: Positive | None = None
    monthly_energy_kwh: Nonnegative | None = None
    usage_hours_per_day: (
        Annotated[Decimal, Field(ge=0, le=24, allow_inf_nan=False, max_digits=8, decimal_places=6)]
        | None
    ) = None
    usage_days_per_month: int | None = Field(default=None, ge=0, le=31, strict=True)
    maximum_power_w: Nonnegative | None = None
    microwave_output_w: Nonnegative | None = None
    mechanical_power: Nonnegative | None = None
    mechanical_unit: Literal["cv", "hp"] = "cv"
    efficiency: Ratio | None = None
    configuration: Literal["unknown", "single_phase", "balanced_three_phase"] = "unknown"
    assume_resistive: bool = False
    nameplate_current_a: Nonnegative | None = None
    starting_current_a: Nonnegative | None = None
    maximum_current_a: Nonnegative | None = None


class CatalogItem(Schema):
    recommended_environments: list[str] = Field(default_factory=list)
    id: str
    name: str
    selection_name: str | None = None
    selection_default: bool = True
    category: str
    kind: Literal["lighting", "general_use", "specific_use"]
    equipment_type: EquipmentType
    technology: str = ""
    brand: str | None = None
    model: str | None = None
    reference_power_w: Nonnegative | None = None
    unit: Literal["W"] = "W"
    voltage_v: Positive | None = None
    voltage_range: str | None = None
    power_factor: Ratio | None = None
    power_rating: Literal["nominal", "maximum", "estimated", "unknown"] = "unknown"
    source: str | None = None
    source_url: str | None = None
    document: str | None = None
    verified_on: str | None = None
    status: Literal["verified", "pending"] = "pending"
    note: str
    parameters: TechnicalParameters = Field(default_factory=TechnicalParameters)


EnergisaGroup = Literal["d1", "d2", "d3", "d4", "d5", "d6", "d7"]


class EnergisaLoadClassification(Schema):
    group: EnergisaGroup | None = None
    reserve: bool = Field(default=False, strict=True)
    air_conditioning_type: Literal["unconfirmed", "window_or_individual", "central_unit"] = (
        "unconfirmed"
    )


class ProjectEnergisaDemandSettings(Schema):
    enabled: bool = Field(default=False, strict=True)
    unit_type: Literal["unconfirmed", "individual_residential", "grouped", "non_residential"] = (
        "unconfirmed"
    )
    has_signage_or_display_lighting: bool | None = Field(default=None, strict=True)
    simultaneous_lighting_outlets: bool | None = Field(default=None, strict=True)
    confirmed_absent_groups: list[EnergisaGroup] = Field(default_factory=list, max_length=7)
    reviewed_inventory_digest: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")


class Load(Schema):
    energisa_demand: EnergisaLoadClassification | None = None
    id: UUID = Field(default_factory=uuid4)
    name: Text
    category: Text = "Outros"
    technology: str = Field(default="", max_length=100)
    kind: Literal["lighting", "general_use", "specific_use"] = "specific_use"
    quantity: int = Field(default=1, ge=1, le=100000, strict=True)
    unit_power_w: Nonnegative | None = None
    voltage_v: Positive | None = None
    power_factor: Ratio | None = None
    power_origin: Literal["nameplate", "manufacturer", "user_estimate"] = "user_estimate"
    source: str = Field(default="Informado pelo usuário", min_length=1, max_length=1000)
    demand_classification: str | None = Field(default=None, max_length=100)

    equipment_type: EquipmentType = "custom"
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=200)
    parameters: TechnicalParameters = Field(default_factory=TechnicalParameters)
    catalog_reference: CatalogItem | None = None
    manual_override: bool = False
    power_user_edited: bool = False

    @model_validator(mode="after")
    def validate_technical_mode(self):
        if self.equipment_type == "lighting":
            if "kind" not in self.model_fields_set:
                self.kind = "lighting"
            elif self.kind != "lighting":
                raise ValueError("Equipamentos de iluminação devem ter natureza iluminação")
        if self.parameters.power_mode == "mechanical" and self.equipment_type != "motor":
            raise ValueError("Potência mecânica só é aplicável a motores e bombas")
        if self.parameters.assume_resistive and self.power_factor not in (None, Decimal(1)):
            raise ValueError(
                "Hipótese resistiva com FP=1 conflita com o fator de potência informado"
            )
        if self.catalog_reference is not None:
            ref = self.catalog_reference
            self.manual_override = any(
                (
                    self.equipment_type != ref.equipment_type,
                    self.kind != ref.kind,
                    self.category != ref.category,
                    self.unit_power_w != ref.reference_power_w,
                    self.voltage_v != ref.voltage_v,
                    self.power_factor != ref.power_factor,
                    self.technology != ref.technology,
                    self.parameters != ref.parameters,
                    self.model != (ref.model or ""),
                    self.brand != (ref.brand or ""),
                )
            )
        return self


class Environment(Schema):
    id: UUID = Field(default_factory=uuid4)
    name: Text
    type: Literal[
        "living",
        "bedroom",
        "kitchen",
        "bathroom",
        "laundry",
        "garage",
        "corridor",
        "outdoor",
        "office",
        "other",
    ] = "other"
    area_m2: Positive | None = None
    perimeter_m: Positive | None = None
    lighting_points: int = Field(default=0, ge=0, strict=True)
    outlets: int = Field(default=0, ge=0, strict=True)
    loads: list[Load] = Field(default_factory=list, max_length=1000)


class CircuitProtectionInput(Schema):
    source: Text | None = None
    device_rated_a: Positive | None = None
    cable_k: Positive | None = None
    let_through_a2s: Nonnegative | None = None
    short_duration_s: Positive | None = None
    earthing_system: Literal["unknown", "TN", "TT"] = "unknown"
    phase_earth_voltage_v: Positive | None = None
    tn_situation: Literal[1, 2] | None = None
    fault_loop_ohm: Positive | None = None
    trip_current_a: Positive | None = None
    trip_time_s: Positive | None = None
    tt_ra_ohm: Positive | None = None
    touch_limit_v: Literal[12, 25, 50] | None = None
    rcd_sensitivity_ma: Positive | None = None
    rcd_type_compatible_confirmed: bool = Field(default=False, strict=True)
    rcd_additional_required: bool | None = Field(default=None, strict=True)


class CircuitInput(Schema):
    protections: CircuitProtectionInput | None = None
    id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=200)
    name: Text = "Novo circuito"
    purpose: Literal["lighting", "sockets", "dedicated"] = "sockets"
    load_ids: list[str] = Field(default_factory=list, max_length=1000)
    method: Literal["unknown", "B1", "B2"] = "unknown"
    voltage_v: Positive | None = None
    length_m: Positive | None = None
    ambient_temperature_c: Literal[10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60] | None = None
    grouped_circuits: int | None = Field(default=None, ge=1, le=8, strict=True)
    scope_confirmed: bool = Field(default=False, strict=True)
    voltage_drop_model_confirmed: bool = Field(default=False, strict=True)
    overload_duration_confirmed: bool = Field(default=False, strict=True)
    breaker_ratings_a: list[Positive] = Field(default_factory=list, max_length=50)
    breaker_i2_factor: Annotated[Decimal, Field(ge=1, le=10, allow_inf_nan=False)] | None = None
    breaker_source: Text | None = None
    prospective_short_circuit_ka: Positive | None = None
    breaking_capacity_ka: Positive | None = None
    supply_origin: Literal[
        "unknown", "public_lv_delivery", "own_transformer", "delivery_at_transformer", "generator"
    ] = "unknown"
    upstream_drop_percent: Nonnegative | None = None

    @model_validator(mode="after")
    def distinct_loads(self):
        if len(set(self.load_ids)) != len(self.load_ids):
            raise ValueError("Carga duplicada no mesmo circuito")
        return self


class ServiceEntryInput(Schema):
    network: Literal["unknown", "220_127"] = "unknown"
    route: Literal["unknown", "embedded", "underground"] = "unknown"
    insulation: Literal["unknown", "PVC70", "XLPE90"] = "unknown"
    requested_phases: Literal[1, 2, 3] | None = None
    scope_confirmed: bool = Field(default=False, strict=True)
    special_loads_reviewed: bool = Field(default=False, strict=True)


class ProjectInput(Schema):
    service_entry: ServiceEntryInput | None = None
    circuits: list[CircuitInput] = Field(default_factory=list, max_length=200)
    energisa_demand: ProjectEnergisaDemandSettings | None = None
    analysis_scope: Literal["installed", "apparent", "current", "normative"] = "installed"
    name: Text
    municipality: Text
    state: Literal[
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    ] = "SP"
    utility: Literal[
        "energisa_sul_sudeste",
        "cpfl_paulista",
        "cpfl_piratininga",
        "cpfl_santa_cruz",
        "neoenergia_elektro",
        "enel_sp",
        "edp_sp",
        "unconfirmed",
    ] = "unconfirmed"
    residence_type: Text | None = "Casa"
    built_area_m2: Positive | None = None
    floors: int | None = Field(default=1, ge=1, le=100, strict=True)
    reference_voltage_v: Positive | None = Decimal(220)
    energy_tariff_brl_per_kwh: Nonnegative | None = None
    notes: str = Field(default="", max_length=10000)
    environments: list[Environment] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def unique_ids(self):
        rooms = [room.id for room in self.environments]
        loads = [load.id for room in self.environments for load in room.loads]
        if len(set(rooms)) != len(rooms) or len(set(loads)) != len(loads):
            raise ValueError("Identificadores duplicados de ambientes ou cargas")
        circuits = [c.id for c in self.circuits]
        if len(circuits) != len(set(circuits)):
            raise ValueError("Identificadores duplicados de circuitos")
        return self


class CalculationInput(ProjectInput):
    # Project metadata does not block an unsaved electrical study.
    name: str = Field(default="", max_length=200)
    municipality: str = Field(default="", max_length=200)
    built_area_m2: Positive | None = None


class Project(ProjectInput):
    deleted_at: datetime | None = None
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    standards_version: str


class ProjectSummary(Schema):
    id: UUID
    name: str
    municipality: str
    state: str
    utility: str
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    standards_version: str


class Value(Schema):
    value: Decimal
    unit: Literal["W", "kW", "VA", "kVA", "A", "kWh", "BRL"]
    status: Status


class MemoryInputs(Schema):
    quantity: int
    unit_power_w: Decimal


class MemoryResult(Schema):
    value: Decimal
    unit: Literal["W"]


class Memory(Schema):
    rule_id: str = "installed_power"
    rule_version: str = "0.3.0"
    power_origin: str | None = None
    manual_override: bool = False
    catalog_reference: CatalogItem | None = None
    calculation: Literal["installed_power"]
    load_id: UUID
    environment_id: UUID
    name: str
    inputs: MemoryInputs
    formula: str
    result: MemoryResult
    status: Status
    reference: str | None
    source: str


class TechnicalStep(Schema):
    calculation: str
    formula: str
    substituted: str
    value: Decimal
    unit: Literal["W", "kW", "VA", "kVA", "A", "kWh", "BRL"]
    source: str | None = None
    assumptions: str


class LoadTechnicalResult(Schema):
    load_id: UUID
    name: str
    electrical_input_w: Decimal | None
    thermal_capacity_w: Decimal | None
    apparent_power_va: Decimal | None
    monthly_energy_kwh: Decimal | None = None
    monthly_cost_brl: Decimal | None = None
    energy_basis: Literal["stated", "schedule", "pending"] = "pending"
    unit_current_a: Decimal | None
    status: Status
    steps: list[TechnicalStep]
    warnings: list[str]


class ResearchEvidence(Schema):
    title: str
    url: str
    finding: str
    access: Literal[
        "official_metadata",
        "official_index",
        "institutional_full_text",
        "official_full_text",
        "user_supplied_full_text",
    ]
    consulted_on: str
    section: str | None = None
    file_name: str | None = None
    sha256: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")


class EnergisaDemandLoad(Schema):
    name: Text
    group: EnergisaGroup = Field(
        description="Classificação explícita §9.1: d1 iluminação/TUG; d2 aquecimento de água; d3 secadora de roupas/micro-ondas/lava-louças/hidromassagem; d4 fogão/forno elétrico; d5 AC janela/individual; d6 motores; d7 solda transformador/raios-X. Sem classificação automática."
    )
    quantity: int = Field(ge=1, le=100000, strict=True)
    unit_power_w: Nonnegative | None = Field(
        description="Potência elétrica por unidade, em W, adotada pelo responsável. Não informar VA normativo, potência térmica ou kWh. Valores manuais válidos prevalecem sobre referências."
    )
    reserve: bool = Field(default=False, strict=True)
    air_conditioning_type: Literal["unconfirmed", "window_or_individual", "central_unit"] = (
        "unconfirmed"
    )


class EnergisaDemandInput(Schema):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                dict(
                    utility="energisa_sul_sudeste",
                    state="SP",
                    unit_type="individual_residential",
                    inventory_reviewed=True,
                    has_signage_or_display_lighting=False,
                    simultaneous_lighting_outlets=False,
                    loads=[
                        dict(
                            name="Iluminação/TUG — exemplo fictício",
                            group="d1",
                            quantity=1,
                            unit_power_w="1000",
                        ),
                        dict(
                            name="Chuveiro — exemplo manual",
                            group="d2",
                            quantity=1,
                            unit_power_w="5500",
                        ),
                    ],
                    confirmed_absent_groups=["d3", "d4", "d5", "d6", "d7"],
                )
            ]
        }
    )
    utility: str = Field(min_length=1, max_length=100)
    state: str = Field(pattern="^[A-Z]{2}$")
    unit_type: Literal["individual_residential", "grouped", "non_residential"]
    inventory_reviewed: bool = Field(
        strict=True,
        description="Confirma inventário completo, classificação de cada carga uma única vez, quantidades, potências adotadas e identificação das reservas (§9.1 notaVI).",
    )
    has_signage_or_display_lighting: bool = Field(
        strict=True,
        description="Letreiros/iluminação de vitrines não são abrangidos pela Tabela5; presença deixa este método fora de escopo.",
    )
    simultaneous_lighting_outlets: bool | None = Field(default=None, strict=True)
    loads: list[EnergisaDemandLoad] = Field(max_length=1000)
    confirmed_absent_groups: list[EnergisaGroup] = Field(max_length=7)

    @model_validator(mode="after")
    def consistent_groups(self):
        absent = self.confirmed_absent_groups
        if len(absent) != len(set(absent)):
            raise ValueError("Grupos ausentes duplicados.")
        if set(absent) & {load.group for load in self.loads if not load.reserve}:
            raise ValueError("Grupo declarado ausente contém cargas em operação.")
        return self


class EnergisaDemandBand(Schema):
    installed_band_w: Decimal
    factor: Decimal
    demand_w: Decimal


class EnergisaDemandGroupResult(Schema):
    group: EnergisaGroup
    quantity: int
    installed_power_w: Decimal | None
    factor: Decimal | None
    demand_w: Decimal | None
    table: str
    reason: str | None
    bands: list[EnergisaDemandBand] = Field(default_factory=list)


class EnergisaDemandResult(Schema):
    value: Decimal | None
    unit: Literal["kVA"]
    status: Status
    installed_power_w: Decimal | None
    demanded_power_kw: Decimal | None
    groups: list[EnergisaDemandGroupResult]
    pending_checks: list[str]
    ignored_reserve_loads: list[str]
    limitations: list[str]
    reference: ResearchEvidence


class ProjectEnergisaDemandInventoryItem(Schema):
    load_id: str
    environment_id: str
    environment: str
    name: str
    group: EnergisaGroup | None
    quantity: int
    unit_power_w: Nonnegative | None
    reserve: bool
    air_conditioning_type: Literal["unconfirmed", "window_or_individual", "central_unit"]


class ProjectEnergisaDemandResult(EnergisaDemandResult):
    declarations: ProjectEnergisaDemandSettings
    inventory_digest: str
    inventory_reviewed: bool
    unclassified_load_ids: list[str]
    inventory: list[ProjectEnergisaDemandInventoryItem]


class NormativeCapability(Schema):
    code: Literal["lighting", "outlets", "demand"]
    label: str
    purpose: str
    available: bool
    status: Status
    reason: str
    evidence: list[ResearchEvidence]
    pending_checks: list[str]


class RegionalMethodInfo(Schema):
    code: str
    endpoint: str
    status: Status
    available: bool
    scope: str
    supported_utilities: list[str]
    supported_states: list[str]
    reference: ResearchEvidence


class TechnicalRules(Schema):
    regional_methods: list[RegionalMethodInfo] = Field(default_factory=list)
    registry_version: str
    mathematical: list[dict]
    normative: list[dict]
    coverage: list[NormativeCapability]
    notice: str


class NormativeEnvironment(Schema):
    environment_id: str
    name: str
    status: Status
    lighting_va: Decimal | None
    minimum_lighting_points: int | None
    registered_lighting_points: int
    lighting_points_missing: int | None
    minimum_outlet_points: int | None
    registered_outlet_points: int
    outlet_points_missing: int | None
    outlet_basis_points: int | None
    outlets_va: Decimal | None
    missing_fields: list[Literal["area_m2", "perimeter_m"]]
    notes: list[str]
    reason: str


class CircuitProtectionCheck(Schema):
    code: str
    label: str
    value: Decimal | None
    passed: bool | None
    reason: str


class CircuitResult(Schema):
    protection_checks: list[CircuitProtectionCheck] = Field(default_factory=list)
    circuit_id: str
    name: str
    status: Status
    design_current_a: Decimal | None
    power_factor: Decimal | None
    breaker_a: Decimal | None
    conventional_current_a: Decimal | None
    phase_section_mm2: Decimal | None
    pe_section_mm2: Decimal | None
    capacity_a: Decimal | None
    temperature_factor: Decimal | None
    grouping_factor: Decimal | None
    voltage_drop_v: Decimal | None
    voltage_drop_percent: Decimal | None
    total_drop_percent: Decimal | None
    breaking_capacity_ok: bool | None
    pending_checks: list[str]
    reference: str
    reference_urls: list[str] = Field(default_factory=list)
    limitations: list[str]


class ServiceEntryResult(Schema):
    status: Status
    category: str | None
    phases: int | None
    basis_value: Decimal | None
    basis_unit: str | None
    minimum_phase_mm2: Decimal | None
    minimum_neutral_mm2: Decimal | None
    minimum_earthing_mm2: Decimal | None
    band_breaker_references_a: list[Decimal]
    pending_checks: list[str]
    reference: str


class CalculationResult(Schema):
    service_entry: ServiceEntryResult | None = None
    circuit_results: list[CircuitResult] = Field(default_factory=list)
    energisa_demand: ProjectEnergisaDemandResult | None = None
    normative_environments: list[NormativeEnvironment] = Field(default_factory=list)
    normative_capabilities: list[NormativeCapability] = Field(default_factory=list)
    notifications: list["Notification"] = Field(default_factory=list)
    field_issues: list["FieldIssue"] = Field(default_factory=list)
    technical_context: dict = Field(default_factory=dict)
    input_digest: str
    engine_version: str
    status: Status
    installed_power: Value
    installed_power_kw: Value
    lighting_nominal: Value
    by_environment_w: dict[str, Decimal]
    by_category_w: dict[str, Decimal]
    apparent_power: Value | None
    normative: dict[str, dict]
    memory: list[Memory]
    warnings: list[str]
    counting_policy: str
    unknown_load_ids: list[str] = Field(default_factory=list)
    load_results: list[LoadTechnicalResult] = Field(default_factory=list)
    apparent_power_kva: Value | None = None
    aggregate_steps: list[TechnicalStep] = Field(default_factory=list)
    monthly_energy: Value | None = None
    monthly_cost: Value | None = None
    energy_unknown_load_ids: list[str] = Field(default_factory=list)
    energy_by_environment_kwh: dict[str, Decimal] = Field(default_factory=dict)
    energy_by_category_kwh: dict[str, Decimal] = Field(default_factory=dict)


class ProjectRevalidation(Schema):
    project_id: UUID
    project_version: int
    previous_registry_version: str
    current_registry_version: str
    previous_engine_version: str | None
    requires_revalidation: bool
    # Historical snapshots keep their original schema and must remain readable.
    previous_result: dict | None
    current_result: CalculationResult
    notice: str


class AccessSession(Schema):
    mode: Literal["local", "remote"]
    authenticated: bool
    username: str | None
    csrf: str | None


class UtilityInfo(Schema):
    id: str
    name: str
    states: list[str]
    document_ids: list[str]
    status: Status
    municipality_mapping: Literal["unverified"]


class TechnicalDocument(Schema):
    id: str
    title: str
    edition: str | None
    effective_date: str | None
    source: str
    status: str
    consulted_on: str
    source_file: str | None = None
    sha256: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")


class DocumentRegistry(Schema):
    registry_version: str
    documents: list[TechnicalDocument]


class FieldRequirement(Schema):
    required_for: list[str] = Field(
        default_factory=lambda: ["installed", "apparent", "current", "normative"]
    )
    max_length: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    integer: bool = False
    label: str
    purpose: str
    when: dict[str, str | bool] | None


class FieldIssue(Schema):
    target_id: str = ""
    location: list[str] = Field(default_factory=list)
    solution: str = ""
    affected_results: list[str] = Field(default_factory=list)
    path: str
    field: str
    label: str
    purpose: str
    status: Literal["pending", "invalid"]
    message: str


class PDFExportInput(Schema):
    saved_project_id: UUID | None = None
    saved_project_version: int | None = Field(default=None, ge=1)
    project: CalculationInput
    expected_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_registry_version: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_engine_version: str = Field(min_length=1, max_length=50)


class Notification(Schema):
    id: str
    category: Literal["error", "technical", "normative", "info", "estimate"]
    location: list[str]
    problem: str
    solution: str
    affected_results: list[str]
    target_id: str | None = None


class HealthInfo(Schema):
    status: str
    app_version: str
    api_version: str
    engine_version: str


class InputValidationError(Schema):
    detail: str | list[dict]
    notifications: list[Notification] = Field(default_factory=list)
