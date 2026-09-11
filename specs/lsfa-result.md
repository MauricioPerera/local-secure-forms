---
type: LSFA Protocol Specification
id: lsfa-result
version: 0.2
status: draft
---

# Resultado LSFA

El cliente devuelve un objeto estructurado con `status` y `operation`. Los
estados son `accepted`, `declined`, `cancelled`, `invalid`, `failed` y
`expired`.

Puede incluir `request_id`, `risk`, `checks`, `stored_refs` y `error_code`.
Estos campos deben ser opacos, booleanos o valores enumerados. Nunca pueden
contener el valor de un campo `secret`, PIN, token, código de segundo factor,
contraseña ni material de autenticación.

Un resultado `accepted` no implica que todos los efectos externos hayan sido
exitosos: `checks` debe indicar las verificaciones ejecutadas y `error_code`
debe describir un fallo sin incluir datos sensibles.
