# ControlPro Advisor OS V16 - MarketVision Pro

Copiloto de cotizacion industrial en espanol para motores, bombas, compresores, guinches, bandas y tableros.

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
