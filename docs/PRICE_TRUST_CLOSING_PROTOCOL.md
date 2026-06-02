# ControlPro V13 - MarketPilot Lock Protocol

Objetivo: que la app no entregue precios basura en cotizaciones de miles de dólares.

## Estados de precio

- **Verde / confirmado:** proveedor, stock, modelo y vigencia razonablemente confirmados o fuente interna validada. Usable para propuesta revisable.
- **Amarillo / referencial:** sirve para presupuesto, pero requiere RFQ si afecta margen, plazo o si el cliente exige precio cerrado.
- **Rojo / bloqueado:** no debe usarse para cerrar. La app debe autocorregir con mediana temporal y exigir RFQ.

## Reglas anti-basura

1. Nunca escoger automáticamente el más barato.
2. Auditar también ofertas no seleccionadas.
3. Separar catálogo piloto de mercado vivo.
4. Mostrar fuente, proveedor, stock, vigencia, banda y acción requerida.
5. No decir 100% seguro si no hay confirmación formal.
6. Si hay muchos amarillos/rojos, el PDF debe mostrarlo claramente.

## Umbrales sugeridos

- PriceGuard >= 85%: propuesta fuerte revisable.
- PriceGuard 70-85%: propuesta revisable con RFQ.
- PriceGuard < 70%: no enviar sin confirmar precios.
