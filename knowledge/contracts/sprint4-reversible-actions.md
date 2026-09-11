---
type: KDD Task Contract
task: sprint4_reversible_actions
status: draft
target: specs/lsfa-lifecycle.md
tests: tests/frozen_sprint4_lifecycle.py
---

# Objetivo 4 — Acciones reversibles y borrado permanente

## Intent

Separar borrado reversible, restauración y borrado permanente para evitar
acciones destructivas ambiguas.

## Interface

Entradas: operación, referencia del recurso, riesgo y confirmación.
Salidas: estado de la operación, recuperación posible o `recovery_required`.

## Invariants

- `soft_delete`, `restore` y `purge` son operaciones diferentes.
- `purge` requiere `irreversible` y `pin_and_totp`.
- Un fallo parcial nunca se reporta como aceptación completa.
- La recuperación y el rollback se informan explícitamente.

## Examples

- Papelera: `soft_delete` seguido de `restore`.
- Eliminación definitiva: `purge` con advertencia y segundo factor.

## Do / Don't

- Do: mostrar recurso, alcance y permanencia antes de confirmar.
- Do: conservar una referencia de recuperación cuando sea posible.
- Don't: convertir `soft_delete` en `purge` automáticamente.
- Don't: ocultar un estado parcial o desconocido.

## Tests

`python -m pytest tests/frozen_sprint4_lifecycle.py -q`

## Constraints

No implementar todavía adaptadores de almacenamiento. **PARAR y reportar si**
una acción permanente puede ejecutarse sin confirmación reforzada o si un
estado parcial se presenta como exitoso.
