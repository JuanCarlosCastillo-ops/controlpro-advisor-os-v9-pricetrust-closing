from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import HTMLResponse

from app.ops.models import ApprovalRequest, AssetCreate, IncidentCreate
from app.ops.service import OpsService


router = APIRouter()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_service: Optional[OpsService] = None


def get_service() -> OpsService:
    global _service
    if _service is None:
        _service = OpsService()
    return _service


def _auth(x_teod_api_key: Optional[str] = Header(default=None)) -> None:
    expected = os.environ.get("TEOD_HUB_API_KEY")
    if expected and x_teod_api_key != expected:
        raise HTTPException(status_code=401, detail="invalid_api_key")


@router.get("/ops", response_class=HTMLResponse)
def ops_ui() -> str:
    return (STATIC_DIR / "ops.html").read_text(encoding="utf-8")


@router.get("/api/ops/health")
def ops_health():
    return {
        "status": "ok",
        "product": "TEOD Industrial AI Hub V1",
        "persistence": "sqlite-wal",
        "human_approval_gate": True,
        "agents": ["intake_triage", "safety_guard", "diagnostic_assistant", "work_planner", "supervisor"],
    }


@router.get("/api/ops/dashboard")
def dashboard(_: None = Depends(_auth)):
    return get_service().dashboard()


@router.get("/api/ops/assets")
def list_assets(_: None = Depends(_auth)):
    svc = get_service()
    return svc.store.list_assets(svc.organization_id)


@router.post("/api/ops/assets", status_code=201)
def create_asset(payload: AssetCreate, _: None = Depends(_auth)):
    try:
        return get_service().create_asset(payload)
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            raise HTTPException(status_code=409, detail="asset_tag_exists") from exc
        raise


@router.get("/api/ops/assets/{asset_id}")
def get_asset(asset_id: str, _: None = Depends(_auth)):
    svc = get_service()
    asset = svc.store.get_asset(asset_id, svc.organization_id)
    if not asset:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return asset


@router.get("/api/ops/incidents")
def list_incidents(status: Optional[str] = None, limit: int = Query(default=100, ge=1, le=500), _: None = Depends(_auth)):
    svc = get_service()
    return svc.store.list_incidents(svc.organization_id, status=status, limit=limit)


@router.post("/api/ops/incidents", status_code=201)
def create_incident(payload: IncidentCreate, _: None = Depends(_auth)):
    try:
        return get_service().open_incident(payload, analyze=True)
    except ValueError as exc:
        if str(exc) == "asset_not_found":
            raise HTTPException(status_code=404, detail="asset_not_found") from exc
        raise


@router.get("/api/ops/incidents/{incident_id}")
def get_incident(incident_id: str, _: None = Depends(_auth)):
    svc = get_service()
    incident = svc.store.get_incident(incident_id, svc.organization_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident_not_found")
    incident["agent_runs"] = svc.store.list_agent_runs(incident_id, svc.organization_id)
    incident["work_orders"] = [w for w in svc.store.list_work_orders(svc.organization_id) if w["incident_id"] == incident_id]
    return incident


@router.post("/api/ops/incidents/{incident_id}/analyze")
def analyze_incident(incident_id: str, _: None = Depends(_auth)):
    try:
        return get_service().analyze_incident(incident_id)
    except ValueError as exc:
        if str(exc) == "incident_not_found":
            raise HTTPException(status_code=404, detail="incident_not_found") from exc
        raise


@router.get("/api/ops/work-orders")
def list_work_orders(limit: int = Query(default=100, ge=1, le=500), _: None = Depends(_auth)):
    svc = get_service()
    return svc.store.list_work_orders(svc.organization_id, limit=limit)


@router.post("/api/ops/work-orders/{work_order_id}/approve")
def approve_work_order(work_order_id: str, payload: ApprovalRequest, _: None = Depends(_auth)):
    try:
        return get_service().approve_work_order(work_order_id, payload.approver, payload.note)
    except ValueError as exc:
        mapping = {"work_order_not_found": 404, "work_order_not_pending": 409}
        code = str(exc)
        if code in mapping:
            raise HTTPException(status_code=mapping[code], detail=code) from exc
        raise


@router.get("/api/ops/audit")
def audit(limit: int = Query(default=100, ge=1, le=500), _: None = Depends(_auth)):
    svc = get_service()
    return svc.store.list_events(svc.organization_id, limit=limit)


@router.post("/api/ops/demo/seed")
def seed_demo(_: None = Depends(_auth)):
    return get_service().seed_demo()
