from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.ops.agents import run_agent_stack
from app.ops.models import AssetCreate, IncidentCreate
from app.ops.store import OpsStore


DEFAULT_ORG = "teod-control"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class OpsService:
    def __init__(self, store: Optional[OpsStore] = None, organization_id: str = DEFAULT_ORG):
        self.store = store or OpsStore()
        self.organization_id = organization_id

    def create_asset(self, payload: AssetCreate) -> Dict[str, Any]:
        now = utcnow()
        row = payload.model_dump()
        row.update({"id": str(uuid4()), "organization_id": self.organization_id, "created_at": now, "updated_at": now})
        row["criticality"] = payload.criticality.value
        asset = self.store.create_asset(row)
        self._event("asset.created", "asset", asset["id"], {"tag": asset["tag"], "name": asset["name"]}, "human")
        return asset

    def open_incident(self, payload: IncidentCreate, analyze: bool = True) -> Dict[str, Any]:
        if payload.asset_id and not self.store.get_asset(payload.asset_id, self.organization_id):
            raise ValueError("asset_not_found")
        now = utcnow()
        row = payload.model_dump()
        row.update({
            "id": str(uuid4()), "organization_id": self.organization_id,
            "status": "new", "analysis": {}, "created_at": now, "updated_at": now,
        })
        row["severity"] = payload.severity.value
        incident = self.store.create_incident(row)
        self._event("incident.opened", "incident", incident["id"], {"severity": incident["severity"], "source": incident["source"]}, "human")
        return self.analyze_incident(incident["id"]) if analyze else incident

    def analyze_incident(self, incident_id: str) -> Dict[str, Any]:
        incident = self.store.get_incident(incident_id, self.organization_id)
        if not incident:
            raise ValueError("incident_not_found")
        asset = self.store.get_asset(incident["asset_id"], self.organization_id) if incident.get("asset_id") else None
        analysis, runs = run_agent_stack(incident, asset)
        supervisor = analysis["supervisor"]
        now = utcnow()
        self.store.update_incident_analysis(
            incident_id, self.organization_id, analysis,
            status=supervisor["incident_status"], severity=supervisor["severity"], updated_at=now,
        )
        for run in runs:
            output = run["output"]
            self.store.save_agent_run({
                "id": str(uuid4()), "organization_id": self.organization_id, "incident_id": incident_id,
                "agent_name": run["agent_name"], "status": "completed",
                "confidence": float(output.get("confidence", output.get("confidence_floor", 0.5))),
                "requires_human_approval": bool(output.get("requires_human_approval", False)),
                "input": {"asset_id": incident.get("asset_id"), "incident_id": incident_id},
                "output": output, "created_at": now,
            })
        plan = analysis["work_plan"]
        work_order = self.store.create_work_order({
            "id": str(uuid4()), "organization_id": self.organization_id,
            "incident_id": incident_id, "asset_id": incident.get("asset_id"),
            "title": plan["title"], "priority": plan["priority"], "status": "pending_approval",
            "steps": plan["steps"], "safety_notes": plan["safety_notes"],
            "requires_human_approval": True, "created_at": now, "updated_at": now,
        })
        self._event(
            "incident.analyzed", "incident", incident_id,
            {"severity": supervisor["severity"], "work_order_id": work_order["id"], "confidence_floor": supervisor["confidence_floor"]},
            "agent-stack",
        )
        result = self.store.get_incident(incident_id, self.organization_id)
        result["asset"] = asset
        result["agent_runs"] = self.store.list_agent_runs(incident_id, self.organization_id)
        result["work_order"] = work_order
        return result

    def approve_work_order(self, work_order_id: str, approver: str, note: str) -> Dict[str, Any]:
        current = self.store.get_work_order(work_order_id, self.organization_id)
        if not current:
            raise ValueError("work_order_not_found")
        if current["status"] != "pending_approval":
            raise ValueError("work_order_not_pending")
        now = utcnow()
        approved = self.store.approve_work_order(work_order_id, self.organization_id, approver, note, now)
        self._event("work_order.approved", "work_order", work_order_id, {"approver": approver, "note": note}, "human")
        return approved

    def dashboard(self) -> Dict[str, Any]:
        counts = self.store.dashboard_counts(self.organization_id)
        return {
            "organization_id": self.organization_id,
            "counts": counts,
            "recent_incidents": self.store.list_incidents(self.organization_id, limit=6),
            "recent_work_orders": self.store.list_work_orders(self.organization_id, limit=6),
            "recent_events": self.store.list_events(self.organization_id, limit=10),
            "architecture": {
                "layers": ["service desk", "active watch", "event agents", "copilot", "asset intelligence"],
                "agent_stack": ["intake_triage", "safety_guard", "diagnostic_assistant", "work_planner", "supervisor"],
                "human_gate": True,
            },
        }

    def seed_demo(self) -> Dict[str, Any]:
        existing = self.store.list_assets(self.organization_id)
        if existing:
            return {"seeded": False, "message": "La organización ya contiene activos.", "assets": existing}
        compressor = self.create_asset(AssetCreate(
            tag="CMP-01", name="Compresor principal 132 kW", asset_type="compressor",
            location="Planta industrial", manufacturer="", model="",
            voltage_v=440, rated_current_a=280, rated_power_kw=132,
            criticality="high",
            metadata={"motor_rpm": 3560, "power_factor": 0.91, "efficiency_percent": 94.5, "starter": "star-delta interno"},
        ))
        bank = self.create_asset(AssetCreate(
            tag="BC-01", name="Banco automático de capacitores", asset_type="capacitor_bank",
            location="Tablero general 440 V", voltage_v=440, criticality="high",
            metadata={"service": "corrección de factor de potencia", "upstream_transformer_kva": 500},
        ))
        transformer = self.create_asset(AssetCreate(
            tag="TR-01", name="Transformador seco 500 kVA", asset_type="transformer",
            location="Planta industrial", voltage_v=440, criticality="critical",
            metadata={"rating_kva": 500},
        ))
        demo_incident = self.open_incident(IncidentCreate(
            asset_id=compressor["id"], title="Calentamiento anormal en contactor",
            description="Se reporta contactor de potencia caliente durante operación del compresor. Requiere triage antes de reemplazar componentes.",
            severity="high", source="demo", measurements={"temperature_c": 76, "current_a": 280},
        ))
        return {"seeded": True, "assets": [compressor, bank, transformer], "demo_incident": demo_incident}

    def _event(self, event_type: str, entity_type: str, entity_id: str, payload: Dict[str, Any], actor: str) -> None:
        self.store.append_event({
            "organization_id": self.organization_id, "event_type": event_type,
            "entity_type": entity_type, "entity_id": entity_id,
            "payload": payload, "actor": actor, "occurred_at": utcnow(),
        })
