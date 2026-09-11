---
type: KDD Task Contract
task: sprint6_reference_sdk
status: draft
target: src/lsfa/core.py
tests: tests/frozen_sprint6_sdk.py
---

# Objetivo 6 — SDK de referencia

## Intent

Ofrecer modelos Python pequeños para validar solicitudes, resultados,
expiración y confirmación sin acoplar LSFA a una UI o proveedor.

## Interface

Entradas: diccionarios y valores tipados de una operación LSFA.
Salidas: objetos inmutables y resultados serializables sin secretos.

## Invariants

- Los niveles de riesgo tienen una confirmación mínima.
- Los resultados solo contienen campos estructurados permitidos.
- El SDK no captura ni devuelve PIN, tokens o secretos.
- Una solicitud puede determinar si expiró.

## Examples

- `ConfirmationPolicy.minimum_for("irreversible")` devuelve `pin_and_totp`.
- `LSFAResult(...).to_dict()` produce un objeto JSON seguro.

## Do / Don't

- Do: mantener el núcleo independiente de transporte, UI y almacén.
- Do: usar tipos y errores deterministas.
- Don't: implementar autenticadores o almacenar secretos en el SDK.
- Don't: aceptar métodos de confirmación débiles para riesgo alto.

## Tests

`python -m pytest tests/frozen_sprint6_sdk.py -q`

## Constraints

Usar únicamente la biblioteca estándar. **PARAR y reportar si** el SDK
necesita leer un secreto, depende de un proveedor externo o devuelve material
de autenticación.
