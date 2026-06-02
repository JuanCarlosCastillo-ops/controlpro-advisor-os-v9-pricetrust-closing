from __future__ import annotations
import json
from pathlib import Path
from app.engine.advisor import generate_engineering_pack
from app.engine.models import ProjectIntake

ROOT = Path(__file__).resolve().parents[1]
scenarios = []
scenarios.append(("demo_guinche", json.loads((ROOT / "examples/hoist_intake.json").read_text(encoding="utf-8"))))
low = scenarios[0][1].copy()
low.update({"full_load_amps": None, "field_photos_count": 0, "needs_brake": False, "needs_limit_switches": False})
scenarios.append(("caso_incompleto_bloqueado", low))
comp = scenarios[0][1].copy()
comp.update({"project_name": "Compresor 15 HP — arranque controlado", "application": "Compresor de aire", "load_type": "Compresor", "motor_power_hp": 15, "full_load_amps": 22.0, "needs_reversing": False, "needs_brake": False, "needs_limit_switches": False, "starts_per_hour": 8})
scenarios.append(("compresor_estandar", comp))

for name, payload in scenarios:
    pack = generate_engineering_pack(ProjectIntake(**payload)).model_dump()
    print(f"[{name}]")
    print("  completitud:", pack["statistics"]["engineering_completeness_percent"])
    print("  quote:", pack["quote_readiness"]["status"], pack["quote_readiness"]["score_percent"])
    print("  construccion:", pack["release_gates"]["construction_ready"])
    print("  precio recomendado:", pack["budget"]["recommended_sell_price"])
    print("  RFQ:", pack["statistics"]["rfq_required_items"])
