---
type: KDD Task Contract
task: sprint9_conformance_kit
status: draft
target: scripts/validate_conformance.py
tests: tests/frozen_sprint9_conformance.py
---

# Objetivo 9 — Kit de conformidad

## Intent

Permitir que una implementación LSFA compruebe de forma determinista sus
artefactos mínimos y publique evidencia reproducible.

## Interface

Entradas: esquemas, documentos y ejemplos del repositorio.
Salida: código 0 y resumen estructural, o error explícito sin secretos.

## Invariants

- Los cuatro esquemas normativos existen y son JSON válido.
- Las guías de seguridad y UX están presentes.
- Existe al menos un ejemplo validable.
- El validador no usa red ni modelos.

## Examples

- CI ejecuta el validador y las pruebas congeladas.
- Una implementación ausente falla con un mensaje genérico.

## Do / Don't

- Do: verificar una versión concreta y conservar evidencia.
- Do: ejecutar en Linux y Windows.
- Don't: llamar servicios externos para validar.
- Don't: imprimir contenido sensible durante la verificación.

## Tests

`python -m pytest tests/frozen_sprint9_conformance.py -q`

## Constraints

El kit no certifica una implementación ni sustituye una auditoría externa.
**PARAR y reportar si** la validación necesita secretos, red o ejecución de
acciones externas.

## Actualización Sprint 13

Aplicar Draft 2020-12 con referencias locales a confirmation/lifecycle y
validación de formatos; dependencias en `requirements-dev.txt`. Añadir pruebas
negativas de comportamiento y descubrir tanto `test_*.py` como `frozen_*.py`.
La matriz incluye macOS además de Linux y Windows. No confundir el resultado
estructural con evidencia sobre la UI o el verificador real de un integrador.
