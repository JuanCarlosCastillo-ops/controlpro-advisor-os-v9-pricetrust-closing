"""Conector WhatsApp Cloud API listo para RFQ.

El envío automático requiere credenciales reales y acción explícita del usuario.
"""
from __future__ import annotations

import os
import httpx


def is_enabled() -> bool:
    return os.getenv("WHATSAPP_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


async def send_text(to_phone: str, message: str) -> dict:
    if not is_enabled():
        return {"enabled": False, "sent": False, "note": "WhatsApp desactivado. Copiar RFQ manual o configurar WHATSAPP_ENABLED=true."}
    token = os.getenv("WHATSAPP_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    api_version = os.getenv("WHATSAPP_API_VERSION", "v20.0")
    if not token or not phone_number_id:
        raise RuntimeError("Faltan WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID")
    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()
