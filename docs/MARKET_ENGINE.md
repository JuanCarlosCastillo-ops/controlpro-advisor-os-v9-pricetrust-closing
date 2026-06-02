# Motor de mercado

La app no asume que todo precio de internet sea correcto. Usa niveles:

1. **Confirmado**: proveedor respondió RFQ o precio validado manualmente.
2. **Referencial fuerte**: catálogo interno o proveedor con buena confianza/stock.
3. **Referencial**: marketplace o precio de referencia.
4. **Estimado**: fallback conservador cuando no hay dato.

Todo ítem con baja confianza pasa al mensaje RFQ.

## Cómo actualizar precios

Editar:

```text
app/data/price_catalog.csv
app/data/suppliers.csv
```

Luego recargar la app. No requiere base de datos compleja para piloto.
