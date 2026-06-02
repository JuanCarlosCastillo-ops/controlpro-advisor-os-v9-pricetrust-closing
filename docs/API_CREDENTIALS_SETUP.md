# ControlPro Advisor OS V9 — Activación de credenciales reales

Esta versión queda lista para activar APIs reales sin tocar el núcleo del producto. Por seguridad, la app funciona por defecto en modo **offline/catálogo interno** y no finge precios en vivo.

## 1. Archivo `.env`

1. Copiar `.env.example` como `.env`.
2. Completar credenciales.
3. No subir `.env` a GitHub.
4. Reiniciar Uvicorn/Render después de cambiar variables.

```bash
cp .env.example .env
```

En Windows PowerShell:

```powershell
copy .env.example .env
```

## 2. Mercado Libre

Uso previsto: búsqueda referencial de productos/precios.

Variables:

```env
MELI_ENABLED=true
MELI_SITE_ID=MEC
MELI_ACCESS_TOKEN=
MELI_MAX_RESULTS=8
```

Notas:

- `MEC` corresponde al sitio Ecuador en el flujo de Mercado Libre.
- Sin token, algunas búsquedas públicas pueden funcionar; para producción conviene configurar token según cuenta/app.
- Todo precio de marketplace entra como **referencial**, no como precio confirmado.

## 3. Google Places

Uso previsto: encontrar proveedores cercanos.

Variables:

```env
GOOGLE_PLACES_ENABLED=true
GOOGLE_PLACES_API_KEY=TU_API_KEY
GOOGLE_PLACES_DEFAULT_COUNTRY=Ecuador
GOOGLE_PLACES_FIELD_MASK=places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.rating,places.websiteUri
```

Regla: Google Places encuentra proveedores, pero **no confirma precio ni stock**. Para precio cerrado se usa RFQ o catálogo confirmado.

## 4. WhatsApp Cloud API

Uso previsto: envío de RFQ a proveedores aprobados.

Variables:

```env
WHATSAPP_ENABLED=true
WHATSAPP_API_VERSION=v20.0
WHATSAPP_TOKEN=TU_TOKEN
WHATSAPP_PHONE_NUMBER_ID=TU_PHONE_NUMBER_ID
WHATSAPP_DEFAULT_COUNTRY_CODE=593
```

Regla: el sistema debe mostrar el mensaje y requerir acción explícita del usuario antes de enviar. No spam, no envío masivo no solicitado.

## 5. SMTP

Uso previsto: envío de RFQ por correo.

```env
SMTP_ENABLED=true
SMTP_HOST=smtp.tudominio.com
SMTP_PORT=587
SMTP_USER=usuario
SMTP_PASSWORD=password
SMTP_FROM_EMAIL=cotizaciones@tudominio.com
SMTP_FROM_NAME=ControlPro Advisor OS
```

## 6. Verificar estado dentro de la app

La app expone:

```text
GET /api/integrations/status
GET /api/integrations/env-template
```

El panel **APIs** muestra qué servicio está apagado, activado con faltantes o listo.

## 7. Reglas de verdad

- Precio estimado: solo sirve para borrador.
- Precio referencial: puede ir a propuesta con advertencia/vigencia corta.
- Precio confirmado: proveedor, stock y vigencia validados.
- Ninguna API libera construcción; solo mejora cotización.
