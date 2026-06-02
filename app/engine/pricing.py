from __future__ import annotations

import csv
import json
import re
import statistics
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .models import ComponentRequirement, PriceDecision, ProjectIntake, SupplierOffer

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

SOURCE_WEIGHT = {
    "confirmed": 1.00,
    "internal": 0.82,
    "reference": 0.68,
    "marketplace": 0.62,
    "estimate": 0.30,
}
STOCK_WEIGHT = {
    "available": 1.00,
    "quote_needed": 0.62,
    "unknown": 0.50,
    "unavailable": 0.12,
}


# -----------------------------
# FitLock / Sizing Lock helpers
# -----------------------------
def _num(v: str) -> float | None:
    try:
        return float(v)
    except Exception:
        return None


def _extract_amp_values(text: str) -> list[float]:
    text = text or ""
    vals: list[float] = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*A\b", text, flags=re.I):
        vals.append(float(m.group(1)))
    # Model strings like ACS580-01-039A-4
    for m in re.finditer(r"(?<![A-Z0-9])(\d{2,4})A(?![A-Z])", text, flags=re.I):
        vals.append(float(m.group(1).lstrip('0') or 0))
    return vals


def _extract_hp_values(text: str) -> list[float]:
    return [float(m.group(1)) for m in re.finditer(r"(\d+(?:\.\d+)?)\s*HP\b", text or "", flags=re.I)]


def _extract_kva_values(text: str) -> list[float]:
    return [float(m.group(1)) for m in re.finditer(r"(\d+(?:\.\d+)?)\s*kVA\b", text or "", flags=re.I)]




def _extract_voltage_values(text: str) -> list[float]:
    return [float(m.group(1)) for m in re.finditer(r"(\d+(?:\.\d+)?)\s*V\b", text or "", flags=re.I)]


def _extract_awg(text: str) -> int | None:
    m = re.search(r"#\s*(\d+)\s*AWG", text or "", flags=re.I)
    return int(m.group(1)) if m else None


