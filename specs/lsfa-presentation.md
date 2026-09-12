---
type: LSFA Protocol Specification
id: lsfa-presentation
version: 0.2
status: draft
---

# Adaptadores de presentación LSFA

Una implementación puede presentar la solicitud como formulario gráfico,
preguntas de terminal o configuración manual/headless. Los tres modos deben
usar la misma solicitud, política de riesgo, validación y resultado.

El adaptador recibe valores dentro del proceso local y los entrega directamente
al ejecutor autorizado. No debe serializarlos al agente ni imprimirlos. Un
callback de colección puede devolver `null` para cancelar; la confirmación
debe devolver una decisión explícita antes de ejecutar.

Desde el Sprint 13 se usa `adapter.run(client.issue(request))`, con política y
verificador registrados en el cliente. Una decisión positiva requiere recibo
verificado, no un booleano; `False`/`None` pueden rechazar. El callback recibe
una copia privada del contexto, nunca propiedad sobre el snapshot ejecutado.

La ausencia de GUI no autoriza degradar la seguridad: terminal y manual deben
ocultar secretos, respetar expiración y exigir el mismo método de confirmación.

Los adaptadores del SDK no implementan esas interfaces visuales ni factores
reales; aplican un flujo común a callbacks confiables. No ejecutan headless
automáticamente ni convierten ausencia de UI en autorización.
