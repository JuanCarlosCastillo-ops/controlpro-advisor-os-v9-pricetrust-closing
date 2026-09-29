# ControlPro Advisor OS V16 - MarketVision Pro

Copiloto de cotizacion industrial en espanol para motores, bombas, compresores, guinches, bandas y tableros.


## TEOD Industrial AI Hub V1

Esta rama agrega un **vertical slice operacional cerrado** encima del motor técnico existente. No intenta resolver toda la industria en V1: cierra un flujo completo y auditable antes de ampliar alcance.

**Flujo:** activo → incidencia → 5 agentes → orden de trabajo → aprobación humana → auditoría.

- UI operacional: `/ops`
- Activos industriales y ficha técnica.
- Incidencias con mediciones y severidad.
- Cinco agentes deterministas: triage, Safety Guard, diagnóstico, Work Planner y Supervisor.
- Orden de trabajo bloqueada en `pending_approval` hasta aprobación humana identificada.
- Audit ledger para altas, análisis y aprobaciones.
- SQLite + WAL como persistencia de piloto, aislada detrás de `OpsStore`.
- `TEOD_HUB_API_KEY` habilita protección simple por header `X-TEOD-API-Key`.
- `TEOD_HUB_DB_PATH` permite elegir la ubicación del archivo de datos.

La especificación y el lock de alcance están en `docs/TEOD_INDUSTRIAL_AI_HUB_V1.md`.

### Prueba rápida

1. Inicie la aplicación.
2. Abra `http://127.0.0.1:8000/ops`.
3. Pulse **Cargar caso demo**.
4. Revise la incidencia creada, los cinco agent runs y la orden pendiente.
5. Apruebe la orden y confirme el evento en **Auditoría**.

### Tests

```bash
pytest -q
```

## Lo nuevo en V16

- Market Ledger historico con mediana/IQR por componente, HP/corriente/tension y fuente.
- Conectores de mercado listos: MercadoLibre, Google Places, WhatsApp Cloud API y SMTP.
- Busqueda publica referencial de MercadoLibre mediante endpoint `/api/market/live/mercadolibre`.
- Desglose claro de precio: material, mano de obra, ingenieria, contingencia y margen.
- Diagramas CAD-like actualizados a V16 y visual dinamico por caso.
- OptionTrust: compara DOL, estrella-triangulo, soft starter, VFD y PLC/HMI con BOM/RFQ propio.
- SelectionTrust: lo que aparece en control/diagramas debe aparecer en BOM o quedar marcado como pendiente.
- FitLock: si breaker/VFD/reactor/cable no calzan con HP/FLA/tension, bloquea propuesta.

## Ejecutar local

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Deploy Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
