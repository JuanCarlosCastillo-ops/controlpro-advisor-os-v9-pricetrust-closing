# ControlPro Advisor OS V11 — Workshop Lock

Sistema operativo en español para **diseñar, cotizar, justificar y preparar entregables** de trabajos eléctricos industriales: tableros de motor, guinches, bombas, compresores y soluciones de control.

Esta versión está pensada para prueba con ingenieros eléctricos reales. El valor principal no es verse bonita: es **ahorrar tiempo de cotización**, ordenar datos, generar BOM, buscar/preparar precios por confianza, producir RFQ y entregar expediente técnico-comercial revisable.

## Qué trae V11

- Interfaz premium en español.
- Flujo didáctico: datos → fotos → 3D → CAD-like → cálculos → soluciones → BOM → mercado → APIs → RFQ → presupuesto → validación → entregables.
- Semáforo de precisión.
- Libro de supuestos.
- Auditoría de coherencia.
- Release gates: cotización vs construcción.
- BOM técnico cotizable.
- PriceGuard 11: semáforo verde/amarillo/rojo, banda de mercado, detección de outliers, autocorrección y RFQ obligatorio cuando no hay confianza.
- Precio por confianza: estimado, estimado corregido, referencial, referencial fuerte, confirmado.
- RFQ listo para WhatsApp/correo.
- Exportables:
  - Markdown técnico.
  - Propuesta cliente.
  - PDF premium con portada, KPIs, PriceGuard, presupuesto, BOM, supuestos y firmas.
  - BOM CSV/XLSX.
  - Unifilar CAD-like SVG.
  - Ladder CAD-like SVG.
  - Layout tablero CAD-like SVG.
  - Draw.io editable.
  - Lista de borneras CSV.
  - Lista de cables CSV.
- Panel para activar APIs reales por `.env`:
  - Mercado Libre.
  - Google Places.
  - WhatsApp Cloud API.
  - SMTP.

## Ejecutar localmente

```powershell
cd C:\AGENTES\controlpro_advisor_os_v11_workshop_lock

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Abrir:

```text
http://127.0.0.1:8000
```

## Activar APIs reales

Copiar la plantilla:

```powershell
copy .env.example .env
```

Editar `.env`, activar solo lo que se tenga listo y reiniciar la app.

Ver estado:

```text
/api/integrations/status
```

Ver plantilla desde API:

```text
/api/integrations/env-template
```

## Subir a GitHub

```powershell
cd C:\AGENTES\controlpro_advisor_os_v11_workshop_lock

git init
git branch -M main
git config --global user.name "JuanCarlosCastillo-ops"
git config --global user.email "JuanCarlosCastillo-ops@users.noreply.github.com"

git add .
git commit -m "Publicar ControlPro Advisor OS V11 Workshop Lock"

gh repo create controlpro-advisor-os-v10-workshop-lock --public --source=. --remote=origin --push
```

## Render

Build Command:

```text
pip install -r requirements.txt
```

Start Command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Límites profesionales

ControlPro V11 es un asesor técnico-comercial premium. No reemplaza:

- visita de campo,
- placa real,
- normativa local,
- cálculo final de SCCR/kAIC,
- coordinación de protecciones,
- revisión y firma de responsable técnico,
- pruebas seguras antes de energizar.

La regla del producto es:

> El humano revisa y aprueba; no reconstruye desde cero.
