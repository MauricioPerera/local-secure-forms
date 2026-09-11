---
type: KDD Task Contract
task: sprint5_ux_style
status: draft
target: UX-GUIDE.md
tests: tests/frozen_sprint5_ux.py
---

# Objetivo 5 — UX y guía de estilos

## Intent

Hacer que una implementación LSFA sea clara, accesible y coherente para
usuarios técnicos y no técnicos.

## Interface

Entradas: operación, campos, riesgo y resultado.
Salidas: interfaz GUI, terminal o manual con la misma semántica de seguridad.

## Invariants

- Aceptar, rechazar y cancelar son acciones diferentes.
- La implementación distingue aceptar, rechazar y cancelar.
- La interfaz muestra destino, alcance y riesgo antes de confirmar.
- Los secretos se ocultan y nunca se imprimen.
- Estados y códigos permanecen estables entre idiomas y plataformas.

## Examples

- `Sí, confirmar` para una operación revisada.
- `Eliminar permanentemente` para `purge`.
- Mensaje de error que explica la corrección sin mostrar trazas.

## Do / Don't

- Do: validar cerca del campo y ofrecer ejemplos comprensibles.
- Do: mantener GUI, terminal y manual equivalentes.
- Don't: pedir al usuario que copie comandos o secretos.
- Don't: usar “Aceptar” para una acción cuyo alcance no se muestra.

## Tests

`python -m pytest tests/frozen_sprint5_ux.py -q`

## Constraints

No implementar todavía componentes visuales ni traducciones completas. **PARAR y reportar si**
un texto oculta el riesgo, mezcla cancelación con rechazo o
requiere exponer un secreto para completar el flujo.
