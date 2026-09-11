---
type: KDD Task Contract
task: sprint7_presentation_adapters
status: draft
target: src/lsfa/adapters.py
tests: tests/frozen_sprint7_adapters.py
---

# Objetivo 7 — Adaptadores de presentación

## Intent

Proporcionar una interfaz común para GUI, terminal y modo manual sin acoplar
el núcleo LSFA a una tecnología visual.

## Interface

Entradas: solicitud, callback de captura, callback de confirmación y ejecutor.
Salida: `PresentationResult` con estado estructurado y sin valores capturados.

## Invariants

- Cancelar no ejecuta la operación.
- Rechazar no ejecuta la operación.
- La política de riesgo determina la confirmación mínima.
- Los valores capturados solo viven en el proceso local.
- Los tres modos comparten semántica.

## Examples

- GUI y terminal usan el mismo `run` con distintos callbacks.
- Manual devuelve `cancelled` cuando el usuario no completa los datos.

## Do / Don't

- Do: inyectar UI y ejecución para mantener el SDK portable.
- Do: devolver solo `LSFAResult`.
- Don't: imprimir o serializar el diccionario de valores.
- Don't: permitir que el adaptador reduzca el nivel de confirmación.

## Tests

`python -m pytest tests/frozen_sprint7_adapters.py -q`

## Constraints

No añadir dependencias GUI ni integrar todavía almacenes seguros. **PARAR y
reportar si** un adaptador expone valores capturados al agente o ejecuta tras
cancelación, rechazo o expiración.
