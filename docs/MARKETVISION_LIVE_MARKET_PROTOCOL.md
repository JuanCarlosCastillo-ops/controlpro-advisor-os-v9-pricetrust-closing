# MarketVision Live Market Protocol

ControlPro V16 no trata una pagina web como precio final. Usa tres capas:

1. **Market Ledger**: memoria historica por componente, tension, HP/corriente, fuente, fecha y banda robusta p25/mediana/p75.
2. **Catalogo piloto**: ofertas internas o referenciales con proveedor, marca, modelo, stock y vigencia.
3. **Mercado vivo / APIs**: MercadoLibre, Google Places, RFQ por WhatsApp/correo y busqueda web dirigida.

## Regla dura

Un precio solo puede pasar a propuesta revisable cuando cumple:

- componente tecnicamente compatible por FitLock;
- fuente verificable;
- stock o disponibilidad razonable;
- vigencia;
- banda robusta razonable;
- proveedor/modelo trazable.

Si falla uno de los componentes criticos, el sistema debe declarar PRE-COTIZACION INTERNA y generar RFQ.

## Uso sin credenciales

Sin credenciales reales, la app entrega enlaces de busqueda y Market Ledger. Eso no se considera precio vivo. Sirve para acelerar la verificacion manual.

## Uso con credenciales

Con MELI_ENABLED, GOOGLE_PLACES_ENABLED, WHATSAPP_ENABLED o SMTP_ENABLED se puede automatizar busqueda/RFQ, pero PriceGuard/FitLock siguen bloqueando si el resultado no calza con HP, FLA, tension o especificacion.
