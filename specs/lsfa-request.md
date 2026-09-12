---
type: LSFA Protocol Specification
id: lsfa-request
version: 0.2
status: draft
---

# Solicitud LSFA

Una solicitud describe una operación concreta que el cliente local debe
presentar y validar. `operation`, `purpose`, `fields`, `validation` y
`expires_in_seconds` son obligatorios.

Cada campo declara `name`, `type` y `sensitivity`. Las sensibilidades válidas
son `public`, `private` y `secret`. Un campo secreto se captura únicamente en
el cliente y nunca se serializa hacia el agente después de completar la
operación.

`request_id` puede ser proporcionado por el agente como correlación, pero el
cliente debe generar o validar un identificador opaco propio. No debe contener
contraseñas, tokens ni datos personales.

La solicitud expira cuando transcurre `expires_in_seconds`; una solicitud
expirada no puede aceptar, guardar secretos ni ejecutar efectos externos.

El cliente fija el plazo al emitir la solicitud, antes de capturar datos.
`presentation` es opcional (`auto`). Nombres duplicados, defaults privados o
secretos, tipos no soportados y booleanos usados como TTL son inválidos.
Los validadores son nombres registrados localmente, nunca código del agente.
Véase [el perfil ejecutable y sus límites](../SDK-MIGRATION.md).
