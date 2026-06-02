# ControlPro Advisor OS V9 PriceTrust Closing — Expediente técnico-comercial

**Proyecto:** Guinche de izaje — Cotización técnica premium
**Cliente:** Cliente industrial
**Ubicación:** Zaruma, El Oro, Ecuador
**Generado:** 2026-06-02T01:00:17.661162+00:00

## Veredicto ejecutivo
El sistema guía la entrada, genera solución, cálculos, BOM normalizado, precios por confianza, RFQ, presupuesto, riesgos, compuertas de calidad, exportables y acciones pendientes para que el ingeniero revise en vez de reconstruir.

## Calidad de datos
Estado: **cotización revisable; exige RFQ/verificación antes de oferta cerrada** · Score: **96.0%**
- OK · **Corriente de placa / FLA** · impacto Crítica · Subir foto de placa o confirmar FLA medido antes de enviar precio cerrado.
- OK · **Datos eléctricos base** · impacto Crítica · Confirmar tensión real, fases y frecuencia.
- OK · **Potencia y aplicación** · impacto Crítica · Indicar máquina, potencia y uso real.
- OK · **Evidencia fotográfica** · impacto Alta · Cargar placa, tablero actual/ruta y ambiente de instalación.
- OK · **Seguridad de izaje** · impacto Crítica · Para guinche/izaje exigir freno, finales de carrera y paro de emergencia.
- OK · **Protección ante falla de fase** · impacto Alta · En motores trifásicos de trabajo crítico usar monitor de fase/secuencia.
- OK · **Distancia y ambiente** · impacto Alta · Medir ruta real, temperatura, polvo/humedad y canalización.
- OK · **Ubicación comercial** · impacto Media · Indicar ciudad/provincia para proveedores, logística y vigencia.
- OK · **Alcance y margen** · impacto Media · Definir si incluye tablero, instalación, pruebas, transporte y margen mínimo.
- FALTA · **Cortocircuito disponible** · impacto Alta · Si no se conoce, marcar SCCR/kAIC como pendiente y no liberar construcción.

## Semáforo de precisión
Preparación cotización: **Alta: lista para propuesta piloto revisable** · Score: **95.4%**
Liberación construcción: **No liberada para construcción automática**

## Auditoría de coherencia
- **Coherencia FLA vs potencia** · ok · FLA placa 30.4 A vs estimado 29.1 A; desviación 4.5%. · Acción: Si supera 35%, revisar placa, conexión, tensión y unidades HP/kW.
- **Arquitectura de izaje** · ok · Aplicación de carga suspendida detectada. · Acción: No liberar construcción sin freno, finales de carrera, paro de emergencia y enclavamientos.
- **Caída de tensión** · ok · Caída estimada 0.42%. · Acción: Mantener verificación con tabla/código local.
- **SCCR/kAIC** · pendiente · No se declaró corriente de cortocircuito disponible. · Acción: Cotizar con advertencia; no liberar fabricación hasta verificar kAIC/SCCR.

## Libro de supuestos
- **SCCR/kAIC** · No se conoce corriente de cortocircuito; el breaker se trata como preliminar. · Confianza: baja · Verificación: Solicitar dato de transformador/red o medir/calcular antes de construir.
- **Precio de materiales** · Cobertura catálogo 100.0%; PriceGuard 83.8%; verdes 17, amarillos 1, rojos 1; RFQ requerido en 1 ítems. · Confianza: según fuente · Verificación: Confirmar stock/vigencia; el precio 100% cerrado solo existe con proveedor confirmado.
- **Mano de obra** · Se asumen 1.5 días tablero y 1.5 días campo. · Confianza: media · Verificación: Ajustar con visita técnica y alcance final.
- **Alcance** · Tablero + instalación en campo · Confianza: media · Verificación: Definir exclusiones: obra civil, canalización extra, parada de producción, permisos.
- **Izaje** · Se trata como equipo crítico por carga suspendida; se exige revisión superior. · Confianza: alta · Verificación: Probar sin carga, con carga supervisada y firmar checklist.

## Cálculos preliminares
- **full_load_current_a:** 30.4
- **breaker_size_a:** 60
- **overload_setting_a:** 38.0
- **conductor_preliminary:** #8 AWG Cu
- **voltage_drop_percent:** 0.42
- **control_transformer_va:** 2000
- **starting_current_estimate:** 182.4 A aprox. en arranque directo
- **short_circuit_available_ka:** pendiente
- **calculation_basis:** FLA de placa si existe; si no, estimación desde HP, V, fp y eficiencia.
- **notice:** Cálculos preliminares para cotización. Para construcción se requiere placa real, tablas/códigos aplicables, temperatura, canalización, coordinación y verificación de campo.

## Solución recomendada
**Estrella-triángulo** — Reduce corriente de arranque en motores aptos y cargas con bajo torque inicial.
Seleccionada por equilibrio entre seguridad, tiempo de cotización, control del riesgo y valor comercial defendible.

