---
type: KDD Task Contract
task: sprint2_protocol_base
status: draft
target: specs/lsfa-request.md
tests: tests/frozen_sprint2_protocol.py
---

# Objetivo 2 — Protocolo base LSFA

## Intent

Definir la forma mínima y portable de una solicitud y un resultado LSFA.

## Interface

Entradas: operación, propósito, campos, validación y expiración.
Salidas: solicitud validable y resultado estructurado sin secretos.

## Invariants

- `operation`, `purpose`, `fields`, `validation` y `expires_in_seconds` son
  obligatorios.
- Los estados son exactamente los seis definidos por la especificación.
- Los identificadores son opacos y no contienen secretos.
- Una solicitud expirada no puede ejecutar efectos.
- Los resultados no contienen valores de campos secretos.

## Examples

- `connect_email` devuelve verificaciones IMAP/SMTP y una referencia opaca.
- `cancelled` indica que el usuario cerró o canceló el formulario.
- `expired` indica que venció el tiempo antes de confirmar.

## Do / Don't

- Do: validar el esquema antes de presentar o ejecutar.
- Do: usar `checks` y `stored_refs` para estados verificables.
- Don't: devolver contraseñas, PIN, tokens o códigos en cualquier resultado.
- Don't: tratar `declined`, `cancelled` y `expired` como aceptación.

## Tests

`python -m pytest tests/frozen_sprint2_protocol.py -q`

## Constraints

Los esquemas son independientes del lenguaje y del transporte. No incorporar
todavía lógica de UI, almacenamiento ni proveedores externos. **PARAR y reportar si**
un diseño necesita incluir un secreto en el resultado o ejecutar
una solicitud después de su expiración.
