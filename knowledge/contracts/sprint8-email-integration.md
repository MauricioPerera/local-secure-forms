---
type: KDD Task Contract
task: sprint8_email_integration
status: draft
target: specs/lsfa-email-integration.md
tests: tests/frozen_sprint8_email_integration.py
---

# Objetivo 8 — Integración con email-agent-kdd

## Intent

Demostrar que LSFA puede gobernar captura, validación y confirmación de las
operaciones de correo sin exponer credenciales.

## Interface

Entradas: intención de conectar o enviar, campos y referencia de cuenta.
Salidas: solicitud LSFA y resultado estructurado sin secretos.

## Invariants

- Conectar valida IMAP/SMTP antes de guardar.
- Enviar requiere confirmación de alto riesgo.
- La contraseña no aparece en la respuesta.
- Cancelación, rechazo y expiración no ejecutan efectos.

## Examples

- `connect_email` con `password` secreto y `imap_auth_and_smtp_auth`.
- `send_email` con confirmación `pin`.

## Do / Don't

- Do: pasar secretos del formulario directamente al ejecutor local.
- Do: devolver referencias opacas y verificaciones.
- Don't: incluir la contraseña en prompts, logs o resultados.
- Don't: enviar correo antes de la confirmación.

## Tests

`python -m pytest tests/frozen_sprint8_email_integration.py -q`

## Constraints

No conectar cuentas reales durante las pruebas del puente. **PARAR y reportar si**
la integración serializa un secreto al agente o ejecuta SMTP sin la confirmación
requerida.
