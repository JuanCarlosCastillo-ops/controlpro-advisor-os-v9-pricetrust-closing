# ControlPro V12 - MarketPilot Lock Protocol

La V12 corrige el error crítico detectado en la exportación: una arquitectura recomendada no puede generar un BOM de otra arquitectura.

## Regla central

**Solución recomendada = BOM principal = RFQ = PDF = propuesta cliente.**

Si la app recomienda VFD, el BOM puede incluir VFD, reactor de línea y resistencia de frenado.
Si recomienda estrella-triángulo, el BOM debe incluir contactor principal, contactor estrella, contactor triángulo y temporizador; no debe incluir VFD, reactor ni resistencia de frenado.
Si recomienda inversión por contactores, no debe mezclar componentes de VFD ni estrella-triángulo.

## Regla especial para guinche/izaje

En guinches y carga suspendida, estrella-triángulo no se selecciona por defecto. Solo puede aceptarse con validación explícita: motor con seis terminales accesibles, carga liviana al arranque, torque suficiente, secuencia de freno validada y responsable humano.

Por defecto, un guinche profesional con freno, finales, muchas maniobras o perfil premium se orienta a **Variador + control inteligente**.

## Compuerta

La auditoría de coherencia agrega el chequeo **Coherencia arquitectura-BOM**. Si falla, bloquea salida fuerte.
