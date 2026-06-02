# FitLock / Sizing Lock — Protocolo V14

ControlPro no debe permitir que un precio parezca confiable si el componente no calza técnicamente.

## Regla principal

**PriceGuard no puede estar fuerte si FitLock está rojo.**

Un precio solo puede usarse como base de cotización revisable si cumple estas cuatro condiciones:

1. El componente existe en catálogo o proveedor.
2. El componente calza con HP, FLA, tensión, arquitectura y aplicación.
3. El precio corresponde a ese tamaño real.
4. El proveedor confirma modelo, stock, vigencia y condiciones.

## Qué valida FitLock

- MCCB/breaker: corriente mínima requerida y tensión.
- Contactores: corriente AC-3 mínima y función correcta.
- VFD/soft starter: HP o corriente nominal compatible con FLA.
- Reactor/resistencia: tamaño compatible con VFD/motor.
- Conductores: si la corriente supera el catálogo piloto, bloquea y pide cálculo dedicado.
- Transformador de control: kVA/VA compatible.
- Gabinete: reserva/tamaño coherente para VFD y potencia.

## Comportamiento cuando falla

Si no hay producto compatible:

- Semáforo rojo.
- RFQ obligatorio.
- Precio no cerrable.
- La cotización baja a borrador interno o propuesta con advertencias.
- El PDF debe decir que el precio es presupuestario, no confirmado.

## Objetivo

Evitar que un proyecto de miles de dólares salga con componentes subdimensionados solo porque estaban en el catálogo piloto.
