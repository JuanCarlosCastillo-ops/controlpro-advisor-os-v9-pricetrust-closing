# ControlPro Advisor OS V15 OptionTrust Pro — Expediente técnico-comercial

**Proyecto:** Bomba industrial — Arranque protegido
**Cliente:** Cliente industrial
**Ubicación:** Zaruma, El Oro, Ecuador
**Generado:** 2026-06-02T22:39:24.395171+00:00

## Veredicto ejecutivo
El sistema guía la entrada, genera solución, cálculos, BOM normalizado, precios por confianza, RFQ, presupuesto, riesgos, compuertas de calidad, exportables y acciones pendientes para que el ingeniero revise en vez de reconstruir.

## Calidad de datos
Estado: **cotización revisable; exige RFQ/verificación antes de oferta cerrada** · Score: **96.0%**
- OK · **Corriente de placa / FLA** · impacto Crítica · Subir foto de placa o confirmar FLA medido antes de enviar precio cerrado.
- OK · **Datos eléctricos base** · impacto Crítica · Confirmar tensión real, fases y frecuencia.
- OK · **Potencia y aplicación** · impacto Crítica · Indicar máquina, potencia y uso real.
- OK · **Evidencia fotográfica** · impacto Alta · Cargar placa, tablero actual/ruta y ambiente de instalación.
- OK · **Protección hidráulica** · impacto Crítica · Confirmar protección contra trabajo en seco, nivel/presión, válvulas, cebado y golpe de ariete.
- OK · **Protección ante falla de fase** · impacto Alta · En motores trifásicos de trabajo crítico usar monitor de fase/secuencia.
- OK · **Distancia y ambiente** · impacto Alta · Medir ruta real, temperatura, polvo/humedad y canalización.
- OK · **Ubicación comercial** · impacto Media · Indicar ciudad/provincia para proveedores, logística y vigencia.
- OK · **Alcance y margen** · impacto Media · Definir si incluye tablero, instalación, pruebas, transporte y margen mínimo.
- FALTA · **Cortocircuito disponible** · impacto Alta · Si no se conoce, marcar SCCR/kAIC como pendiente y no liberar construcción.

## Semáforo de precisión
Preparación cotización: **Alta: lista para propuesta piloto revisable** · Score: **92.8%**
Liberación construcción: **No liberada para construcción automática**

## Auditoría de coherencia
- **Coherencia FLA vs potencia** · revisar · FLA placa 14.0 A vs estimado 24.3 A; desviación 42.4%. · Acción: Si supera 35%, revisar placa, conexión, tensión y unidades HP/kW.
- **Protección hidráulica** · ok · Contexto detectado: Bomba. · Acción: Confirmar protección contra trabajo en seco, nivel/presión, válvulas, cebado y golpe de ariete.
- **Caída de tensión** · ok · Caída estimada 0.41%. · Acción: Mantener verificación con tabla/código local.
- **SCCR/kAIC** · pendiente · No se declaró corriente de cortocircuito disponible. · Acción: Cotizar con advertencia; no liberar fabricación hasta verificar kAIC/SCCR.
- **Coherencia arquitectura-BOM** · ok · Arquitectura soft_starter coincide con el BOM generado. · Acción: Mantener regla: una arquitectura recomendada = un BOM principal coherente.

## Libro de supuestos
- **SCCR/kAIC** · No se conoce corriente de cortocircuito; el breaker se trata como preliminar. · Confianza: baja · Verificación: Solicitar dato de transformador/red o medir/calcular antes de construir.
- **Precio de materiales** · Cobertura catálogo 100.0%; PriceGuard 83.8%; FitLock bloqueados 0; verdes 16, amarillos 0, rojos 0; RFQ requerido en 0 ítems. · Confianza: según fuente · Verificación: Confirmar stock/vigencia y compatibilidad técnica; el precio 100% cerrado solo existe con proveedor confirmado y componente que calza.
- **Mano de obra** · Se asumen 1.5 días tablero y 1.5 días campo. · Confianza: media · Verificación: Ajustar con visita técnica y alcance final.
- **Alcance** · Tablero + instalación en campo · Confianza: media · Verificación: Definir exclusiones: obra civil, canalización extra, parada de producción, permisos.

