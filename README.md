# ControlPro Advisor OS V15 — OptionTrust Pro

Sistema piloto para cotización industrial: múltiples alternativas de arranque, BOM coherente, MathTrust, FitLock, PriceGuard, RFQ, proveedor rápido por ciudad y entregables.

## Ejecutar
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Cierre técnico V15
- No recomienda siempre VFD.
- Cotiza alternativas DOL / estrella-triángulo / soft starter / VFD / PLC.
- Bloquea propuesta si datos, FitLock o MathTrust fallan.
- Sensores usados en control/riesgo aparecen en BOM.
- Cables calculados se validan contra catálogo.
- Incluye búsqueda rápida de proveedores por ciudad y RFQ.
