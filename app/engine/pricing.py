from __future__ import annotations

import csv
import json
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
        offers = find_offers(req.component_id, intake)
        selected, band, pg_score, flags, auto_corrected = _select_offer(offers, intake)
        if selected:
            color, risk_label, action = _semaphore(pg_score, flags, selected.source_type)
            ptype, label = confidence_label(pg_score, selected.source_type)
            unit_cost = selected.price_usd
            if color == "rojo" and band.get("median"):
                # PriceGuard does not pretend certainty: it uses robust median as temporary budget reference and forces RFQ.
                unit_cost = float(band["median"])
                auto_corrected = True
                ptype, label = "estimado corregido", "baja"
                action = "Precio fuera de confianza. Usar mediana temporal y enviar RFQ a varios proveedores."
            note = f"PriceGuard: {color.upper()} ({pg_score}%). {selected.brand} {selected.model}, {selected.supplier_name}, {selected.city}."
            if flags:
                note += " Alertas: " + "; ".join(flags) + "."
            if auto_corrected:
                note += " Se aplicó autocorrección por banda de mercado."
            explanation = _price_explanation(req, selected, band, color)
        else:
            color, label, action = "rojo", "baja", "Sin precio confiable: enviar RFQ y usar rango de contingencia."
            ptype = "estimado"
            unit_cost = estimate_fallback(req)
            pg_score = 28.0
            flags = ["sin ofertas en catálogo"]
            band = {"min": unit_cost * 0.75, "p25": unit_cost * 0.9, "median": unit_cost, "p75": unit_cost * 1.15, "max": unit_cost * 1.35, "sample_size": 0, "spread_percent": 0}
            note = "Sin precio en catálogo; se usa estimación conservadora y se debe enviar RFQ."
            explanation = "Estimación temporal sin proveedor. No debe usarse como precio final."
        decisions.append(PriceDecision(
            component_id=req.component_id,
            selected_offer=selected,
            offers=offers[:5],
            qty=req.qty,
            unit_cost=round(unit_cost, 2),
            extended_cost=round(unit_cost * req.qty, 2),
            price_type=ptype,
            confidence_label=label,
            decision_note=note,
            semaphore_color=color,
            priceguard_score=pg_score,
            market_band=band,
            anomaly_flags=flags,
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

def summarize_market(decisions: List[PriceDecision]) -> Dict[str, Any]:
    total = sum(d.extended_cost for d in decisions)
    covered = sum(1 for d in decisions if d.selected_offer)
    green = sum(1 for d in decisions if d.semaphore_color == "verde")
    yellow = sum(1 for d in decisions if d.semaphore_color == "amarillo")
    red = sum(1 for d in decisions if d.semaphore_color == "rojo")
    high_conf = sum(1 for d in decisions if d.confidence_label in {"alta", "media-alta"})
    quote_needed = [d for d in decisions if d.semaphore_color == "rojo" or not d.selected_offer or (d.selected_offer and d.selected_offer.stock_status != "available") or d.confidence_label == "baja"]
    outliers = [d for d in decisions if d.anomaly_flags]
    suppliers = sorted({d.selected_offer.supplier_name for d in decisions if d.selected_offer})
    pg_score = round(sum(d.priceguard_score for d in decisions) / max(1, len(decisions)), 1)
    catalog_depth = round(sum(min(1, (d.market_band.get("sample_size") or 0) / 3) for d in decisions) / max(1, len(decisions)) * 100, 1)
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
        "auto_corrected_count": sum(1 for d in decisions if d.auto_corrected),
        "catalog_depth_score_percent": catalog_depth,
        "candidate_offer_audit": _all_offer_anomaly_audit(decisions),
        "locked_price_count": sum(1 for d in decisions if d.semaphore_color == "verde" and d.confidence_label in {"alta", "media-alta"}),
        "referential_price_count": sum(1 for d in decisions if d.semaphore_color == "amarillo"),
        "blocked_price_count": sum(1 for d in decisions if d.semaphore_color == "rojo"),
        "priceguard_verdict": "Fuerte para piloto" if pg_score >= 85 and red == 0 else ("Revisable con RFQ" if pg_score >= 70 else "Débil: no enviar sin confirmar"),
        "catalog_scope": "Catálogo piloto ampliado: fuerza, control, seguridad, VFD, soft starter, taller, cables y consumibles. No sustituye precios reales confirmados.",
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
        "name": "PriceGuard 11",
        "goal": "Evitar cotizaciones débiles, precios exagerados, precios incompatibles, BOM incoherente con la arquitectura y falsas certezas antes de presupuestar trabajos de miles de dólares.",
        "inputs": ["catálogo interno", "fuente de precio", "stock", "vigencia", "proveedor", "banda de mercado", "ubicación", "historial/RFQ", "auditoría de outliers", "estado de credenciales API"],
        "semaforos": {
            "verde": "usable en cotización revisable; aun así debe verificarse si el precio es sensible o la oferta vence pronto",
            "amarillo": "referencial; se recomienda RFQ o confirmación antes de enviar propuesta firme",
            "rojo": "no cerrar precio; se autocorrige con mediana temporal o se exige RFQ",
        },
        "anti_garbage_rules": [
            "No escoger automáticamente el precio más barato.",
            "No usar precio sospechosamente bajo como definitivo.",
            "No fingir mercado real si las APIs están sin credenciales.",
            "Mostrar catálogo piloto separado de mercado vivo.",
            "Auditar todas las ofertas candidatas, no solo la seleccionada.",
            "Forzar coherencia: solución recomendada, BOM, RFQ, PDF y propuesta deben usar la misma arquitectura.",
            "Separar precio estimado, referencial, referencial fuerte y confirmado.",
            "Bloquear salida fuerte cuando hay demasiados rojos o stock sin confirmar.",
        ],
    }
