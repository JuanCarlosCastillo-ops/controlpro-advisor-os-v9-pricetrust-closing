# Validation Report - ControlPro Advisor OS V12 MarketPilot Lock

## Resultado
VALIDATION OK.

## Validaciones ejecutadas

```bash
python -m compileall app scripts tests -q
PYTHONPATH=. python scripts/validate_project.py
PYTHONPATH=. pytest -q
```

## Resultado esperado
- Engineering completeness: >= 80%
- Market coverage: >= 80%
- PriceGuard: >= 70%
- API health: OK
- Exportables: Markdown, propuesta cliente, PDF, BOM CSV/XLSX, SVG, Draw.io, listas CSV
- Tests: 11 passed

## Cierre V12
La V12 agrega **Machine Context Lock** y **Layered UX**:

1. El texto, riesgos, checklist, CAD/taller y RFQ cambian según la máquina: guinche, compresor, bomba, banda o motor general.
2. La web se usa por capas: registro piloto, datos mínimos, evidencia/CAD, mercado, entregables y admin interno.
3. El panel de APIs queda oculto para el cliente normal; solo sirve para activación interna.
4. La vista 3D didáctica se reemplaza por un visual premium de producto.
5. Se agrega captura de lead piloto con endpoint `/api/leads` y almacenamiento temporal/local.

## Límite profesional
ControlPro reduce tiempo y ordena el expediente. No reemplaza normativa local, verificación de campo, proveedor confirmado ni aprobación humana antes de fabricar o energizar.