def _extract_va_requirement(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*VA\b", text or "", flags=re.I)
    return float(m.group(1)) if m else None


def _extract_required_current(req: ComponentRequirement, intake: ProjectIntake) -> float | None:
    spec = req.spec or ""
    # Corriente >= X A / compatible con X A / ajuste X A / preliminar X A
    patterns = [
        r">=\s*(\d+(?:\.\d+)?)\s*A",
        r"compatible con\s*(\d+(?:\.\d+)?)\s*A",
        r"ajuste\s*(\d+(?:\.\d+)?)\s*A",
        r"(\d+(?:\.\d+)?)\s*A\s*preliminar",
        r"rango que cubra ajuste\s*(\d+(?:\.\d+)?)\s*A",
    ]
    for pat in patterns:
        m = re.search(pat, spec, flags=re.I)
        if m:
            return float(m.group(1))
    # Fallback for power components
    if req.component_id in {"vfd", "soft_starter", "line_reactor", "braking_resistor", "power_cable"}:
        if intake.full_load_amps:
            return float(intake.full_load_amps)
    return None


def _fitlock_estimate(req: ComponentRequirement, intake: ProjectIntake) -> float:
    """Budgetary placeholder when catalog does not have a technically fitting item.

    V16 first tries MarketVision Ledger median/IQR references. This is still
    intentionally marked red/RFQ when FitLock blocks: it is an order-of-magnitude
    value, not a sellable confirmed price.
    """
    ref = ledger_reference(req.component_id, intake)
    if ref.get("available") and ref.get("median_usd"):
        return float(ref["median_usd"])
    hp = max(float(intake.motor_power_hp or 0), 1.0)
    flc = float(intake.full_load_amps or 0) if intake.full_load_amps else None
    text = (req.item + " " + req.spec + " " + req.component_id).lower()
    if req.component_id == "vfd":
        return max(1200.0, hp * 95.0)
    if req.component_id == "soft_starter":
        return max(750.0, hp * 55.0)
    if req.component_id in {"mccb_main"}:
        req_a = _extract_required_current(req, intake) or flc or 60
        return max(160.0, req_a * 6.5)
    if "contactor" in text or req.component_id in {"contactor_fwd", "contactor_rev", "main_contactor", "bypass_contactor"}:
        req_a = _extract_required_current(req, intake) or flc or 32
        return max(90.0, req_a * 7.0)
    if req.component_id == "overload_relay":
        req_a = _extract_required_current(req, intake) or flc or 30
        return max(80.0, req_a * 3.5)
    if req.component_id == "line_reactor":
        return max(220.0, hp * 13.0)
    if req.component_id == "braking_resistor":
        return max(260.0, hp * 10.0)
    if req.component_id == "control_transformer":
        va = _extract_va_requirement(req.spec) or max(750, hp * 80)
        return max(140.0, va / 1000.0 * 180.0)
    if req.component_id == "cabinet":
        return 135.0 if hp <= 30 else (450.0 if hp <= 100 else 950.0)
    if req.component_id == "power_cable":
        length = max(float(req.qty or 1), 1.0)
        unit = 2.5 if (flc or 0) <= 45 else (8.0 if (flc or 0) <= 120 else 25.0)
        return unit
    return estimate_fallback(req)


def _fitlock_offer(req: ComponentRequirement, offer: SupplierOffer, intake: ProjectIntake) -> tuple[bool, list[str]]:
    """Hard technical compatibility check between BOM requirement and catalog offer.

    If this fails, PriceGuard cannot turn green regardless of price.
    """
    flags: list[str] = []
    blob = f"{offer.description} {offer.brand} {offer.model}".upper()
    req_current = _extract_required_current(req, intake)
    hp_required = float(intake.motor_power_hp or 0)
    current_values = _extract_amp_values(blob)
    hp_values = _extract_hp_values(blob)
    kva_values = _extract_kva_values(blob)

    def max_or_none(vals):
        return max(vals) if vals else None

    offer_a = max_or_none(current_values)
    offer_hp = max_or_none(hp_values)

    # Dedicated conductor sizing is a blocker; do not use #8 or any stock cable as if it were valid.
    if req.component_id == "power_cable" and "REQUIERE CÁLCULO DEDICADO" in (req.spec or "").upper():
        flags.append("FitLock: conductor requiere cálculo dedicado; catálogo piloto no puede cerrar calibre/precio")

    if req.component_id in {"mccb_main", "contactor_fwd", "contactor_rev", "main_contactor", "star_contactor", "delta_contactor", "bypass_contactor", "overload_relay", "soft_starter", "line_reactor"}:
        if req_current and offer_a and offer_a < req_current * 0.95:
            flags.append(f"FitLock: corriente ofertada {offer_a:g} A menor que requerida {req_current:g} A")
        elif req_current and not offer_a and req.component_id not in {"line_reactor"}:
            flags.append(f"FitLock: oferta sin corriente verificable para requerimiento {req_current:g} A")

    if req.component_id in {"vfd", "soft_starter", "line_reactor", "braking_resistor"}:
        if offer_hp and hp_required and offer_hp < hp_required * 0.90:
            flags.append(f"FitLock: oferta {offer_hp:g} HP menor que motor {hp_required:g} HP")
        if req_current and offer_a and offer_a < req_current * 0.90:
            flags.append(f"FitLock: corriente ofertada {offer_a:g} A menor que FLA/requerida {req_current:g} A")
        if not offer_hp and not offer_a:
            flags.append("FitLock: oferta sin HP/A verificable para componente crítico")

    if req.component_id == "control_transformer":
        req_va = _extract_va_requirement(req.spec)
        offer_kva = max_or_none(kva_values)
        if req_va and offer_kva and offer_kva * 1000 < req_va * 0.90:
            flags.append(f"FitLock: transformador {offer_kva:g} kVA menor que {req_va:g} VA requeridos")
        elif req_va and not offer_kva:
            flags.append("FitLock: transformador sin kVA verificable")

    # Voltage compatibility for critical power electronics.
    if req.component_id in {"vfd", "soft_starter", "line_reactor", "mccb_main", "contactor_fwd", "contactor_rev", "main_contactor", "bypass_contactor"}:
        vvals = _extract_voltage_values(blob)
        if vvals:
            # Allow 460/480 class for 440V, but do not accept 460V equipment as confirmed for 220V jobs.
            max_v = max(vvals)
            if intake.voltage <= 240 and max_v > 300:
                flags.append(f"FitLock: oferta clase {max_v:g} V no corresponde a proyecto {intake.voltage:g} V")
            elif intake.voltage >= 380 and max_v < 300:
                flags.append(f"FitLock: oferta clase {max_v:g} V menor que proyecto {intake.voltage:g} V")

    if req.component_id == "power_cable":
        req_awg = _extract_awg(req.spec)
        offer_awg = _extract_awg(blob)
        if req_awg and offer_awg and req_awg != offer_awg:
            flags.append(f"FitLock: cable ofertado #{offer_awg} AWG no coincide con cálculo preliminar #{req_awg} AWG")

    if req.component_id == "cabinet" and hp_required >= 75:
        # The pilot catalog cabinet is 600x400; large VFD jobs must go to RFQ/layout.
        if any(token in blob for token in ["600X400", "604025", "600 X 400"]):
            flags.append("FitLock: gabinete piloto 600x400 no validado para VFD/motor de alta potencia")

    return len(flags) == 0, flags



def _read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_suppliers() -> Dict[str, Dict[str, str]]:
    return {r["supplier_id"]: r for r in _read_csv(DATA_DIR / "suppliers.csv")}


def load_price_catalog() -> List[Dict[str, str]]:
    return _read_csv(DATA_DIR / "price_catalog.csv")


def load_canonical_components() -> List[Dict[str, object]]:
    return json.loads((DATA_DIR / "canonical_components.json").read_text(encoding="utf-8"))


def load_starter_profiles() -> List[Dict[str, Any]]:
    path = DATA_DIR / "starter_profiles.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


# -----------------------------
# MarketVision Ledger / robust reference pricing
# -----------------------------
def load_market_ledger() -> List[Dict[str, str]]:
    path = DATA_DIR / "market_ledger.csv"
    if not path.exists():
        return []
    return _read_csv(path)


def _voltage_class(voltage: float) -> str:
    return "240" if float(voltage or 0) <= 260 else "480"


def _ledger_candidates(component_id: str, intake: ProjectIntake) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    hp = float(intake.motor_power_hp or 0)
    fla = float(intake.full_load_amps or 0) if intake.full_load_amps else 0.0
    vclass = _voltage_class(float(intake.voltage or 0))
    for r in load_market_ledger():
        if r.get("component_id") != component_id:
            continue
        vc = (r.get("voltage_class") or "any").strip().lower()
        if vc not in {"any", vclass}:
            continue
        try:
            hp_min, hp_max = float(r.get("hp_min") or 0), float(r.get("hp_max") or 99999)
            a_min, a_max = float(r.get("current_min_a") or 0), float(r.get("current_max_a") or 99999)
        except Exception:
            continue
        hp_ok = hp_min <= hp <= hp_max or hp == 0
        a_ok = a_min <= fla <= a_max or fla == 0
        if hp_ok or a_ok:
            out.append(r)
    return out


def ledger_reference(component_id: str, intake: ProjectIntake) -> Dict[str, Any]:
    rows = _ledger_candidates(component_id, intake)
    if not rows:
        return {"available": False, "component_id": component_id, "note": "Sin referencia ledger para este tamaño/tensión."}
    def f(row: Dict[str,str], key: str, default: float = 0.0) -> float:
        try: return float(row.get(key) or default)
        except Exception: return default
    # Prefer higher confidence and closest HP/current band
    rows = sorted(rows, key=lambda r: (f(r, "confidence"), -abs((f(r,"hp_min")+f(r,"hp_max"))/2 - float(intake.motor_power_hp or 0))), reverse=True)
    r = rows[0]
    return {
        "available": True,
        "component_id": component_id,
        "description": r.get("description", ""),
        "p25_usd": f(r, "p25_usd"),
        "median_usd": f(r, "median_usd"),
        "p75_usd": f(r, "p75_usd"),
        "confidence": f(r, "confidence", 0.4),
        "source_type": r.get("source_type", "ledger"),
        "source_url": r.get("source_url", ""),
        "last_confirmed": r.get("last_confirmed", ""),
        "notes": r.get("notes", ""),
        "policy": "Referencia robusta por mediana/IQR. No reemplaza precio confirmado por proveedor; sirve para evitar perderse cuando no hay API o catálogo compatible.",
    }


def ledger_overview(decisions: List[PriceDecision], intake: ProjectIntake) -> Dict[str, Any]:
    comps = sorted({d.component_id for d in decisions})
    refs = [ledger_reference(c, intake) for c in comps]
    available = [r for r in refs if r.get("available")]
    return {
        "enabled": True,
        "reference_count": len(available),
        "total_components": len(comps),
        "coverage_percent": round(len(available) / max(1, len(comps)) * 100, 1),
        "references": available[:20],
        "truth_rule": "Market Ledger es memoria de precios por componente/tamaño/ciudad. Si no hay proveedor confirmado, el precio sigue siendo referencial o pre-cotización.",
    }


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _location_bonus(row: Dict[str, str], intake: ProjectIntake) -> float:
    city = (row.get("city") or "").lower()
    province = (intake.location_province or "").lower()
    bonus = 0.0
    if province and province in city:
        bonus += 0.08
    if "machala" in city and ("oro" in province or "el oro" in province):
        bonus += 0.07
    if "base interna" in city:
        bonus += 0.02
    return bonus


def offer_score(row: Dict[str, str], intake: ProjectIntake, supplier: Dict[str, str]) -> float:
    confidence = float(row.get("confidence") or 0.5)
    stock = row.get("stock_status", "unknown")
    source = row.get("source_type", "reference")
    stock_bonus = {"available": 0.22, "quote_needed": 0.05, "unknown": 0.0, "unavailable": -0.35}.get(stock, 0.0)
    source_bonus = {"confirmed": 0.35, "internal": 0.18, "reference": 0.08, "marketplace": 0.06, "estimate": -0.05}.get(source, 0.0)
    lead = int(float(row.get("lead_time_days") or 7))
    lead_bonus = max(-0.15, min(0.12, (7 - lead) * 0.025))
    supplier_rating = float(supplier.get("rating") or 4.0)
    rating_bonus = (supplier_rating - 4.0) * 0.05
    return round(confidence + stock_bonus + source_bonus + lead_bonus + _location_bonus(row, intake) + rating_bonus, 3)


def _market_band(offers: List[SupplierOffer]) -> Dict[str, Any]:
    values = sorted(float(o.price_usd) for o in offers if o.price_usd > 0)
    if not values:
        return {"min": 0, "p25": 0, "median": 0, "p75": 0, "max": 0, "sample_size": 0, "spread_percent": 0}
    median = statistics.median(values)
    if len(values) >= 4:
        q = statistics.quantiles(values, n=4, method="inclusive")
        p25, p75 = q[0], q[2]
    elif len(values) == 1:
        p25 = p75 = values[0]
    else:
        p25 = values[0]
        p75 = values[-1]
    spread = ((values[-1] - values[0]) / median * 100) if median else 0
    return {
        "min": round(values[0], 2),
        "p25": round(p25, 2),
        "median": round(median, 2),
        "p75": round(p75, 2),
        "max": round(values[-1], 2),
        "sample_size": len(values),
        "spread_percent": round(spread, 1),
    }


def _offer_flags(offer: SupplierOffer, band: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    median = float(band.get("median") or 0)
    p75 = float(band.get("p75") or 0)
    p25 = float(band.get("p25") or 0)
    if median > 0:
        if offer.price_usd > max(p75 * 1.35, median * 1.55):
            flags.append("precio alto fuera de banda")
        if offer.price_usd < min(p25 * 0.72 if p25 else median * 0.55, median * 0.58):
            flags.append("precio sospechosamente bajo")
    if offer.stock_status != "available":
        flags.append("stock no confirmado")
    if offer.source_type not in {"confirmed", "internal"} and offer.confidence < 0.68:
        flags.append("fuente débil")
    valid = _parse_date(offer.valid_until)
    if valid and valid < date.today():
        flags.append("vigencia vencida")
    return flags


def _priceguard_score(offer: SupplierOffer, band: Dict[str, Any], intake: ProjectIntake) -> Tuple[float, List[str]]:
    flags = _offer_flags(offer, band)
    source = SOURCE_WEIGHT.get(offer.source_type, 0.45)
    stock = STOCK_WEIGHT.get(offer.stock_status, 0.45)
    base_conf = max(0, min(1, offer.confidence))
    sample = min(1.0, float(band.get("sample_size") or 0) / 4.0)
    spread = float(band.get("spread_percent") or 0)
    spread_quality = max(0.35, 1.0 - min(spread, 160) / 230)
    location = 0.72 + min(0.25, _location_bonus({"city": offer.city}, intake) * 2)
    penalty = 0.0
    if "precio alto fuera de banda" in flags:
        penalty += 0.20
    if "precio sospechosamente bajo" in flags:
        penalty += 0.24
    if "stock no confirmado" in flags:
        penalty += 0.16
    if "fuente débil" in flags:
        penalty += 0.12
    if "vigencia vencida" in flags:
        penalty += 0.30
    score = (
        0.30 * base_conf +
        0.20 * source +
        0.18 * stock +
        0.12 * sample +
        0.10 * spread_quality +
        0.10 * location
    ) - penalty
    return round(max(0, min(1, score)) * 100, 1), flags


def _semaphore(score: float, flags: List[str], source_type: str) -> Tuple[str, str, str]:
    critical_flags = {"vigencia vencida", "precio sospechosamente bajo"}
    if score >= 76 and not flags and source_type in {"confirmed", "internal", "reference", "marketplace"}:
        return "verde", "alta", "Usar en cotización revisable; confirmar vigencia si la oferta supera 72 horas."
    if score >= 65 and not (critical_flags & set(flags)):
        return "amarillo", "media", "Usar como referencia; enviar RFQ si el proyecto es sensible a precio o plazo."
    return "rojo", "baja", "No cerrar precio con este valor. Enviar RFQ y pedir confirmación formal."


def _build_offer(row: Dict[str, str], intake: ProjectIntake, supplier: Dict[str, str]) -> SupplierOffer:
    return SupplierOffer(
        component_id=row["component_id"],
        category=row["category"],
        description=row["description"],
        brand=row["brand"],
        model=row["model"],
        supplier_id=row["supplier_id"],
        supplier_name=supplier.get("name", row["supplier_id"]),
        city=row["city"],
        price_usd=float(row["price_usd"]),
        stock_status=row["stock_status"],
        lead_time_days=int(float(row["lead_time_days"])),
        confidence=float(row["confidence"]),
        source_type=row["source_type"],
        valid_until=row["valid_until"],
        url=row.get("url", ""),
        notes=row.get("notes", ""),
        score=offer_score(row, intake, supplier),
    )


def find_offers(component_id: str, intake: ProjectIntake) -> List[SupplierOffer]:
    suppliers = load_suppliers()
    offers: List[SupplierOffer] = []
    for row in load_price_catalog():
        if row["component_id"] != component_id:
            continue
        supplier = suppliers.get(row["supplier_id"], {})
        offers.append(_build_offer(row, intake, supplier))
    band = _market_band(offers)
    enriched = []
    for offer in offers:
        pg, flags = _priceguard_score(offer, band, intake)
        # Store PriceGuard influence into score while keeping original supplier quality.
        offer.score = round((offer.score * 0.52) + (pg / 100 * 0.92), 3)
        enriched.append((offer, pg, flags))
    return [x[0] for x in sorted(enriched, key=lambda t: (t[1], t[0].score, -t[0].price_usd), reverse=True)]


def confidence_label(score: float, source_type: str) -> Tuple[str, str]:
    if source_type == "confirmed" or score >= 90:
        return "confirmado", "alta"
    if source_type in {"internal", "reference", "marketplace"} and score >= 78:
        return "referencial fuerte", "media-alta"
    if score >= 62:
        return "referencial", "media"
    return "estimado", "baja"


def _select_offer(offers: List[SupplierOffer], intake: ProjectIntake) -> Tuple[SupplierOffer | None, Dict[str, Any], float, List[str], bool]:
    if not offers:
        return None, _market_band([]), 0, ["sin ofertas en catálogo"], False
    band = _market_band(offers)
    scored = []
    for offer in offers:
        pg_score, flags = _priceguard_score(offer, band, intake)
        scored.append((pg_score, flags, offer))
    # Prefer green/high confidence and in-band. Avoid suspiciously low or expired even if cheap.
    scored.sort(key=lambda t: (t[0], t[2].score, -t[2].price_usd), reverse=True)
    selected_score, selected_flags, selected = scored[0]
    auto_corrected = False
    if selected_flags and ("precio sospechosamente bajo" in selected_flags or "vigencia vencida" in selected_flags):
        clean = [t for t in scored if "precio sospechosamente bajo" not in t[1] and "vigencia vencida" not in t[1]]
        if clean:
            selected_score, selected_flags, selected = clean[0]
            auto_corrected = True
    return selected, band, selected_score, selected_flags, auto_corrected


def decide_prices(requirements: Iterable[ComponentRequirement], intake: ProjectIntake) -> List[PriceDecision]:
    decisions: List[PriceDecision] = []
    for req in requirements:
        all_offers = find_offers(req.component_id, intake)
        compatible: List[SupplierOffer] = []
        fit_rejects: List[str] = []
        for offer in all_offers:
            ok, fflags = _fitlock_offer(req, offer, intake)
            if ok:
                compatible.append(offer)
            else:
                if len(fit_rejects) < 4:
                    fit_rejects.append(f"{offer.brand} {offer.model}: " + "; ".join(fflags))
        selected, band, pg_score, flags, auto_corrected = _select_offer(compatible, intake)
        if selected:
            color, risk_label, action = _semaphore(pg_score, flags, selected.source_type)
            ptype, label = confidence_label(pg_score, selected.source_type)
            unit_cost = selected.price_usd
            if color == "rojo" and band.get("median"):
                unit_cost = float(band["median"])
                auto_corrected = True
                ptype, label = "estimado corregido", "baja"
                action = "Precio fuera de confianza. Usar mediana temporal y enviar RFQ a varios proveedores."
            note = f"PriceGuard: {color.upper()} ({pg_score}%). {selected.brand} {selected.model}, {selected.supplier_name}, {selected.city}."
            if fit_rejects:
                note += " FitLock rechazó ofertas incompatibles: " + " | ".join(fit_rejects) + "."
            if flags:
                note += " Alertas: " + "; ".join(flags) + "."
            if auto_corrected:
                note += " Se aplicó autocorrección por banda de mercado."
            explanation = _price_explanation(req, selected, band, color)
            anomaly_flags = flags + (["FitLock rechazó ofertas incompatibles"] if fit_rejects else [])
        else:
            color, label, action = "rojo", "baja", "FitLock bloqueó el precio: no hay oferta técnicamente compatible. Enviar RFQ con especificación real."
            ptype = "RFQ obligatorio / estimación presupuestaria"
            unit_cost = _fitlock_estimate(req, intake)
            pg_score = 12.0 if fit_rejects else 25.0
            flags = ["FitLock: sin oferta compatible en catálogo piloto"] + fit_rejects
            # Band based on rejected market if available; otherwise conservative RFQ placeholder band.
            band = _market_band(all_offers) if all_offers else {
                "min": round(unit_cost * 0.75, 2), "p25": round(unit_cost * 0.9, 2), "median": round(unit_cost, 2),
                "p75": round(unit_cost * 1.2, 2), "max": round(unit_cost * 1.45, 2), "sample_size": 0, "spread_percent": 0,
            }
            note = "FitLock: ningún producto del catálogo piloto calza con HP/FLA/tensión/especificación. Se muestra solo una estimación presupuestaria y se exige RFQ."
            if fit_rejects:
                note += " Rechazos: " + " | ".join(fit_rejects) + "."
            explanation = "FitLock bloqueó el uso comercial de catálogo: el precio no es cerrable hasta que un proveedor confirme modelo compatible, stock, vigencia y especificación."
            auto_corrected = False
            anomaly_flags = flags
        decisions.append(PriceDecision(
            component_id=req.component_id,
            selected_offer=selected,
            offers=all_offers[:5],
            qty=req.qty,
            unit_cost=round(unit_cost, 2),
            extended_cost=round(unit_cost * req.qty, 2),
            price_type=ptype,
            confidence_label=label,
            decision_note=note,
            semaphore_color=color,
            priceguard_score=pg_score,
            market_band=band,
            anomaly_flags=anomaly_flags,
            action_required=action,
            auto_corrected=auto_corrected,
            rfq_priority="alta" if color == "rojo" else ("media" if color == "amarillo" else "baja"),
            price_explanation=explanation,
        ))
    return decisions


def _price_explanation(req: ComponentRequirement, offer: SupplierOffer, band: Dict[str, Any], color: str) -> str:
    return (
        f"{req.item}: se compara precio unitario contra banda catálogo "
        f"min {band.get('min')} / mediana {band.get('median')} / max {band.get('max')} USD. "
        f"Semáforo {color}. Importa porque un precio bajo puede significar componente incompatible o sin garantía, "
        f"y uno alto puede destruir margen en cotizaciones que quizá no se ganen."
    )


def estimate_fallback(req: ComponentRequirement) -> float:
    text = (req.item + " " + req.spec).lower()
    if "variador" in text or "vfd" in text:
        return 900.0
    if "soft starter" in text or "suave" in text:
        return 620.0
    if "gabinete" in text:
        return 140.0
    if "contactor" in text:
        return 65.0
    if "breaker" in text or "mccb" in text:
        return 95.0
    if "transformador" in text:
        return 130.0
    if "cable" in text or "conductor" in text:
        return 120.0
    if "mano" in text or "jornada" in text:
        return 200.0
    return 35.0



def _all_offer_anomaly_audit(decisions: List[PriceDecision]) -> Dict[str, Any]:
    """Audit all candidate offers, not only the selected line.

    This lets the product prove that it is rejecting bad prices instead of silently
    using the cheapest value. It is especially important when quotes can reach
    thousands of dollars.
    """
    total_offers = 0
    suspicious_low = 0
    suspicious_high = 0
    expired = 0
    weak_source = 0
    blocked_examples: List[Dict[str, Any]] = []
    for d in decisions:
        band = d.market_band or {}
        median = float(band.get("median") or 0)
        p25 = float(band.get("p25") or 0)
        p75 = float(band.get("p75") or 0)
        for offer in d.offers:
            total_offers += 1
            flags = _offer_flags(offer, band)
            if "precio sospechosamente bajo" in flags:
                suspicious_low += 1
            if "precio alto fuera de banda" in flags:
                suspicious_high += 1
            if "vigencia vencida" in flags:
                expired += 1
            if "fuente débil" in flags:
                weak_source += 1
            if flags and len(blocked_examples) < 8:
                blocked_examples.append({
                    "component_id": d.component_id,
                    "supplier": offer.supplier_name,
                    "brand_model": f"{offer.brand} {offer.model}",
                    "price_usd": offer.price_usd,
                    "market_median": median,
                    "flags": flags,
                })
    return {
        "total_candidate_offers": total_offers,
        "suspicious_low_rejected": suspicious_low,
        "suspicious_high_flagged": suspicious_high,
        "expired_rejected": expired,
        "weak_source_flagged": weak_source,
        "blocked_examples": blocked_examples,
        "policy": "El motor audita también ofertas no seleccionadas para no caer en precio barato falso ni precio inflado fuera de banda.",
    }



def _mathtrust_model(decisions: List[PriceDecision]) -> Dict[str, Any]:
    """Mathematical reliability layer for price decisions.

    This is not a magic oracle. It quantifies when a price can be trusted and when it
    must be treated as an order-of-magnitude placeholder. It combines:
    - FitLock compatibility: HP/FLA/voltage/specification must fit.
    - Robust market band: median/IQR instead of cheapest value.
    - Source/stock/vigency weighting: confirmed supplier beats weak references.
    - RFQ consensus rule: red items remain blocked until supplier confirmation.
    """
    n = max(1, len(decisions))
    fit_blocked = sum(1 for d in decisions if d.semaphore_color == "rojo" and any("FitLock" in str(f) for f in (d.anomaly_flags or [])))
    red = sum(1 for d in decisions if d.semaphore_color == "rojo")
    yellow = sum(1 for d in decisions if d.semaphore_color == "amarillo")
    green = sum(1 for d in decisions if d.semaphore_color == "verde")
    depth_scores = [min(1.0, float(d.market_band.get("sample_size") or 0) / 4.0) for d in decisions]
    dispersion_scores = []
    for d in decisions:
        spread = float(d.market_band.get("spread_percent") or 0)
        dispersion_scores.append(max(0.15, 1.0 - min(spread, 180.0) / 220.0))
    priceguard_avg = sum(float(d.priceguard_score or 0) for d in decisions) / n
    fit_score = 100.0 * (1.0 - fit_blocked / n)
    depth_score = 100.0 * (sum(depth_scores) / n)
    dispersion_score = 100.0 * (sum(dispersion_scores) / n)
    source_score = 100.0 * (green + yellow * 0.55) / n
    score = round(0.36 * fit_score + 0.26 * priceguard_avg + 0.16 * depth_score + 0.12 * dispersion_score + 0.10 * source_score, 1)
    if fit_blocked:
        verdict = "BLOQUEADO: FitLock tiene componentes sin ajuste técnico"
    elif score >= 88 and red == 0:
        verdict = "Fuerte para propuesta revisable"
    elif score >= 72 and red <= 1:
        verdict = "Revisable con RFQ selectivo"
    else:
        verdict = "Débil: solo borrador interno"
    return {
        "score_percent": score,
        "verdict": verdict,
        "fit_score_percent": round(fit_score, 1),
        "priceguard_avg_percent": round(priceguard_avg, 1),
        "catalog_depth_percent": round(depth_score, 1),
        "dispersion_score_percent": round(dispersion_score, 1),
        "source_score_percent": round(source_score, 1),
        "fitlock_blocked_count": fit_blocked,
        "green_count": green,
        "yellow_count": yellow,
        "red_count": red,
        "formula": "MathTrust = 0.36*FitLock + 0.26*PriceGuard + 0.16*profundidad catálogo + 0.12*dispersión robusta + 0.10*fuente/stock",
        "robust_policy": "No se usa el precio más barato: se usa mediana/IQR, pesos por fuente/stock/vigencia y bloqueo por compatibilidad. Si falta oferta compatible, el valor es solo orden de magnitud y debe ir a RFQ.",
    }

def summarize_market(decisions: List[PriceDecision]) -> Dict[str, Any]:
    total = sum(d.extended_cost for d in decisions)
    covered = sum(1 for d in decisions if d.selected_offer)
    green = sum(1 for d in decisions if d.semaphore_color == "verde")
    yellow = sum(1 for d in decisions if d.semaphore_color == "amarillo")
    red = sum(1 for d in decisions if d.semaphore_color == "rojo")
    high_conf = sum(1 for d in decisions if d.confidence_label in {"alta", "media-alta"})
    quote_needed = [d for d in decisions if d.semaphore_color == "rojo" or not d.selected_offer or (d.selected_offer and d.selected_offer.stock_status != "available") or d.confidence_label == "baja"]
    outliers = [d for d in decisions if d.anomaly_flags]
    fitlock_blocked = [d for d in decisions if d.semaphore_color == "rojo" and any("FitLock" in f for f in (d.anomaly_flags or []))]
    suppliers = sorted({d.selected_offer.supplier_name for d in decisions if d.selected_offer})
    pg_score = round(sum(d.priceguard_score for d in decisions) / max(1, len(decisions)), 1)
    catalog_depth = round(sum(min(1, (d.market_band.get("sample_size") or 0) / 3) for d in decisions) / max(1, len(decisions)) * 100, 1)
    mathtrust = _mathtrust_model(decisions)
    return {
        "materials_cost": round(total, 2),
        "items_with_price": covered,
        "total_items": len(decisions),
        "coverage_percent": round(covered / max(1, len(decisions)) * 100, 1),
        "high_confidence_items": high_conf,
        "needs_rfq_count": len(quote_needed),
        "suppliers_used": suppliers,
        "quote_needed_components": [d.component_id for d in quote_needed],
        "priceguard_score_percent": pg_score,
        "green_count": green,
        "yellow_count": yellow,
        "red_count": red,
        "outlier_count": len(outliers),
        "fitlock_blocked_count": len(fitlock_blocked),
        "fitlock_blocked_components": [d.component_id for d in fitlock_blocked],
        "fitlock_status": "OK" if not fitlock_blocked else "BLOQUEADO: componentes sin compatibilidad técnica confirmada",
        "auto_corrected_count": sum(1 for d in decisions if d.auto_corrected),
        "catalog_depth_score_percent": catalog_depth,
        "candidate_offer_audit": _all_offer_anomaly_audit(decisions),
        "locked_price_count": sum(1 for d in decisions if d.semaphore_color == "verde" and d.confidence_label in {"alta", "media-alta"}),
        "referential_price_count": sum(1 for d in decisions if d.semaphore_color == "amarillo"),
        "blocked_price_count": sum(1 for d in decisions if d.semaphore_color == "rojo"),
        "priceguard_verdict": "BLOQUEADO POR FITLOCK" if fitlock_blocked else ("Fuerte para piloto" if pg_score >= 85 and red == 0 else ("Revisable con RFQ" if pg_score >= 70 else "Débil: no enviar sin confirmar")),
        "mathtrust": mathtrust,
        "mathtrust_score_percent": mathtrust["score_percent"],
        "mathtrust_verdict": mathtrust["verdict"],
        "catalog_scope": "Catálogo piloto ampliado: fuerza, control, seguridad, VFD, soft starter, taller, cables y consumibles. No sustituye precios reales confirmados.",
        "market_ledger": ledger_overview(decisions, decisions[0].selected_offer and getattr(decisions[0].selected_offer, "_intake", None) or ProjectIntake()) if False else {"note": "Ledger overview attached by MarketVision in advisor layer."},
        "confidence_policy": {
            "precio_confirmado": "Proveedor/stock/vigencia confirmados o fuente interna validada; se puede usar en propuesta revisable.",
            "precio_referencial": "Sirve para armar presupuesto, pero se debe confirmar si afecta margen o plazo.",
            "precio_bloqueado": "No usar para cerrar propuesta; enviar RFQ y esperar respuesta.",
        },
        "semaphore_method": "Verde = precio usable en cotización revisable; amarillo = referencia con RFQ recomendado; rojo = no cerrar precio, autocorregir/consultar proveedor.",
        "truth_status": "Precio 100% cerrado solo cuando proveedor confirma modelo, stock, vigencia y condiciones. Sin eso, se muestra como referencial o bloqueado.",
    }


def generate_rfq_message(requirements: Iterable[ComponentRequirement], decisions: Iterable[PriceDecision], intake: ProjectIntake) -> str:
    decision_map = {d.component_id: d for d in decisions}
    lines = [
        "Buenos días, necesito cotizar materiales para un proyecto de control industrial.",
        "",
        f"Proyecto: {intake.project_name}",
        f"Ubicación de entrega/referencia: {intake.location_city}, {intake.location_province}, {intake.country}",
        "",
        "Favor confirmar precio unitario, marca disponible, modelo exacto, stock, tiempo de entrega, garantía, forma de pago y vigencia de oferta:",
        "",
    ]
    n = 1
    for req in requirements:
        d = decision_map.get(req.component_id)
        need = d is None or d.semaphore_color != "verde" or d.confidence_label == "baja"
        if need:
            priority = d.rfq_priority.upper() if d else "ALTA"
            flags = "; ".join(d.anomaly_flags) if d and d.anomaly_flags else "confirmación de mercado"
            lines.append(f"{n}. [{priority}] {req.item} — Cantidad: {req.qty:g} {req.unit} — Especificación: {req.spec} — Motivo: {flags}")
            n += 1
    if n == 1:
        lines.append("1. Confirmar disponibilidad, vigencia y precio final de todos los materiales del BOM adjunto para cerrar propuesta.")
    lines += [
        "",
        "También indicar alternativas equivalentes de calidad industrial y si pueden emitir proforma.",
        "Gracias.",
    ]
    return "\n".join(lines)


def priceguard_methodology() -> Dict[str, Any]:
    return {
        "name": "PriceGuard 16 + MarketVision + OptionTrust + MathTrust + FitLock",
        "goal": "Evitar cotizaciones débiles, precios exagerados, precios incompatibles, BOM incoherente con la arquitectura y falsas certezas antes de presupuestar trabajos de miles de dólares.",
        "inputs": ["catálogo interno", "Market Ledger histórico", "fuente de precio", "stock", "vigencia", "proveedor", "banda robusta mediana/IQR", "ubicación", "historial/RFQ", "auditoría de outliers", "estado de credenciales API", "búsqueda web/API cuando esté activada"],
        "semaforos": {
            "verde": "usable en cotización revisable; aun así debe verificarse si el precio es sensible o la oferta vence pronto",
            "amarillo": "referencial; se recomienda RFQ o confirmación antes de enviar propuesta firme",
            "rojo": "no cerrar precio; se autocorrige con mediana temporal o se exige RFQ",
        },
        "anti_garbage_rules": [
            "No escoger automáticamente el precio más barato.",
            "No usar precio sospechosamente bajo como definitivo.",
            "No fingir mercado real si las APIs están sin credenciales.",
            "Usar Market Ledger por mediana/IQR para no perderse cuando no exista precio vivo.",
            "Mostrar catálogo piloto separado de mercado vivo.",
            "Auditar todas las ofertas candidatas, no solo la seleccionada.",
            "Forzar coherencia: solución recomendada, BOM, RFQ, PDF y propuesta deben usar la misma arquitectura.",
            "FitLock: bloquear precios si breaker/VFD/reactor/cable/protecciones no calzan con HP, FLA y tensión.",
            "Separar precio estimado, referencial, referencial fuerte y confirmado.",
            "Bloquear salida fuerte cuando hay demasiados rojos o stock sin confirmar.",
        ],
    }
