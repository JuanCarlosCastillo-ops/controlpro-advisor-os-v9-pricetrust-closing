# TEOD Industrial AI Hub V1 — Vertical Slice Lock

## Objetivo
Cerrar un producto pequeño y completo antes de ampliar alcance. V1 convierte **activo → incidencia → análisis de 5 agentes → orden de trabajo → aprobación humana → auditoría** en un flujo usable.

## Capas
1. **Service Desk**: registro estructurado de incidencias y mediciones.
2. **Active Watch ready**: eventos append-only y modelo preparado para entradas de PLC/SCADA/Modbus.
3. **Event Agents**: triage, seguridad, diagnóstico, planificación y supervisor.
4. **Copilot**: hipótesis y verificaciones, sin presentar diagnóstico como certeza.
5. **Asset Intelligence**: ficha técnica + historial operativo.

## Regla de seguridad
La IA no autoriza puentes de protección, cambios de ajuste ni energización. Toda orden se crea en `pending_approval` y requiere aprobación humana identificada. Cada decisión genera un evento de auditoría.

## Persistencia
V1 usa SQLite + WAL para que funcione sin servicios externos. `TEOD_HUB_DB_PATH` permite mover el archivo a volumen persistente. La capa `OpsStore` aísla persistencia para migrar a Postgres/Supabase sin reescribir agentes ni API.

## Seguridad de API
Si se define `TEOD_HUB_API_KEY`, las rutas operativas requieren `X-TEOD-API-Key`. Para un despliegue multiempresa se debe reemplazar este control de piloto por identidad real + RBAC + RLS.

## Alcance bloqueado de V1
Incluido: activos, incidencias, 5 agentes deterministas, órdenes, aprobación, auditoría, dashboard y caso demo industrial.

Fuera de V1: ejecución automática sobre PLC, escritura Modbus, compras automáticas, WhatsApp productivo, CMMS externo, visión avanzada, predicción ML y multi-tenant comercial. Esas capacidades solo entran después de que el flujo V1 sea usado de extremo a extremo.

## Endpoints
- `GET /ops`
- `GET /api/ops/health`
- `GET /api/ops/dashboard`
- `GET|POST /api/ops/assets`
- `GET|POST /api/ops/incidents`
- `POST /api/ops/incidents/{id}/analyze`
- `GET /api/ops/work-orders`
- `POST /api/ops/work-orders/{id}/approve`
- `GET /api/ops/audit`
- `POST /api/ops/demo/seed`

## DoD
V1 se considera cerrada cuando CI pasa, la UI abre, el seed crea el caso, una incidencia genera cinco `agent_runs`, existe exactamente una orden activa por incidente, la orden no puede ejecutarse sin aprobación y el ledger registra cada transición relevante.
