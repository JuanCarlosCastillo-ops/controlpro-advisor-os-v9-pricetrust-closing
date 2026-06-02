# Propuesta técnica-comercial

**Proyecto:** Bomba industrial — Arranque protegido
**Cliente:** Cliente industrial
**Ubicación:** Zaruma, El Oro

## Alcance propuesto
Diseño, selección preliminar de componentes, armado de expediente técnico, lista de materiales, presupuesto, checklist de pruebas y recomendaciones de instalación para sistema de control industrial.

## Solución recomendada
Soft starter + bypass/protección: Intermedio para reducir corriente/golpe sin control de velocidad..
Criterio de arquitectura: Bomba: la decisión depende de presión/caudal, ahorro energético, golpe de ariete y presupuesto. Sin control variable declarado, pero con arranques/golpe: soft starter reduce estrés con menor costo que VFD.

## Alternativas evaluadas
- **Arranque directo DOL** (ALTERNATIVA): referencia $3,047.56, MathTrust 86.9%, RFQ 0. Motor pequeño/mediano, red robusta, bajo número de arranques y cliente con presupuesto ajustado.
- **Estrella-triángulo** (ALTERNATIVA): referencia $3,341.86, MathTrust 85.8%, RFQ 0. Motores con seis terminales accesibles, carga liviana al arranque y red sensible a picos.
- **Soft starter + bypass/protección** (RECOMENDADA): referencia $3,591.61, MathTrust 86.9%, RFQ 0. Arranques frecuentes moderados, red débil o se quiere menor estrés mecánico sin complejidad de VFD.
- **Variador + control inteligente** (ALTERNATIVA): referencia $3,856.21, MathTrust 85.6%, RFQ 0. Equipo crítico, muchas maniobras, necesidad de control suave o propuesta de alta confiabilidad.

## Valores comerciales
- Precio piso técnico: $3,218.08
- Precio recomendado: $3,591.61
- Opción premium: $4,381.76

## Vigencia y condiciones
Precio sujeto a confirmación de stock, proveedor, placa real de motor/freno, condiciones de campo y aprobación técnica final.

## Nota de seguridad
ControlPro reduce tiempo, ordena el expediente y baja la carga de corrección; no reemplaza normativa local, verificación de campo, proveedor confirmado ni aprobación humana antes de fabricar o energizar.