from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import json, os
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from app.engine import example_intake, generate_engineering_pack, export_pack_markdown, export_client_proposal
from app.engine.models import ProjectIntake
from app.engine.pricing import load_price_catalog, load_suppliers, load_canonical_components, load_starter_profiles, load_market_ledger, priceguard_methodology
from app.engine.exports import export_bom_csv, export_bom_xlsx, export_pdf_report
from app.engine.cad import single_line_cad_svg, control_ladder_cad_svg, panel_layout_cad_svg, terminal_schedule, wire_schedule, drawio_xml
from app.engine.cad_exports import rows_to_csv
from app.integrations.config import integration_status, env_template

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="ControlPro Advisor OS V16 MarketVision Pro",
    description="Sistema operativo en español para diseño, cotización, CAD-like, mercado, RFQ y activación con credenciales reales.",
    version="16.0-marketvision-pro",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")




class LeadPilot(BaseModel):
    name: str = Field(default="", max_length=120)
    email: str = Field(default="", max_length=160)
    phone: str = Field(default="", max_length=80)
    company: str = Field(default="", max_length=160)
    role: str = Field(default="", max_length=120)
    note: str = Field(default="", max_length=500)


@app.post("/api/leads")
def capture_lead(lead: LeadPilot):
    row = lead.model_dump()
    row["captured_at"] = datetime.now(timezone.utc).isoformat()
    row["source"] = "controlpro_v16_pilot"
    path = os.environ.get("CONTROLPRO_LEADS_PATH", "/tmp/controlpro_v16_leads.jsonl")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        stored = True
    except Exception:
        stored = False
    return {"status": "ok", "stored_runtime": stored, "message": "Registro de piloto recibido. Para producción conectar base de datos/CRM."}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "product": "ControlPro Advisor OS V16 MarketVision Pro",
        "language": "es",
        "modules": [
            "datos", "fotos", "3d", "unifilar", "control", "calculos", "soluciones",
            "BOM", "PriceGuard", "semaforo-precios", "mercado", "proveedores", "APIs", "RFQ", "presupuesto", "CRM", "registro_piloto", "capas_cliente", "validacion", "CAD-like", "Draw.io", "PDF", "Excel", "entregables"
        ],
        "safety_boundary": "asesor técnico-comercial; requiere aprobación humana antes de construir o energizar",
    }


@app.get("/api/example")
def example():
    return example_intake()


@app.get("/api/catalog/components")
def components():
    return load_canonical_components()


@app.get("/api/catalog/suppliers")
def suppliers():
    return load_suppliers()


@app.get("/api/catalog/prices")
def prices():
    return load_price_catalog()


@app.get("/api/catalog/market-ledger")
def market_ledger():
    return load_market_ledger()


@app.get("/api/catalog/starter-profiles")
def starter_profiles():
    return load_starter_profiles()


@app.get("/api/priceguard/methodology")
def priceguard():
    return priceguard_methodology()


@app.post("/api/generate")
def generate(intake: ProjectIntake):
    return generate_engineering_pack(intake).model_dump()


@app.post("/api/export/markdown", response_class=PlainTextResponse)
def export_markdown(intake: ProjectIntake):
    return export_pack_markdown(intake)


@app.post("/api/export/client-proposal", response_class=PlainTextResponse)
def export_proposal(intake: ProjectIntake):
    return export_client_proposal(intake)


@app.post("/api/export/bom-csv")
def export_bom_as_csv(intake: ProjectIntake):
    data = export_bom_csv(intake)
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_bom_cotizable.csv"},
    )


@app.post("/api/export/bom-xlsx")
def export_bom_as_xlsx(intake: ProjectIntake):
    data = export_bom_xlsx(intake)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=controlpro_bom_cotizable.xlsx"},
    )


@app.post("/api/export/pdf")
def export_pdf(intake: ProjectIntake):
    data = export_pdf_report(intake)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=controlpro_reporte_tecnico_comercial.pdf"},
    )


@app.get("/api/market/live/mercadolibre")
async def live_mercadolibre(q: str, limit: int = 8):
    from app.integrations.mercadolibre import search_items
    return await search_items(q, limit=limit)


@app.get("/api/market/live/google-places")
async def live_google_places(q: str):
    from app.integrations.google_places import search_suppliers
    return await search_suppliers(q)


@app.get("/api/integrations/status")
def integrations_status():
    return integration_status()


@app.get("/api/integrations/env-template", response_class=PlainTextResponse)
def integrations_env_template():
    return env_template()


@app.post("/api/export/cad/single-line-svg", response_class=PlainTextResponse)
def export_single_line_svg(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    return pack.diagrams["single_line_svg"]


@app.post("/api/export/cad/control-ladder-svg", response_class=PlainTextResponse)
def export_control_ladder_svg(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    return pack.diagrams["control_ladder_svg"]


@app.post("/api/export/cad/panel-layout-svg", response_class=PlainTextResponse)
def export_panel_layout_svg(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    return pack.diagrams["panel_preview_svg"]


@app.post("/api/export/cad/drawio")
def export_drawio(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    arch = pack.starter_intelligence.get("architecture_lock", {})
    data = drawio_xml(intake, pack.calculations, arch)
    return Response(
        content=data,
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_e001_unifilar.drawio"},
    )


@app.post("/api/export/cad/terminal-schedule-csv")
def export_terminal_schedule_csv(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    arch = pack.starter_intelligence.get("architecture_lock", {})
    data = rows_to_csv(terminal_schedule(intake, arch))
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_lista_borneras.csv"},
    )


@app.post("/api/export/cad/wire-schedule-csv")
def export_wire_schedule_csv(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    arch = pack.starter_intelligence.get("architecture_lock", {})
    data = rows_to_csv(wire_schedule(intake, pack.calculations, arch))
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_lista_cables.csv"},
    )
