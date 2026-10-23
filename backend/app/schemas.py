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


class Load(Schema):
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


class ProjectInput(Schema):
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
        "official_metadata", "official_index", "institutional_full_text", "official_full_text"
    ]
    consulted_on: str
    section: str | None = None


class NormativeCapability(Schema):
    code: Literal["lighting", "outlets", "demand"]
    label: str
    purpose: str
    available: bool
    status: Status
    reason: str
    evidence: list[ResearchEvidence]
    pending_checks: list[str]


class TechnicalRules(Schema):
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


class CalculationResult(Schema):
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
