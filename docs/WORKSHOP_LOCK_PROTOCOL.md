# ControlPro V11 - Workshop Lock Protocol

La V11 corrige el último arrastre detectado: si la arquitectura principal es VFD + control inteligente, las salidas de taller no pueden conservar lenguaje de inversión por contactores como KM1/KM2.

## Regla de cierre

Solución recomendada = BOM principal = RFQ = PDF = propuesta cliente = unifilar = ladder = layout = lista de borneras = lista de cables = Draw.io.

## Arquitectura VFD + control inteligente

- Fuerza: QF-01 → K1/seguridad → VFD-01 → MTR-01.
- Control: pulsadores, finales y permisivos a entradas digitales del VFD o controlador.
- Freno: salida/relé coordinado con run/ready del VFD y validación del freno mecánico.
- Alarma: falla VFD/fase a piloto o salida de alarma.
- No usar KM1/KM2 como inversión principal.

## Arquitectura contactorizada

Solo en DOL/reversing se permite KM1/KM2 subir/bajar con enclavamiento eléctrico y mecánico.

## Arquitectura estrella-triángulo

Solo se permite KM-L/KM-Y/KM-Δ si el motor/carga son aptos y se valida seis terminales, torque y secuencia.