## BOM cotizable
- **mccb_main** · Cant. 1.0 · Schneider EasyPact CVS 60A 25kA · ElectroIndustrial Guayaquil · $145.0 · confianza alta · PriceGuard: VERDE (88.0%). Schneider EasyPact CVS 60A 25kA, ElectroIndustrial Guayaquil, Guayaquil.
- **overload_relay** · Cant. 1.0 · Schneider LRD3357 · ElectroIndustrial Guayaquil · $66.0 · confianza alta · PriceGuard: VERDE (88.1%). Schneider LRD3357, ElectroIndustrial Guayaquil, Guayaquil.
- **contactor_fwd** · Cant. 1.0 · Schneider LC1D32G7 · ElectroIndustrial Guayaquil · $82.0 · confianza alta · PriceGuard: VERDE (91.4%). Schneider LC1D32G7, ElectroIndustrial Guayaquil, Guayaquil.
- **contactor_rev** · Cant. 1.0 · Schneider LC1D32G7 · ElectroIndustrial Guayaquil · $82.0 · confianza alta · PriceGuard: VERDE (91.4%). Schneider LC1D32G7, ElectroIndustrial Guayaquil, Guayaquil.
- **mechanical_interlock** · Cant. 1.0 · Schneider LAD9R1V · ElectroIndustrial Guayaquil · $27.0 · confianza alta · PriceGuard: VERDE (88.2%). Schneider LAD9R1V, ElectroIndustrial Guayaquil, Guayaquil.
- **phase_monitor** · Cant. 1.0 · Schneider RM22TR33 · ElectroIndustrial Guayaquil · $94.0 · confianza alta · PriceGuard: VERDE (86.3%). Schneider RM22TR33, ElectroIndustrial Guayaquil, Guayaquil.
- **control_transformer** · Cant. 1.0 · Genérico industrial TC-2KVA · Suministros El Oro · $125.0 · confianza alta · PriceGuard: VERDE (86.2%). Genérico industrial TC-2KVA, Suministros El Oro, Machala.
- **cabinet** · Cant. 1.0 · Metálico Nacional MN-604025 · Suministros El Oro · $135.0 · confianza alta · PriceGuard: VERDE (84.9%). Metálico Nacional MN-604025, Suministros El Oro, Machala.
- **estop** · Cant. 1.0 · Schneider XB4BS542 · ElectroIndustrial Guayaquil · $24.0 · confianza alta · PriceGuard: VERDE (87.2%). Schneider XB4BS542, ElectroIndustrial Guayaquil, Guayaquil.
- **pushbuttons** · Cant. 1.0 · Schneider XB4 Kit · ElectroIndustrial Guayaquil · $72.0 · confianza alta · PriceGuard: VERDE (86.5%). Schneider XB4 Kit, ElectroIndustrial Guayaquil, Guayaquil.
- **limit_switches** · Cant. 2.0 · Schneider XCK-M · ElectroIndustrial Guayaquil · $38.0 · confianza alta · PriceGuard: VERDE (86.8%). Schneider XCK-M, ElectroIndustrial Guayaquil, Guayaquil.
- **brake_rectifier** · Cant. 1.0 · Bonfiglioli BRE120 · Proveedor Premium Quito · $142.0 · confianza media · PriceGuard: VERDE (77.7%). Bonfiglioli BRE120, Proveedor Premium Quito, Quito.
- **vfd** · Cant. 1.0 · ABB ACS580-01-039A-4 · Cuenca Control Supply · $1180.0 · confianza media-alta · PriceGuard: VERDE (80.7%). ABB ACS580-01-039A-4, Cuenca Control Supply, Cuenca.
- **line_reactor** · Cant. 1.0 · Genérico industrial LR-25HP-460 · Suministros El Oro · $168.0 · confianza media · PriceGuard: AMARILLO (75.0%). Genérico industrial LR-25HP-460, Suministros El Oro, Machala.
- **braking_resistor** · Cant. 1.0 · Danfoss BR-25HP · Automatización Andina · $247.5 · confianza baja · PriceGuard: ROJO (50.8%). Danfoss BR-25HP, Automatización Andina, Quito. Alertas: stock no confirmado. Se aplicó autocorrección por banda de mercado.
- **label_package** · Cant. 1.0 · Genérico LABEL-KIT · Suministros El Oro · $32.0 · confianza alta · PriceGuard: VERDE (81.1%). Genérico LABEL-KIT, Suministros El Oro, Machala.
- **terminal_blocks** · Cant. 1.0 · Genérico TB-KIT-30 · Suministros El Oro · $38.0 · confianza alta · PriceGuard: VERDE (86.5%). Genérico TB-KIT-30, Suministros El Oro, Machala.
- **wiring_pack** · Cant. 1.0 · Genérico WP-LOCAL · Suministros El Oro · $98.0 · confianza alta · PriceGuard: VERDE (85.8%). Genérico WP-LOCAL, Suministros El Oro, Machala.
- **power_cable** · Cant. 53.1 · Electrocables THHN-8AWG-CU · Suministros El Oro · $2.45 · confianza alta · PriceGuard: VERDE (88.7%). Electrocables THHN-8AWG-CU, Suministros El Oro, Machala.

