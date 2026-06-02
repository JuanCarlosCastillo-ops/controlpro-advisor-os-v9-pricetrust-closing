# MathTrust Pro — respaldo matemático de precio y selección

MathTrust no promete precio exacto sin proveedor real. Su función es impedir falsas certezas y separar tres estados:

1. **Precio cerrable/revisable**: componente compatible + fuente confiable + stock/vigencia aceptables.
2. **Precio referencial**: útil para orden de magnitud, requiere confirmación.
3. **Precio bloqueado**: FitLock o PriceGuard detectan incompatibilidad, falta de mercado o señal débil.

## Modelo de puntuación

```text
MathTrust = 0.36·FitLock + 0.26·PriceGuard + 0.16·profundidad_catálogo + 0.12·dispersión_robusta + 0.10·fuente_stock
```

## Capas matemáticas

- **FitLock**: valida corriente, HP, tensión y especificación contra cada oferta.
- **Banda robusta de mercado**: usa mediana/IQR y dispersión, no el precio más barato.
- **Pesos bayesianos simples**: fuente, stock, vigencia, ciudad y reputación ajustan confianza.
- **RFQ consensus**: si no hay oferta compatible, el precio queda bloqueado hasta confirmación de proveedor.
- **Anti-garbage rule**: PriceGuard no puede ponerse fuerte si FitLock está rojo.

## Regla comercial

Si MathTrust/FitLock bloquea, la salida de cliente debe decir **pre-cotización interna**, no propuesta cerrada.
