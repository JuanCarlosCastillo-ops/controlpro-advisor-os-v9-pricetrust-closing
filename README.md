# ControlPro Advisor OS V12 - MarketPilot Lock

Sistema web en español para cotizar trabajos de control industrial con flujo por capas, PriceGuard, Machine Context Lock, BOM, mercado/RFQ, CAD-like, PDF, Excel y registro piloto.

## Qué trae V12

- Interfaz premium por capas: cotizar rápido, evidencia/CAD, mercado, entregables y admin interno.
- Registro piloto para capturar interesados.
- Machine Context Lock: guinche, compresor, bomba, banda o motor general generan riesgos, checklist, RFQ y taller diferentes.
- Architecture Lock + Workshop Lock: solución recomendada = BOM = CAD/taller = PDF = propuesta.
- PriceGuard 12: semáforos de precio, outliers, autocorrección, RFQ y fuente/vigencia.
- Exportables: PDF, Markdown, propuesta cliente, BOM CSV/XLSX, Draw.io, unifilar/ladder/layout SVG, cables/borneras CSV.
- APIs listas por `.env`: Mercado Libre, Google Places, WhatsApp Cloud API y SMTP.

## Ejecutar local

```powershell
cd C:\AGENTES\controlpro_advisor_os_v12_marketpilot_final
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abrir:

```text
http://127.0.0.1:8000
```

## Deploy Render

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Subir a GitHub

```powershell
git add .
git commit -m "Actualizar a ControlPro V12 MarketPilot Lock"
git push
```

## Límite profesional

Es herramienta de cotización/revisión. No libera construcción ni energización sin placa real, campo, normativa aplicable, proveedor confirmado y aprobación humana.