## Presupuesto
- **materials:** 2963.59
- **panel_labor:** 270.0
- **field_labor:** 330.0
- **engineering:** 570.0
- **transport_logistics:** 120.0
- **contingency:** 340.29
- **margin:** 1148.47
- **floor_price:** 5145.14
- **recommended_sell_price:** 5742.35
- **premium_price:** 7005.66
- **price_confidence:** media-alta
- **priceguard_status:** PriceGuard 83.8% · verde 17 · amarillo 1 · rojo 1
- **commercial_note:** Cotización defendible con semáforo PriceGuard. Precio final cerrado solo con proveedor confirmado, stock y vigencia.

## RFQ listo para enviar
```text
Buenos días, necesito cotizar materiales para un proyecto de control industrial.

Proyecto: Guinche de izaje — Cotización técnica premium
Ubicación de entrega/referencia: Zaruma, El Oro, Ecuador

Favor confirmar precio unitario, marca disponible, modelo exacto, stock, tiempo de entrega, garantía, forma de pago y vigencia de oferta:

1. [MEDIA] Reactor de línea — Cantidad: 1 u — Especificación: 3%, 460 V, corriente compatible con 30.4 A — Motivo: confirmación de mercado
2. [ALTA] Resistencia de frenado — Cantidad: 1 u — Especificación: Dimensionar por ciclo de carga, energía de frenado y especificación del VFD — Motivo: stock no confirmado

También indicar alternativas equivalentes de calidad industrial y si pueden emitir proforma.
Gracias.
```

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
- **TB1-04** · W201 · S1 SUBIR → KM1 coil · Orden subir
- **TB1-05** · W301 · S2 BAJAR → KM2 coil · Orden bajar
- **TB1-06** · W401 · KM1/KM2 aux → BRK · Liberación freno
- **TB1-07** · W501 · OL/FM → ALM · Alarma/falla
- **TB1-08** · W000 · Control common → L- · Retorno control

### Lista preliminar de cables
- **C-PWR-01** · QF-01 → KM1/KM2 · 3F+PE · #8 AWG Cu · 5.6 m
- **C-MTR-01** · OL-01 → MTR-01 · 3F+PE · #8 AWG Cu · 53.1 m
- **C-CNT-01** · TB1 → Botonera · 8C · #16 AWG Cu · 8.0 m
- **C-LS-01** · TB1 → Final carrera sup/inf · 4C · #16 AWG Cu · 12.0 m

## Riesgos
- **Cotización con precio no confirmado** (Alta): Separar precio estimado, referencial y confirmado; enviar RFQ cuando confianza sea baja.
- **Movimiento simultáneo subir/bajar** (Alta): Enclavamiento eléctrico y mecánico; prueba funcional obligatoria.
- **Sobre-recorrido de carga** (Alta): Finales de carrera superior/inferior y prueba sin carga antes de carga real.
- **Freno mal seleccionado o mal secuenciado** (Alta): Confirmar placa del freno; validar tensión, corriente y lógica de liberación.
- **SCCR no coordinado** (Media): Verificar corriente de cortocircuito disponible y ratings de todos los componentes.
- **Ambiente severo** (Media): Seleccionar gabinete y componentes según ambiente declarado: Interior industrial con polvo.

## Mesa simulada de ingenieros
La V9 está lista para prueba piloto cerrada con ingenieros: el humano revisa, no reconstruye.
- **Ingeniero junior**: feliz para piloto · Flujo guiado, modo rápido, semáforo de precisión y compuertas de salida.
- **Técnico tablerista**: feliz para piloto · BOM normalizado por categoría, tabla cotizable, CSV/XLSX y notas de riesgo por componente.
- **Mantenimiento industrial**: feliz para piloto · Checklist de taller/campo, plan de verificación y diagnóstico de fallas típicas.
- **Diseñador eléctrico**: Satisfecho para piloto · Libro de supuestos, auditoría de coherencia, export PDF, Markdown y bloqueo SCCR/kAIC.
- **Cotizador/compras**: feliz para piloto · Market engine, price confidence, RFQ, CSV/XLSX BOM y fuente/vigencia por línea.
- **Seguridad/supervisor**: feliz: no promete construcción automática · Construction gate separado de quote gate; aprobación humana obligatoria.

## Próximas acciones guiadas
- Si no se conoce, marcar SCCR/kAIC como pendiente y no liberar construcción.

## Aviso
ControlPro reduce tiempo, ordena el expediente y baja la carga de corrección; no reemplaza normativa local, verificación de campo, proveedor confirmado ni aprobación humana antes de fabricar o energizar.