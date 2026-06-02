"""Conector Mercado Libre listo para credenciales reales.

Default seguro: desactivado. La app no inventa precios en vivo si MELI_ENABLED=false.
"""
from __future__ import annotations

import os
import httpx

BASE_URL = "https://api.mercadolibre.com"


def is_enabled() -> bool:
    return os.getenv("MELI_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


async def search_items(query: str, site_id: str | None = None, limit: int | None = None) -> dict:
    if not is_enabled():
        return {"enabled": False, "results": [], "note": "Mercado Libre desactivado. Activar MELI_ENABLED=true y configurar .env."}
    site = site_id or os.getenv("MELI_SITE_ID", "MEC")
    max_results = limit or int(os.getenv("MELI_MAX_RESULTS", "8"))
    token = os.getenv("MELI_ACCESS_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{BASE_URL}/sites/{site}/search", params={"q": query, "limit": max_results}, headers=headers)
        r.raise_for_status()
        data = r.json()
    return {"enabled": True, "site_id": site, "query": query, "raw": data}
