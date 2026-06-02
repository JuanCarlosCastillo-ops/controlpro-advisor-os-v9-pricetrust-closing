"""Conector Mercado Libre listo para credenciales reales.

Default seguro: búsqueda pública referencial opcional. La app no convierte publicaciones en precio cerrado sin FitLock/PriceGuard/RFQ.
"""
from __future__ import annotations

import os
import httpx

BASE_URL = "https://api.mercadolibre.com"


def is_enabled() -> bool:
    return os.getenv("MELI_ENABLED", "false").lower() in {"1", "true", "yes", "on"} or os.getenv("MELI_PUBLIC_SEARCH_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


async def search_items(query: str, site_id: str | None = None, limit: int | None = None) -> dict:
    if not is_enabled():
        return {"enabled": False, "results": [], "note": "Mercado Libre desactivado. Activar MELI_PUBLIC_SEARCH_ENABLED=true o MELI_ENABLED=true."}
    site = site_id or os.getenv("MELI_SITE_ID", "MEC")
    max_results = limit or int(os.getenv("MELI_MAX_RESULTS", "8"))
    token = os.getenv("MELI_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{BASE_URL}/sites/{site}/search", params={"q": query, "limit": max_results}, headers=headers)
        r.raise_for_status()
        data = r.json()
    items = []
    for it in data.get("results", [])[:max_results]:
        items.append({
            "title": it.get("title"),
            "price": it.get("price"),
            "currency_id": it.get("currency_id"),
            "condition": it.get("condition"),
            "permalink": it.get("permalink"),
            "seller_id": (it.get("seller") or {}).get("id"),
            "available_quantity": it.get("available_quantity"),
        })
    return {"enabled": True, "site_id": site, "query": query, "items": items, "truth_rule": "Publicaciones online son referencia: antes de cotizar se debe verificar que HP/A/V/modelo calcen y que exista stock/vigencia."}
