from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AssetCreate(BaseModel):
    tag: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=160)
    asset_type: str = Field(min_length=1, max_length=80)
    location: str = Field(default="", max_length=160)
    manufacturer: str = Field(default="", max_length=120)
    model: str = Field(default="", max_length=120)
    voltage_v: Optional[float] = Field(default=None, ge=0)
    rated_current_a: Optional[float] = Field(default=None, ge=0)
    rated_power_kw: Optional[float] = Field(default=None, ge=0)
    criticality: Severity = Severity.medium
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentCreate(BaseModel):
    asset_id: Optional[str] = None
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=3, max_length=4000)
    severity: Severity = Severity.medium
    source: str = Field(default="manual", max_length=80)
    measurements: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[str] = Field(default_factory=list)


class IncidentPatch(BaseModel):
    status: Optional[str] = Field(default=None, max_length=40)
    severity: Optional[Severity] = None


class EventCreate(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=80)
    entity_id: str = Field(min_length=1, max_length=120)
    payload: Dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="system", max_length=120)


class ApprovalRequest(BaseModel):
    approver: str = Field(min_length=2, max_length=120)
    note: str = Field(default="", max_length=1000)