## Cálculos preliminares
- **full_load_current_a:** 14.0
- **breaker_size_a:** 25
- **overload_setting_a:** 17.5
- **conductor_preliminary:** #12 AWG Cu
- **voltage_drop_percent:** 0.41
- **control_transformer_va:** 1000
- **starting_current_estimate:** 84.0 A aprox. en arranque directo
- **short_circuit_available_ka:** pendiente
- **calculation_basis:** FLA de placa si existe; si no, estimación desde HP, V, fp y eficiencia.
- **notice:** Cálculos preliminares para cotización. Para construcción se requiere placa real, tablas/códigos aplicables, temperatura, canalización, coordinación y verificación de campo.

## Solución recomendada
**Soft starter + bypass/protección** — Intermedio para reducir corriente/golpe sin control de velocidad.
Seleccionada por OptionTrust: balance entre necesidad técnica real, costo, riesgos, datos disponibles, FitLock, MathTrust y valor comercial defendible.

## Comparación de alternativas calculadas
- **Arranque directo DOL** · ALTERNATIVA · Precio ref: $3,047.56 · MathTrust 86.9% · RFQ 0 · FitLock bloqueados 0 · Motor pequeño/mediano, red robusta, bajo número de arranques y cliente con presupuesto ajustado.
- **Estrella-triángulo** · ALTERNATIVA · Precio ref: $3,341.86 · MathTrust 85.8% · RFQ 0 · FitLock bloqueados 0 · Motores con seis terminales accesibles, carga liviana al arranque y red sensible a picos.
- **Soft starter + bypass/protección** · RECOMENDADA · Precio ref: $3,591.61 · MathTrust 86.9% · RFQ 0 · FitLock bloqueados 0 · Arranques frecuentes moderados, red débil o se quiere menor estrés mecánico sin complejidad de VFD.
- **Variador + control inteligente** · ALTERNATIVA · Precio ref: $3,856.21 · MathTrust 85.6% · RFQ 0 · FitLock bloqueados 0 · Equipo crítico, muchas maniobras, necesidad de control suave o propuesta de alta confiabilidad.
FitLock Pro: **soft_starter** · Bomba: la decisión depende de presión/caudal, ahorro energético, golpe de ariete y presupuesto. Sin control variable declarado, pero con arranques/golpe: soft starter reduce estrés con menor costo que VFD.

