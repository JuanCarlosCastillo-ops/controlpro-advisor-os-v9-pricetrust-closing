from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from app.engine import example_intake, generate_engineering_pack, export_pack_markdown, export_client_proposal
from app.engine.models import ProjectIntake
from app.engine.pricing import load_price_catalog, load_suppliers, load_canonical_components, load_starter_profiles, priceguard_methodology
from app.engine.exports import export_bom_csv, export_bom_xlsx, export_pdf_report
from app.engine.cad import single_line_cad_svg, control_ladder_cad_svg, panel_layout_cad_svg, terminal_schedule, wire_schedule, drawio_xml
from app.engine.cad_exports import rows_to_csv
from app.integrations.config import integration_status, env_template

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="ControlPro Advisor OS V10 Architecture Lock",
    description="Sistema operativo en español para diseño, cotización, CAD-like, mercado, RFQ y activación con credenciales reales.",
    version="10.0-architecture-lock",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "product": "ControlPro Advisor OS V10 Architecture Lock",
        "language": "es",
        "modules": [
            "datos", "fotos", "3d", "unifilar", "control", "calculos", "soluciones",
            "BOM", "PriceGuard", "semaforo-precios", "mercado", "proveedores", "APIs", "RFQ", "presupuesto", "CRM", "validacion", "CAD-like", "Draw.io", "PDF", "Excel", "entregables"
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
    data = drawio_xml(intake, pack.calculations)
    return Response(
        content=data,
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_e001_unifilar.drawio"},
    )


@app.post("/api/export/cad/terminal-schedule-csv")
def export_terminal_schedule_csv(intake: ProjectIntake):
    data = rows_to_csv(terminal_schedule(intake))
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_lista_borneras.csv"},
    )


@app.post("/api/export/cad/wire-schedule-csv")
def export_wire_schedule_csv(intake: ProjectIntake):
    pack = generate_engineering_pack(intake)
    data = rows_to_csv(wire_schedule(intake, pack.calculations))
    return Response(
        content=data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=controlpro_lista_cables.csv"},
    )
