# Layered UX + Lead Capture - V12

La app ya no debe abrumar al cliente con todo el sistema interno.

## Capas visibles
1. Cotizar rápido: registro, plantillas y datos mínimos.
2. Evidencia y CAD: fotos, visual premium, unifilar, ladder y taller.
3. Materiales y mercado: BOM, PriceGuard, RFQ y presupuesto.
4. Entregables: validación, estadísticas y exportables.
5. Admin interno: APIs, credenciales y variables `.env`.

## Registro piloto
Incluye formulario de nombre, correo, WhatsApp, empresa y rol. En piloto se guarda localmente y se envía a `/api/leads`; para producción se recomienda conectar CRM, base de datos o Google Sheets.
