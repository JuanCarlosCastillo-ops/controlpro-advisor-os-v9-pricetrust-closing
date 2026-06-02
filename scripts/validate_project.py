from __future__ import annotations
import json
from pathlib import Path
from app.engine.advisor import generate_engineering_pack, export_pack_markdown, export_client_proposal
from app.engine.exports import export_bom_csv, export_bom_xlsx, export_pdf_report
from app.engine.models import ProjectIntake

ROOT = Path(__file__).resolve().parents[1]
required = [
    "app/main.py", "app/engine/advisor.py", "app/engine/pricing.py", "app/engine/models.py",
    "app/static/index.html", "app/static/styles.css", "app/static/app.js", "app/engine/cad.py", "app/integrations/config.py", ".env.example",
    "app/data/price_catalog.csv", "app/data/suppliers.csv", "app/data/starter_profiles.json", "README.md", "DEPLOY_RENDER.md", "GITHUB_UPLOAD.md"
]
missing = [p for p in required if not (ROOT / p).exists()]
if missing:
    raise SystemExit(f"Missing files: {missing}")

example = json.loads((ROOT / "examples/hoist_intake.json").read_text(encoding="utf-8"))
pack = generate_engineering_pack(ProjectIntake(**example)).model_dump()
assert pack["statistics"]["engineering_completeness_percent"] >= 80
assert pack["market"]["summary"]["coverage_percent"] >= 80
assert pack["budget"]["recommended_sell_price"] > pack["budget"]["floor_price"]
assert "Buenos días" in pack["rfq"]["message"]
assert "E-001" in pack["diagrams"]["single_line_svg"]
assert "Expediente" in export_pack_markdown(ProjectIntake(**example))
assert ("Propuesta" in export_client_proposal(ProjectIntake(**example)) or "PRE-COTIZACIÓN" in export_client_proposal(ProjectIntake(**example)))
assert "component_id" in export_bom_csv(ProjectIntake(**example))
assert export_bom_xlsx(ProjectIntake(**example))[:2] == b"PK"
assert export_pdf_report(ProjectIntake(**example))[:4] == b"%PDF"
assert pack["review_board"]["personas"]
assert pack["guided_flow"]["modo_rapido"]
assert pack["cad_outputs"]["terminal_schedule"]
assert pack["cad_outputs"]["wire_schedule"]
assert pack["api_activation"]["services"]
assert pack["priceguard"]["summary"]["priceguard_score_percent"] >= 70
assert pack["starter_intelligence"]["profiles"]
assert pack["premium_document_contract"]["pdf"]
print("VALIDATION OK")
print(f"Engineering completeness: {pack['statistics']['engineering_completeness_percent']}%")
print(f"Market coverage: {pack['statistics']['market_coverage_percent']}%")
print(f"RFQ items: {pack['statistics']['rfq_required_items']}")
print(f"PriceGuard: {pack['statistics']['priceguard_score_percent']}%")
print(f"MathTrust: {pack['statistics'].get('mathtrust_score_percent', 0)}%")
print(f"Recommended sell price: ${pack['budget']['recommended_sell_price']}")
