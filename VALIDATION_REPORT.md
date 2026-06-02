# ControlPro Advisor OS V14 MathTrust Pro — Validation Report

Validación ejecutada:

```bash
python -m compileall app scripts tests -q
PYTHONPATH=. python scripts/validate_project.py
PYTHONPATH=. pytest -q
```

Resultado esperado:

```text
VALIDATION OK
12 tests passed
```

Controles principales:

- MathTrust calcula confiabilidad combinando FitLock, PriceGuard, profundidad de catálogo, dispersión robusta y fuente/stock.
- FitLock bloquea componentes incompatibles con HP/FLA/tensión.
- PriceGuard no puede volverse fuerte cuando FitLock está rojo.
- Propuesta cliente cambia a PRE-COTIZACIÓN INTERNA si la salida está bloqueada.
- El caso crítico de compresor 180 HP / 440 V / 280 A queda bloqueado y exige RFQ.
- Los documentos separan precio cerrable, referencial y bloqueado.
