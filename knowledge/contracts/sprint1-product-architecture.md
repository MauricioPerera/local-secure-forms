---
type: KDD Task Contract
task: sprint1_product_architecture
status: draft
target: DEFINITION.md
tests: tests/frozen_sprint1_definition.py
---

# Objetivo 1 — Definición de producto y arquitectura

## Intent

Fijar el problema, actores, alcance, límites y principios que gobernarán la
implementación de LSFA.

## Interface

Entradas: decisiones del producto y casos de uso de la CLI de correo.

Salidas: definición, nodos OKF enlazados y arquitectura conceptual.

## Invariants

- El agente nunca recibe secretos.
- La confirmación pertenece al usuario y al cliente LSFA.
- El alcance no depende de GUI, terminal ni proveedor de correo.
- `purge` no se confunde con una acción reversible.

## Examples

- Configurar IMAP/SMTP mediante un formulario local.
- Confirmar un envío mostrando destinatario y asunto.
- Cancelar una solicitud sin guardar datos.

## Do / Don't

- Do: documentar límites antes de implementar adaptadores.
- Do: conservar separación entre intención, secreto y efecto externo.
- Don't: convertir LSFA en un proveedor de identidad o correo.
- Don't: permitir que el agente escriba PIN o confirme acciones.

## Tests

`python -m pytest tests/frozen_sprint1_definition.py -q`

## Constraints

No incluir credenciales reales ni datos personales. No diseñar todavía el SDK,
el transporte ni una UI concreta. **PARAR y reportar si** una decisión exige
exponer secretos al agente o cambia el alcance sin actualizar este contrato.
