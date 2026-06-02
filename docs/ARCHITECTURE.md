# Arquitectura

```text
Entrada de datos
  ↓
Validación de calidad
  ↓
Motor técnico: cálculos + requerimientos
  ↓
Normalizador de BOM
  ↓
Motor de precios: catálogo + proveedor + confianza
  ↓
Agente RFQ
  ↓
Presupuesto y margen
  ↓
Validación y entregables
```

## Módulos

- `app/main.py`: API FastAPI y web.
- `app/engine/models.py`: contratos de datos.
- `app/engine/advisor.py`: motor técnico-comercial.
- `app/engine/pricing.py`: precios, proveedores y RFQ.
- `app/integrations/`: conectores opcionales.
- `app/data/`: catálogo editable de precios/proveedores/componentes.
- `app/static/`: app web en español.
