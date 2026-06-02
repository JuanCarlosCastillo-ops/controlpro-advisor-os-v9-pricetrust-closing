from __future__ import annotations

import os
from typing import Any, Dict, List


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _present(name: str) -> bool:
    value = os.getenv(name)
    return bool(value and value.strip() and not value.strip().startswith("REEMPLAZAR"))


def integration_status() -> Dict[str, Any]:
    services: List[Dict[str, Any]] = []

    def add(key: str, name: str, enabled_env: str, required: List[str], optional: List[str] | None = None, note: str = ""):
        enabled = _enabled(enabled_env)
        missing = [v for v in required if not _present(v)] if enabled else required
        configured = enabled and not missing
        services.append({
            "key": key,
            "name": name,
            "enabled": enabled,
            "configured": configured,
            "missing": missing,
            "required_env": required,
            "optional_env": optional or [],
            "status": "activo/configurado" if configured else ("activado con faltantes" if enabled else "desactivado"),
            "note": note,
        })

    add(
        "mercadolibre",
        "Mercado Libre Search",
        "MELI_ENABLED",
        ["MELI_SITE_ID"],
        ["MELI_ACCESS_TOKEN"],
        "Busca precios referenciales. La selección final exige verificar especificación, stock y vigencia.",
    )
    add(
        "google_places",
        "Google Places Suppliers",
        "GOOGLE_PLACES_ENABLED",
        ["GOOGLE_PLACES_API_KEY"],
        ["GOOGLE_PLACES_DEFAULT_COUNTRY"],
        "Encuentra proveedores cercanos; no confirma precios.",
    )
    add(
        "whatsapp_cloud",
        "WhatsApp Cloud API RFQ",
        "WHATSAPP_ENABLED",
        ["WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
        ["WHATSAPP_API_VERSION", "WHATSAPP_DEFAULT_COUNTRY_CODE"],
        "Envía RFQ solo con aprobación del usuario y consentimiento del destinatario.",
    )
    add(
        "smtp_email",
        "SMTP RFQ Email",
        "SMTP_ENABLED",
        ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM_EMAIL"],
        ["SMTP_FROM_NAME"],
        "Envío de RFQ por correo cuando no se use WhatsApp.",
    )
    configured = sum(1 for s in services if s["configured"])
    enabled = sum(1 for s in services if s["enabled"])
    return {
        "release": "V13 FitLock Pro",
        "configured_count": configured,
        "enabled_count": enabled,
        "services": services,
        "safe_default": "Sin credenciales reales la app usa catálogo interno, precios por confianza y RFQ manual. No finge mercado en vivo.",
    }


def env_template() -> str:
    return """# ControlPro Advisor OS V13 - credenciales reales
# Copiar este archivo como .env y reemplazar valores.
# Nunca subir .env a GitHub.

APP_ENV=pilot
CONTROLPRO_ENABLE_LIVE_MARKET=false
CONTROLPRO_DEFAULT_COUNTRY=Ecuador
CONTROLPRO_DEFAULT_CURRENCY=USD

# Mercado Libre Ecuador / búsquedas referenciales
MELI_ENABLED=false
MELI_SITE_ID=MEC
MELI_ACCESS_TOKEN=
MELI_MAX_RESULTS=8

# Google Places / proveedores cercanos
GOOGLE_PLACES_ENABLED=false
GOOGLE_PLACES_API_KEY=
GOOGLE_PLACES_DEFAULT_COUNTRY=Ecuador
GOOGLE_PLACES_FIELD_MASK=places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.rating,places.websiteUri

# WhatsApp Cloud API / RFQ
WHATSAPP_ENABLED=false
WHATSAPP_API_VERSION=v20.0
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_DEFAULT_COUNTRY_CODE=593

# Correo SMTP / RFQ
SMTP_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=ControlPro Advisor OS

# Reglas de seguridad comercial
CONTROLPRO_BLOCK_BUILD_WITHOUT_SCCR=true
CONTROLPRO_REQUIRE_HUMAN_APPROVAL=true
CONTROLPRO_RFQ_CONFIRMATION_REQUIRED=true

# PriceGuard / semáforo de precios
CONTROLPRO_PRICEGUARD_GREEN_MIN=76
CONTROLPRO_PRICEGUARD_YELLOW_MIN=62
CONTROLPRO_PRICEGUARD_MAX_RED_FOR_PILOT_QUOTE=3
CONTROLPRO_REQUIRE_RFQ_FOR_RED_PRICES=true
CONTROLPRO_SHOW_CATALOG_VS_LIVE_MARKET=true
"""
