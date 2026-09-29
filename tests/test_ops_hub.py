from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.ops.router as ops_router_module
from app.ops.router import router
from app.ops.service import OpsService
from app.ops.store import OpsStore


def build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("TEOD_HUB_API_KEY", "test-ops-key")
    ops_router_module._service = OpsService(OpsStore(str(tmp_path / "ops.db")))
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    client.headers.update({"X-TEOD-API-Key": "test-ops-key"})
    return client


def test_operational_hub_end_to_end(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    assert client.get("/api/ops/health").json()["human_approval_gate"] is True

    asset = client.post("/api/ops/assets", json={
        "tag": "CMP-TEST", "name": "Compresor prueba", "asset_type": "compressor",
        "voltage_v": 440, "rated_current_a": 100, "rated_power_kw": 55,
        "criticality": "high", "location": "Planta"
    })
    assert asset.status_code == 201
    asset_id = asset.json()["id"]

    incident = client.post("/api/ops/incidents", json={
        "asset_id": asset_id,
        "title": "Contactor con temperatura elevada",
        "description": "Contactor caliente durante operación del compresor.",
        "severity": "high",
        "measurements": {"temperature_c": 76, "current_a": 110}
    })
    assert incident.status_code == 201
    data = incident.json()
    assert len(data["agent_runs"]) == 5
    assert data["analysis"]["supervisor"]["requires_human_approval"] is True
    assert data["work_order"]["status"] == "pending_approval"

    order_id = data["work_order"]["id"]
    approval = client.post(f"/api/ops/work-orders/{order_id}/approve", json={"approver":"Ing. QA","note":"Revisado"})
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"

    dashboard = client.get("/api/ops/dashboard").json()
    assert dashboard["counts"]["assets"] == 1
    assert dashboard["counts"]["pending_approvals"] == 0
    assert len(dashboard["architecture"]["agent_stack"]) == 5
    assert client.get("/api/ops/audit").json()


def test_safety_guard_escalates_critical_temperature(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    asset = client.post("/api/ops/assets", json={
        "tag":"M-01","name":"Motor","asset_type":"motor","rated_current_a":50,"criticality":"medium"
    }).json()
    incident = client.post("/api/ops/incidents", json={
        "asset_id":asset["id"],"title":"Temperatura crítica","description":"Olor a quemado en contactor",
        "severity":"medium","measurements":{"temperature_c":96,"current_a":50}
    }).json()
    assert incident["severity"] == "critical"
    assert incident["analysis"]["safety"]["flags"]
    assert incident["work_order"]["priority"] == "critical"


def test_duplicate_asset_tag_is_blocked(tmp_path, monkeypatch):
    client = build_client(tmp_path, monkeypatch)
    payload={"tag":"QF-01","name":"Breaker","asset_type":"breaker","criticality":"medium"}
    assert client.post("/api/ops/assets", json=payload).status_code == 201
    assert client.post("/api/ops/assets", json=payload).status_code == 409


def test_operational_routes_fail_closed_without_key(tmp_path, monkeypatch):
    monkeypatch.delenv("TEOD_HUB_API_KEY", raising=False)
    ops_router_module._service = OpsService(OpsStore(str(tmp_path / "ops.db")))
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/api/ops/health").status_code == 200
    assert client.get("/api/ops/dashboard").status_code == 503


def test_operational_routes_reject_wrong_key(tmp_path, monkeypatch):
    monkeypatch.setenv("TEOD_HUB_API_KEY", "correct-key")
    ops_router_module._service = OpsService(OpsStore(str(tmp_path / "ops.db")))
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    assert client.get("/api/ops/dashboard", headers={"X-TEOD-API-Key":"wrong-key"}).status_code == 401
