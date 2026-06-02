# PRE-COTIZACIÓN INTERNA — NO ENVIAR COMO OFERTA CERRADA

**Proyecto:** Guinche de izaje — Cotización técnica premium
**Cliente:** Cliente industrial
**Ubicación:** Zaruma, El Oro

## Estado comercial
**Bloqueada por OptionTrust/FitLock.** Esta salida sirve para revisión interna y solicitud de RFQ, no para enviarse como oferta cerrada al cliente.
- OptionTrust: 86.3% · Revisable con RFQ selectivo
- PriceGuard: 82.7% · Revisable con RFQ
- FitLock bloqueados: 0
- RFQ requeridos: 1

## Alcance propuesto
Diseño, selección preliminar de componentes, armado de expediente técnico, lista de materiales, presupuesto, checklist de pruebas y recomendaciones de instalación para sistema de control industrial.

## Solución recomendada
Variador + control inteligente: Premium para rampas, diagnóstico, control, crecimiento y diferenciación técnica..
Criterio de arquitectura: Guinche/izaje: carga suspendida, freno, finales y E-Stop elevan el riesgo. Uso profesional/premium o muchas maniobras: VFD mejora rampa, diagnóstico y control mecánico.

## Alternativas evaluadas
- **Arranque directo DOL** (BLOQUEADA): referencia $3,441.27, MathTrust 83.8%, RFQ 1. Motor pequeño/mediano, red robusta, bajo número de arranques y cliente con presupuesto ajustado.
- **DOL + contactores de inversión** (BLOQUEADA): referencia $3,588.42, MathTrust 84.7%, RFQ 1. Guinche simple, baja/mediana frecuencia de maniobra y cuando se acepta golpe mecánico.
- **Estrella-triángulo** (BLOQUEADA): referencia $3,743.67, MathTrust 82.8%, RFQ 1. Motores con seis terminales accesibles, carga liviana al arranque y red sensible a picos.
- **Soft starter + bypass/protección** (BLOQUEADA): referencia $4,721.07, MathTrust 83.0%, RFQ 1. Arranques frecuentes moderados, red débil o se quiere menor estrés mecánico sin complejidad de VFD.
- **Variador + control inteligente** (RECOMENDADA): referencia $5,506.10, MathTrust 86.3%, RFQ 1. Equipo crítico, muchas maniobras, necesidad de control suave o propuesta de alta confiabilidad.

## Rango preliminar no confirmado
- Orden de magnitud piso: $4,933.46
- Orden de magnitud medio: $5,506.10
- Orden de magnitud alto: $6,717.44

**Advertencia:** estos valores NO son precio cerrado. Los componentes críticos deben confirmarse por proveedor con modelo, corriente/HP, tensión, stock, vigencia y compatibilidad técnica.

## Ítems que bloquean oferta cerrada
- **mccb_main**: Usar en cotización revisable; confirmar vigencia si la oferta supera 72 horas.
- **contactor_fwd**: Usar en cotización revisable; confirmar vigencia si la oferta supera 72 horas.
- **vfd**: Usar en cotización revisable; confirmar vigencia si la oferta supera 72 horas.
- **line_reactor**: Usar como referencia; enviar RFQ si el proyecto es sensible a precio o plazo.
- **braking_resistor**: Precio fuera de confianza. Usar mediana temporal y enviar RFQ a varios proveedores.
- **power_cable**: Usar en cotización revisable; confirmar vigencia si la oferta supera 72 horas.

## Próxima acción
Enviar RFQ técnico, actualizar precios confirmados y regenerar propuesta.

## Vigencia y condiciones
Precio sujeto a confirmación de stock, proveedor, placa real de motor/freno, condiciones de campo y aprobación técnica final.

## Nota de seguridad
ControlPro reduce tiempo, ordena el expediente y baja la carga de corrección; no reemplaza normativa local, verificación de campo, proveedor confirmado ni aprobación humana antes de fabricar o energizar.