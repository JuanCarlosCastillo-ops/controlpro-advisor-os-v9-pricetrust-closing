# Quality Gates — ControlPro V5

La salida no se mide solo por verse bonita. Se mide por compuertas.

## 1. Calidad de datos

Evalúa FLA de placa, potencia, tensión, fases, fotos, seguridad de izaje, distancia, ambiente, ubicación, alcance y SCCR/kAIC.

## 2. Auditoría de coherencia

Compara FLA declarada vs FLA estimada, aplicación detectada, caída de tensión y disponibilidad de corto circuito.

## 3. Mercado y precio

Todo precio tiene fuente, vigencia, confianza, proveedor, stock y decisión. Si falta precio confiable, se manda a RFQ.

## 4. Liberación

- Cotización piloto: puede salir si datos críticos, coherencia y mercado pasan.
- Construcción: queda bloqueada hasta validar placa, campo, proveedor, seguridad y SCCR/kAIC.

## 5. No garbage policy

Si falta información, el sistema debe decir “pendiente” o “requiere RFQ”, no inventar.


## FitLock V13

Esta versión bloquea componentes técnicamente incompatibles con HP, FLA, tensión y arquitectura antes de considerar un precio como usable.
