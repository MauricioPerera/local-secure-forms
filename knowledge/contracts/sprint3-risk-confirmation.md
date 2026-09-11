---
type: KDD Task Contract
task: sprint3_risk_confirmation
status: draft
target: specs/lsfa-confirmation.md
tests: tests/frozen_sprint3_confirmation.py
---

# Objetivo 3 — Riesgo y confirmación

## Intent

Establecer cómo se autoriza una operación sin permitir que el agente sustituya
la decisión del usuario.

## Interface

Entradas: operación, alcance y nivel de riesgo.
Salidas: confirmación consumible una sola vez o estado no ejecutable.

## Invariants

- `high` requiere PIN y `irreversible` requiere PIN más segundo factor.
- La confirmación está ligada a una solicitud y expira.
- El agente no ve ni introduce PIN o códigos.
- Rechazo, cancelación y expiración no ejecutan efectos.

## Examples

- `send_email` usa `pin` y muestra destinatario y asunto.
- `purge` usa `pin_and_totp` y muestra el recurso afectado.

## Do / Don't

- Do: mostrar riesgo, destino y alcance antes del control de confirmación.
- Do: invalidar la confirmación después de consumirla.
- Don't: aceptar confirmaciones sin `request_id` o fuera de plazo.
- Don't: degradar automáticamente el método solicitado.

## Tests

`python -m pytest tests/frozen_sprint3_confirmation.py -q`

## Constraints

No implementar todavía proveedores de TOTP ni una UI concreta. **PARAR y reportar si**
el agente puede confirmar, recuperar un factor o reutilizar una
confirmación consumida.
