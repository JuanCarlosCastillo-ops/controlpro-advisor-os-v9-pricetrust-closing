# ControlPro V14 — Salidas CAD-like y entregables de taller

La versión V14 mejora los diagramas para que dejen de sentirse como dibujos conceptuales básicos. Ahora el motor entrega salidas intermedias más cercanas a ingeniería:

## Hojas generadas

- **E-001 Unifilar CAD-like SVG**
  - Title block.
  - Tags de equipos.
  - QF, monitor de fase, contactores, sobrecarga, motor y transformador de control.
  - Nota visible de SCCR/kAIC pendiente si no se conoce.

- **E-002 Ladder CAD-like SVG**
  - Rungs numerados.
  - STOP, E-STOP, subir, bajar, finales de carrera, enclavamientos, freno y alarma.
  - Numeración preliminar de cables.

- **E-003 Layout de tablero CAD-like SVG**
  - Backplate.
  - Riel DIN.
  - Canaleta.
  - Contactores.
  - Borneras.
  - Puerta/operador.
  - Reserva interna y nota de congelamiento.

## Exportables CAD

```text
POST /api/export/cad/single-line-svg
POST /api/export/cad/control-ladder-svg
POST /api/export/cad/panel-layout-svg
POST /api/export/cad/drawio
POST /api/export/cad/terminal-schedule-csv
POST /api/export/cad/wire-schedule-csv
```

## Qué significa CAD-like

No significa plano final firmado. Significa:

> “El sistema entrega una base técnica ordenada y editable para que el ingeniero no empiece desde cero.”

Antes de fabricar se debe formalizar:

- Numeración final de bornes.
- Numeración final de cables.
- Modelos exactos de componentes.
- Dimensiones reales.
- Disipación térmica.
- Separación fuerza/control.
- SCCR/kAIC.
- Normativa local.
- Firma técnica responsable.

## Regla de aceptación

Un ingeniero no debería redibujar desde cero. Debería corregir, completar y aprobar.
