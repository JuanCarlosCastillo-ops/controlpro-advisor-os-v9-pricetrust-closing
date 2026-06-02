"""Conector Google Places listo para ubicar proveedores.

No confirma precios; solo identifica proveedores potenciales. Requiere FieldMask.
"""
from __future__ import annotations

import os
import httpx

PLACES_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"


def is_enabled() -> bool:
    return os.getenv("GOOGLE_PLACES_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


async def search_suppliers(text_query: str, location_bias: dict | None = None) -> dict:
    if not is_enabled():
        return {"enabled": False, "places": [], "note": "Google Places desactivado. Activar GOOGLE_PLACES_ENABLED=true y configurar GOOGLE_PLACES_API_KEY."}
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise RuntimeError("Falta GOOGLE_PLACES_API_KEY")
    body = {"textQuery": text_query}
    if location_bias:
        body["locationBias"] = location_bias
    field_mask = os.getenv("GOOGLE_PLACES_FIELD_MASK") or "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.rating,places.websiteUri"
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": field_mask}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(PLACES_TEXT_URL, json=body, headers=headers)
        r.raise_for_status()
        data = r.json()
    return {"enabled": True, "query": text_query, "raw": data}
