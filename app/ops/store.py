from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SCHEMA_VERSION = 1


class OpsStore:
    """Small, dependency-free persistence layer for the V1 operational hub.

    SQLite is intentionally used for the first deployable vertical slice. Each
    operation opens its own connection, WAL is enabled, and the schema is kept
    append-friendly so moving to Postgres/Supabase later is straightforward.
    """

    def __init__(self, db_path: Optional[str] = None):
        configured = db_path or os.environ.get("TEOD_HUB_DB_PATH") or "/tmp/teod_industrial_hub.db"
        self.db_path = str(Path(configured))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=8, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 8000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    name TEXT NOT NULL,
                    asset_type TEXT NOT NULL,
                    location TEXT NOT NULL DEFAULT '',
                    manufacturer TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL DEFAULT '',
                    voltage_v REAL,
                    rated_current_a REAL,
                    rated_power_kw REAL,
                    criticality TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(organization_id, tag)
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    asset_id TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source TEXT NOT NULL,
                    measurements_json TEXT NOT NULL DEFAULT '{}',
                    attachments_json TEXT NOT NULL DEFAULT '[]',
                    analysis_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS work_orders (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    asset_id TEXT,
                    title TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps_json TEXT NOT NULL DEFAULT '[]',
                    safety_notes_json TEXT NOT NULL DEFAULT '[]',
                    requires_human_approval INTEGER NOT NULL DEFAULT 1,
                    approved_by TEXT,
                    approved_at TEXT,
                    approval_note TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
                    FOREIGN KEY(asset_id) REFERENCES assets(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    occurred_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agent_runs (
                    id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    requires_human_approval INTEGER NOT NULL,
                    input_json TEXT NOT NULL DEFAULT '{}',
                    output_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(incident_id) REFERENCES incidents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(organization_id, status, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(organization_id, status, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_events_recent ON events(organization_id, occurred_at DESC);
                CREATE INDEX IF NOT EXISTS idx_agent_runs_incident ON agent_runs(incident_id, created_at ASC);
                """
            )
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @staticmethod
    def _decode(row: Optional[sqlite3.Row], json_fields: Iterable[str]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        data = dict(row)
        for field in json_fields:
            raw = data.pop(field, None)
            out_name = field[:-5] if field.endswith("_json") else field
            try:
                data[out_name] = json.loads(raw) if raw else ({} if field.endswith("analysis_json") else [])
            except json.JSONDecodeError:
                data[out_name] = raw
        for key in ("requires_human_approval",):
            if key in data:
                data[key] = bool(data[key])
        return data

    def create_asset(self, row: Dict[str, Any]) -> Dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO assets (
                    id, organization_id, tag, name, asset_type, location, manufacturer, model,
                    voltage_v, rated_current_a, rated_power_kw, criticality, metadata_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"], row["organization_id"], row["tag"], row["name"], row["asset_type"],
                    row.get("location", ""), row.get("manufacturer", ""), row.get("model", ""),
                    row.get("voltage_v"), row.get("rated_current_a"), row.get("rated_power_kw"),
                    row["criticality"], json.dumps(row.get("metadata", {}), ensure_ascii=False),
                    row["created_at"], row["updated_at"],
                ),
            )
        return self.get_asset(row["id"], row["organization_id"])

    def list_assets(self, organization_id: str) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM assets WHERE organization_id=? ORDER BY criticality DESC, tag ASC",
                (organization_id,),
            ).fetchall()
        return [self._decode(r, ["metadata_json"]) for r in rows]

    def get_asset(self, asset_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM assets WHERE id=? AND organization_id=?",
                (asset_id, organization_id),
            ).fetchone()
        return self._decode(row, ["metadata_json"])

    def create_incident(self, row: Dict[str, Any]) -> Dict[str, Any]:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO incidents (
                    id, organization_id, asset_id, title, description, severity, status, source,
                    measurements_json, attachments_json, analysis_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"], row["organization_id"], row.get("asset_id"), row["title"], row["description"],
                    row["severity"], row["status"], row["source"],
                    json.dumps(row.get("measurements", {}), ensure_ascii=False),
                    json.dumps(row.get("attachments", []), ensure_ascii=False),
                    json.dumps(row.get("analysis", {}), ensure_ascii=False),
                    row["created_at"], row["updated_at"],
                ),
            )
        return self.get_incident(row["id"], row["organization_id"])

    def list_incidents(self, organization_id: str, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM incidents WHERE organization_id=? AND status=? ORDER BY created_at DESC LIMIT ?",
                    (organization_id, status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM incidents WHERE organization_id=? ORDER BY created_at DESC LIMIT ?",
                    (organization_id, limit),
                ).fetchall()
        return [self._decode(r, ["measurements_json", "attachments_json", "analysis_json"]) for r in rows]

    def get_incident(self, incident_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM incidents WHERE id=? AND organization_id=?",
                (incident_id, organization_id),
            ).fetchone()
        return self._decode(row, ["measurements_json", "attachments_json", "analysis_json"])

    def update_incident_analysis(self, incident_id: str, organization_id: str, analysis: Dict[str, Any], status: str, severity: str, updated_at: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE incidents SET analysis_json=?, status=?, severity=?, updated_at=? WHERE id=? AND organization_id=?",
                (json.dumps(analysis, ensure_ascii=False), status, severity, updated_at, incident_id, organization_id),
            )

    def create_work_order(self, row: Dict[str, Any]) -> Dict[str, Any]:
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT id FROM work_orders WHERE organization_id=? AND incident_id=? AND status IN ('pending_approval','approved','in_progress') ORDER BY created_at DESC LIMIT 1",
                (row["organization_id"], row["incident_id"]),
            ).fetchone()
            if existing:
                return self.get_work_order(existing["id"], row["organization_id"])
            conn.execute(
                """INSERT INTO work_orders (
                    id, organization_id, incident_id, asset_id, title, priority, status,
                    steps_json, safety_notes_json, requires_human_approval,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"], row["organization_id"], row["incident_id"], row.get("asset_id"), row["title"],
                    row["priority"], row["status"], json.dumps(row.get("steps", []), ensure_ascii=False),
                    json.dumps(row.get("safety_notes", []), ensure_ascii=False), int(row.get("requires_human_approval", True)),
                    row["created_at"], row["updated_at"],
                ),
            )
        return self.get_work_order(row["id"], row["organization_id"])

    def get_work_order(self, work_order_id: str, organization_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM work_orders WHERE id=? AND organization_id=?",
                (work_order_id, organization_id),
            ).fetchone()
        return self._decode(row, ["steps_json", "safety_notes_json"])

    def list_work_orders(self, organization_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM work_orders WHERE organization_id=? ORDER BY created_at DESC LIMIT ?",
                (organization_id, limit),
            ).fetchall()
        return [self._decode(r, ["steps_json", "safety_notes_json"]) for r in rows]

    def approve_work_order(self, work_order_id: str, organization_id: str, approver: str, note: str, approved_at: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            conn.execute(
                """UPDATE work_orders
                   SET status='approved', approved_by=?, approved_at=?, approval_note=?, updated_at=?
                   WHERE id=? AND organization_id=? AND status='pending_approval'""",
                (approver, approved_at, note, approved_at, work_order_id, organization_id),
            )
        return self.get_work_order(work_order_id, organization_id)

    def append_event(self, row: Dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO events (organization_id,event_type,entity_type,entity_id,actor,payload_json,occurred_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    row["organization_id"], row["event_type"], row["entity_type"], row["entity_id"],
                    row["actor"], json.dumps(row.get("payload", {}), ensure_ascii=False), row["occurred_at"],
                ),
            )

    def list_events(self, organization_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE organization_id=? ORDER BY id DESC LIMIT ?",
                (organization_id, limit),
            ).fetchall()
        return [self._decode(r, ["payload_json"]) for r in rows]

    def save_agent_run(self, row: Dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO agent_runs (
                    id, organization_id, incident_id, agent_name, status, confidence,
                    requires_human_approval, input_json, output_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"], row["organization_id"], row["incident_id"], row["agent_name"], row["status"],
                    row["confidence"], int(row["requires_human_approval"]),
                    json.dumps(row.get("input", {}), ensure_ascii=False),
                    json.dumps(row.get("output", {}), ensure_ascii=False), row["created_at"],
                ),
            )

    def list_agent_runs(self, incident_id: str, organization_id: str) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_runs WHERE incident_id=? AND organization_id=? ORDER BY created_at ASC",
                (incident_id, organization_id),
            ).fetchall()
        return [self._decode(r, ["input_json", "output_json"]) for r in rows]

    def dashboard_counts(self, organization_id: str) -> Dict[str, int]:
        with self.connect() as conn:
            assets = conn.execute("SELECT COUNT(*) c FROM assets WHERE organization_id=?", (organization_id,)).fetchone()["c"]
            open_incidents = conn.execute("SELECT COUNT(*) c FROM incidents WHERE organization_id=? AND status NOT IN ('closed','resolved')", (organization_id,)).fetchone()["c"]
            critical = conn.execute("SELECT COUNT(*) c FROM incidents WHERE organization_id=? AND severity='critical' AND status NOT IN ('closed','resolved')", (organization_id,)).fetchone()["c"]
            pending = conn.execute("SELECT COUNT(*) c FROM work_orders WHERE organization_id=? AND status='pending_approval'", (organization_id,)).fetchone()["c"]
        return {"assets": assets, "open_incidents": open_incidents, "critical_incidents": critical, "pending_approvals": pending}
