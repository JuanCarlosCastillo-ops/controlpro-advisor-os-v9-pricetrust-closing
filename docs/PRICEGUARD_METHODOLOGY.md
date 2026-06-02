# PriceGuard 12 — metodología de precios confiables

ControlPro no debe escoger el precio más barato ni fingir certeza. PriceGuard clasifica cada línea del BOM con semáforo:

- **Verde:** precio usable para cotización revisable. Fuente válida, stock disponible, vigencia visible y sin alertas de banda.
- **Amarillo:** precio referencial. Sirve para avanzar rápido, pero conviene RFQ si el margen es sensible o el cliente exige precio cerrado.
- **Rojo:** no cerrar precio. El sistema detectó precio sospechosamente bajo, alto fuera de banda, stock no confirmado, vigencia vencida o ausencia de ofertas.

## Entradas del score

1. Fuente del precio: confirmado, interno, referencia, marketplace o estimado.
2. Stock: disponible, por cotizar, desconocido o no disponible.
3. Vigencia: fecha de validez de la oferta.
4. Banda de mercado: mínimo, mediana, P25, P75 y máximo por componente.
5. Proveedor: rating, ubicación, plazo de entrega y confiabilidad.
6. Coherencia: detección de valores demasiado baratos o exagerados.

## Autocorrección

Si un precio cae en rojo por fuera de banda, ControlPro no lo usa como definitivo. Usa la mediana temporal solo para presupuesto preliminar y exige RFQ.

## Regla de verdad

Un precio no es 100% seguro hasta que exista proveedor confirmado, stock confirmado, modelo exacto, vigencia y forma de entrega. El software siempre debe mostrar el nivel de confianza.