## BOM cotizable
- **mccb_main** · Cant. 1.0 · Schneider EasyPact CVS 25A 25kA · ElectroIndustrial Guayaquil · $88.0 · confianza media · PriceGuard: VERDE (76.1%). Schneider EasyPact CVS 25A 25kA, ElectroIndustrial Guayaquil, Guayaquil. FitLock rechazó ofertas incompatibles: Schneider EasyPact CVS 60A 25kA: FitLock: oferta clase 600 V no corresponde a proyecto 220 V | ABB Tmax XT1 60A: FitLock: oferta clase 600 V no corresponde a proyecto 220 V | Chint NXM-63S 60A: FitLock: oferta clase 600 V no corresponde a proyecto 220 V.
- **overload_relay** · Cant. 1.0 · Schneider LRD3357 · ElectroIndustrial Guayaquil · $66.0 · confianza alta · PriceGuard: VERDE (90.7%). Schneider LRD3357, ElectroIndustrial Guayaquil, Guayaquil.
- **contactor_fwd** · Cant. 1.0 · Schneider LC1D32G7 · ElectroIndustrial Guayaquil · $82.0 · confianza alta · PriceGuard: VERDE (91.3%). Schneider LC1D32G7, ElectroIndustrial Guayaquil, Guayaquil.
- **soft_starter** · Cant. 1.0 · Chint NJRP2-32-220 · Suministros El Oro · $285.0 · confianza media-alta · PriceGuard: VERDE (78.4%). Chint NJRP2-32-220, Suministros El Oro, Machala. FitLock rechazó ofertas incompatibles: Schneider ATS22D47S6: FitLock: oferta clase 460 V no corresponde a proyecto 220 V | ABB PSE45: FitLock: oferta sin corriente verificable para requerimiento 14 A; FitLock: oferta clase 460 V no corresponde a proyecto 220 V | Chint NJRP2-45: FitLock: oferta sin corriente verificable para requerimiento 14 A; FitLock: oferta clase 460 V no corresponde a proyecto 220 V.
- **bypass_contactor** · Cant. 1.0 · Schneider LC1D50G7 · ElectroIndustrial Guayaquil · $118.0 · confianza media-alta · PriceGuard: VERDE (79.3%). Schneider LC1D50G7, ElectroIndustrial Guayaquil, Guayaquil.
- **phase_monitor** · Cant. 1.0 · Schneider RM22TR33 · ElectroIndustrial Guayaquil · $94.0 · confianza alta · PriceGuard: VERDE (86.3%). Schneider RM22TR33, ElectroIndustrial Guayaquil, Guayaquil.
- **control_transformer** · Cant. 1.0 · Genérico industrial TC-2KVA · Suministros El Oro · $125.0 · confianza alta · PriceGuard: VERDE (86.2%). Genérico industrial TC-2KVA, Suministros El Oro, Machala.
- **cabinet** · Cant. 1.0 · Metálico Nacional MN-604025 · Suministros El Oro · $135.0 · confianza alta · PriceGuard: VERDE (84.9%). Metálico Nacional MN-604025, Suministros El Oro, Machala.
- **estop** · Cant. 1.0 · Schneider XB4BS542 · ElectroIndustrial Guayaquil · $24.0 · confianza alta · PriceGuard: VERDE (87.2%). Schneider XB4BS542, ElectroIndustrial Guayaquil, Guayaquil.
- **pushbuttons** · Cant. 1.0 · Schneider XB4 Kit · ElectroIndustrial Guayaquil · $72.0 · confianza alta · PriceGuard: VERDE (86.5%). Schneider XB4 Kit, ElectroIndustrial Guayaquil, Guayaquil.
- **dry_run_protection** · Cant. 1.0 · Finder DRY-RUN-KIT · Suministros El Oro · $115.0 · confianza media-alta · PriceGuard: VERDE (78.0%). Finder DRY-RUN-KIT, Suministros El Oro, Machala.
- **pressure_sensor** · Cant. 1.0 · Danfoss KP36 · Suministros El Oro · $68.0 · confianza media · PriceGuard: VERDE (77.1%). Danfoss KP36, Suministros El Oro, Machala.
- **label_package** · Cant. 1.0 · Genérico LABEL-KIT · Suministros El Oro · $32.0 · confianza alta · PriceGuard: VERDE (81.1%). Genérico LABEL-KIT, Suministros El Oro, Machala.
- **terminal_blocks** · Cant. 1.0 · Genérico TB-KIT-30 · Suministros El Oro · $38.0 · confianza alta · PriceGuard: VERDE (86.5%). Genérico TB-KIT-30, Suministros El Oro, Machala.
- **wiring_pack** · Cant. 1.0 · Genérico WP-LOCAL · Suministros El Oro · $98.0 · confianza alta · PriceGuard: VERDE (85.8%). Genérico WP-LOCAL, Suministros El Oro, Machala.
- **power_cable** · Cant. 53.1 · Electrocables THHN-12AWG-CU · Suministros El Oro · $0.95 · confianza alta · PriceGuard: VERDE (84.8%). Electrocables THHN-12AWG-CU, Suministros El Oro, Machala. FitLock rechazó ofertas incompatibles: Electrocables THHN-10AWG-CU: FitLock: cable ofertado #10 AWG no coincide con cálculo preliminar #12 AWG | Electrocables THHN-8AWG-CU: FitLock: cable ofertado #8 AWG no coincide con cálculo preliminar #12 AWG | Electrocables THHN-6AWG-CU: FitLock: cable ofertado #6 AWG no coincide con cálculo preliminar #12 AWG | Cablec THHN-8AWG: FitLock: cable ofertado #8 AWG no coincide con cálculo preliminar #12 AWG.

## Presupuesto
- **materials:** 1490.45
- **panel_labor:** 270.0
- **field_labor:** 330.0
- **engineering:** 450.0
- **transport_logistics:** 120.0
- **contingency:** 212.84
- **margin:** 718.32
- **floor_price:** 3218.08
- **recommended_sell_price:** 3591.61
- **premium_price:** 4381.76
- **price_confidence:** alta
- **priceguard_status:** PriceGuard 83.8% · OptionTrust 86.9% · FitLock bloqueados 0 · verde 16 · amarillo 0 · rojo 0
- **commercial_blocked:** False
- **commercial_release_status:** Lista para propuesta revisable
- **range_label:** Precio recomendado revisable
- **mathtrust_score_percent:** 86.9
- **mathtrust_verdict:** Revisable con RFQ selectivo
- **commercial_note:** Cotización defendible con semáforo PriceGuard. Precio final cerrado solo con proveedor confirmado, stock y vigencia.

