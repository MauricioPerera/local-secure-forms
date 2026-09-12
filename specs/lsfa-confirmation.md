---
type: LSFA Protocol Specification
id: lsfa-confirmation
version: 0.2
status: draft
---

# Riesgo y confirmación LSFA

El cliente asigna o valida el nivel de riesgo de cada solicitud y muestra al
usuario un resumen de la operación antes de ejecutarla.

| Riesgo | Confirmación mínima |
|---|---|
| `low` | aceptación visible del usuario |
| `medium` | aceptación visible; PIN opcional según política |
| `high` | PIN local obligatorio |
| `irreversible` | PIN local y segundo factor obligatorio |

Los métodos permitidos son `user_accept`, `pin` y `pin_and_totp`. El agente no
puede seleccionar un método menos seguro, introducir credenciales ni aprobar
la solicitud. Cada confirmación queda ligada a un `request_id`, operación,
alcance y resumen; expira con la solicitud y solo puede consumirse una vez.

Rechazar, cancelar, fallar o dejar expirar una confirmación no ejecuta la
operación ni guarda secretos.

En el esquema, `required` y `single_use` deben ser explícitamente `true`;
`summary` es una lista, no una cadena. Estos son requisitos de la solicitud,
no credenciales ni pruebas de aprobación. El SDK exige evidencia de un
verificador local vinculada al contenido íntegro y con plazo verificable.
La confirmación puede vencer antes que la solicitud. Su consumo es atómico y
persistente antes del efecto; un resultado incierto no habilita repetición.
Véase [el contrato de integración](../SDK-MIGRATION.md).
