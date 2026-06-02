from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ProjectIntake(BaseModel):
    project_name: str = Field(default="Guinche de izaje — Cotización técnica premium")
    client_name: str = Field(default="Cliente industrial")
    location_city: str = Field(default="Zaruma")
    location_province: str = Field(default="El Oro")
    country: str = Field(default="Ecuador")
    application: str = Field(default="Guinche / winche de izaje")
    motor_power_hp: float = Field(default=25.0, ge=0.1, description="Potencia nominal del motor en HP")
    voltage: float = Field(default=460.0, ge=1)
    phases: int = Field(default=3, ge=1, le=3)
    frequency_hz: float = Field(default=60.0, ge=1)
    full_load_amps: Optional[float] = Field(default=30.4, ge=0)
    efficiency: float = Field(default=0.936, gt=0, le=1)
    power_factor: float = Field(default=0.86, gt=0, le=1)
    service_factor: float = Field(default=1.15, ge=1.0)
    rpm: Optional[int] = Field(default=1765, ge=0)
    enclosure: str = Field(default="TEFC")
    load_type: str = Field(default="Izaje / guinche")
    duty_cycle: str = Field(default="Intermitente")
    starts_per_hour: int = Field(default=30, ge=0)
    inertia: str = Field(default="Media")
    environment: str = Field(default="Interior industrial con polvo")
    ambient_temp_c: float = Field(default=40)
    altitude_m: float = Field(default=1000, ge=0)
    hazard_area: str = Field(default="Ninguna declarada")
    cable_run_m: float = Field(default=45, ge=0)
    control_voltage: float = Field(default=120, ge=1)
    needs_reversing: bool = Field(default=True)
    needs_brake: bool = Field(default=True)
    needs_limit_switches: bool = Field(default=True)
    needs_estop: bool = Field(default=True)
    needs_phase_monitor: bool = Field(default=True)
    budget_profile: str = Field(default="Profesional")
    quote_speed: str = Field(default="Rápida pero segura")
    preferred_quality: str = Field(default="Industrial confiable")
    labor_days_panel: float = Field(default=1.5, ge=0)
    labor_days_field: float = Field(default=1.5, ge=0)
    margin_percent: float = Field(default=25.0, ge=0, le=100)
    contingency_percent: float = Field(default=8.0, ge=0, le=100)
    load_capacity_ton: Optional[float] = Field(default=10.0, ge=0, description="Capacidad de izaje si aplica")
    field_photos_count: int = Field(default=3, ge=0, description="Cantidad de fotos/evidencias subidas")
    nameplate_photo_confirmed: bool = Field(default=True)
    panel_photo_confirmed: bool = Field(default=True)
    site_photo_confirmed: bool = Field(default=True)
    short_circuit_available_ka: Optional[float] = Field(default=None, ge=0)
    installation_scope: str = Field(default="Tablero + instalación en campo")
    quote_valid_days: int = Field(default=7, ge=1, le=60)
    client_budget_limit: Optional[float] = Field(default=None, ge=0)
    auto_block_low_confidence: bool = Field(default=True)
    user_notes: str = Field(default="Reemplazar tablero existente del guinche. Mantener huella de montaje. Considerar crecimiento futuro con variador.")

    @field_validator("budget_profile")
    @classmethod
    def normalize_budget(cls, v: str) -> str:
        return (v or "Profesional").strip()


class ComponentRequirement(BaseModel):
    component_id: str
    category: str
    item: str
    qty: float
    unit: str = "u"
    spec: str
    must_have: bool = True
    critical_checks: List[str] = []
    risk_note: str = ""


class SupplierOffer(BaseModel):
    component_id: str
    category: str
    description: str
    brand: str
    model: str
    supplier_id: str
    supplier_name: str
    city: str
    price_usd: float
    stock_status: str
    lead_time_days: int
    confidence: float
    source_type: str
    valid_until: str
    url: str = ""
    notes: str = ""
    score: float


class PriceDecision(BaseModel):
    component_id: str
    selected_offer: Optional[SupplierOffer] = None
    offers: List[SupplierOffer] = []
    qty: float = 1
    unit_cost: float = 0
    extended_cost: float = 0
    price_type: str = "estimado"
    confidence_label: str = "baja"
    decision_note: str = ""
    semaphore_color: str = "rojo"
    priceguard_score: float = 0
    market_band: Dict[str, Any] = {}
    anomaly_flags: List[str] = []
    action_required: str = "Enviar RFQ y confirmar precio."
    auto_corrected: bool = False
    rfq_priority: str = "alta"
    price_explanation: str = ""


class EngineeringPack(BaseModel):
    meta: Dict[str, Any]
    intake: Dict[str, Any]
    executive_verdict: Dict[str, Any]
    data_quality: Dict[str, Any]
    agents: List[Dict[str, Any]]
    calculations: Dict[str, Any]
    requirements: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    recommended_option: Dict[str, Any]
    market: Dict[str, Any]
    budget: Dict[str, Any]
    risks: List[Dict[str, Any]]
    checklists: Dict[str, List[str]]
    diagrams: Dict[str, str]
    statistics: Dict[str, Any]
    deliverables: List[Dict[str, Any]]
    rfq: Dict[str, Any]
    crm: Dict[str, Any]
    validation: Dict[str, Any]
    assumption_ledger: List[Dict[str, Any]] = []
    consistency_audit: Dict[str, Any] = {}
    release_gates: Dict[str, Any] = {}
    quote_readiness: Dict[str, Any] = {}
    field_verification_plan: List[Dict[str, Any]] = []
    qa_scorecard: Dict[str, Any] = {}

    review_board: Dict[str, Any] = {}
    guided_flow: Dict[str, Any] = {}
    output_quality_contract: Dict[str, Any] = {}
    cad_outputs: Dict[str, Any] = {}
    api_activation: Dict[str, Any] = {}
    priceguard: Dict[str, Any] = {}
    starter_intelligence: Dict[str, Any] = {}
    premium_document_contract: Dict[str, Any] = {}
    human_review_notice: str