## RFQ listo para enviar
```text
Buenos días, necesito cotizar materiales para un proyecto de control industrial.

Proyecto: Bomba industrial — Arranque protegido
Ubicación de entrega/referencia: Zaruma, El Oro, Ecuador

Favor confirmar precio unitario, marca disponible, modelo exacto, stock, tiempo de entrega, garantía, forma de pago y vigencia de oferta:

1. Confirmar disponibilidad, vigencia y precio final de todos los materiales del BOM adjunto para cerrar propuesta.

También indicar alternativas equivalentes de calidad industrial y si pueden emitir proforma.
Gracias.
```

## Búsqueda rápida de proveedores
Ciudad base: Zaruma El Oro Ecuador
- materiales eléctricos industriales Zaruma El Oro Ecuador: https://www.google.com/search?q=materiales+el%C3%A9ctricos+industriales+Zaruma+El+Oro+Ecuador
- variadores contactores breakers Zaruma El Oro Ecuador: https://www.google.com/search?q=variadores+contactores+breakers+Zaruma+El+Oro+Ecuador
- tableros eléctricos automatización Zaruma El Oro Ecuador: https://www.google.com/search?q=tableros+el%C3%A9ctricos+automatizaci%C3%B3n+Zaruma+El+Oro+Ecuador
- cotizar Borneras, puentes y marcadores Zaruma El Oro Ecuador: https://www.google.com/search?q=cotizar+Borneras%2C+puentes+y+marcadores+Zaruma+El+Oro+Ecuador
- cotizar Botonera de mando Zaruma El Oro Ecuador: https://www.google.com/search?q=cotizar+Botonera+de+mando+Zaruma+El+Oro+Ecuador

## Salidas CAD-like / taller
- E-001 Unifilar CAD-like SVG
- E-002 Ladder CAD-like SVG
- E-003 Layout de tablero CAD-like SVG
- Draw.io editable para formalización
- Lista de borneras y lista de cables exportables

### Lista preliminar de borneras
- **TB1-01** · W101 · T1 secondary L+ → S0 STOP NC · Alimentación control
- **TB1-02** · W102 · S0 STOP NC → S-ESTOP NC · Cadena de paro
- **TB1-03** · W103 · S-ESTOP NC → CR coil · Permisivo maestro
- **TB1-04** · W201 · S1 MARCHA → KM1 coil · Orden marcha
- **TB1-06** · W401 · KM/AUX → RUN · Permisivo bomba
- **TB1-07** · W501 · OL/FM → ALM · Alarma/falla
- **TB1-99** · W000 · Control common → L- · Retorno control

### Lista preliminar de cables
- **C-PWR-01** · QF-01 → KM1 · 3F+PE · #12 AWG Cu · 5.6 m
- **C-MTR-01** · OL-01 → MTR-01 · 3F+PE · #12 AWG Cu · 53.1 m
- **C-CNT-01** · TB1 → Botonera · 8C · #16 AWG Cu · 8.0 m

## Riesgos
- **Cotización con precio no confirmado** (Alta): Separar precio estimado, referencial y confirmado; enviar RFQ cuando confianza sea baja.
- **Trabajo en seco** (Alta): Agregar sensor de nivel/flujo o protección dedicada.
- **Cavitación o bajo caudal** (Media): Verificar curva de bomba, válvulas y condiciones de succión.
- **Golpe de ariete** (Media): Usar rampa/valvulado adecuado y pruebas de presión.
- **SCCR no coordinado** (Media): Verificar corriente de cortocircuito disponible y ratings de todos los componentes.
- **Ambiente severo** (Media): Seleccionar gabinete y componentes según ambiente declarado: Interior industrial con polvo.

## Mesa simulada de ingenieros
La V15 OptionTrust Pro está lista para prueba piloto cerrada con ingenieros: arquitectura, BOM, CAD/taller, RFQ, PDF y propuesta obedecen la misma solución principal.
- **Ingeniero junior**: feliz para piloto · Resuelto
- **Técnico tablerista**: feliz para piloto · Resuelto
- **Mantenimiento industrial**: feliz para piloto · Resuelto
- **Diseñador eléctrico**: Satisfecho para piloto · Resuelto
- **Cotizador/compras**: feliz para piloto · Resuelto
- **Seguridad/supervisor**: feliz: no promete construcción automática · Resuelto

## Próximas acciones guiadas
- Si no se conoce, marcar SCCR/kAIC como pendiente y no liberar construcción.

## Aviso
ControlPro reduce tiempo, ordena el expediente y baja la carga de corrección; no reemplaza normativa local, verificación de campo, proveedor confirmado ni aprobación humana antes de fabricar o energizar.