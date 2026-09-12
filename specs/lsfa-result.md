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

En el SDK de referencia, `accepted` requiere retorno normal del ejecutor y
salida válida. El ejecutor debe señalar un efecto fallido o incierto mediante
excepción. `checks` contiene solo booleanos bajo nombres registrados;
`stored_refs`, estados booleanos o `present`/`absent`, no tokens arbitrarios.
`request_id` y riesgo efectivo se preservan en todos los resultados del adaptador.

Un fallo posterior a la reserva devuelve `execution_outcome_unknown` y
`values_consumed=True`: no habilita reintento. Véase [migración](../SDK-MIGRATION.md).
