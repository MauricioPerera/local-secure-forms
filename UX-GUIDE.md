---
type: LSFA UX Guide
id: lsfa-ux-guide
version: 0.2
status: draft
---

# Guía UX de LSFA

## Principio central

La interfaz debe pedir solo lo necesario para la operación actual. El usuario
no debe copiar comandos, descubrir nombres técnicos ni pegar secretos en una
terminal para completar un flujo que el cliente puede presentar localmente.

## Secuencia recomendada

1. Explicar quién solicita la acción y para qué.
2. Mostrar campos agrupados por propósito, con ejemplos y valores por defecto
   seguros.
3. Validar cada campo cerca del lugar donde se captura.
4. Ejecutar preflight antes de guardar o producir efectos externos.
5. Mostrar un resumen de operación, destino, alcance y riesgo.
6. Ofrecer `Sí, confirmar`, `Rechazar` y `Cancelar` como acciones distintas.
7. Mostrar el resultado sin secretos y explicar el siguiente paso.

## Estados y errores

Los estados deben ser visibles y distinguibles: aceptado, rechazado,
cancelado, inválido, fallido y expirado. Los errores deben indicar cómo
corregir el problema sin mostrar secretos, trazas ni detalles internos.

## Modos

- GUI: controles accesibles, foco visible y campos secretos ocultos.
- Terminal: preguntas simples, entrada secreta sin eco y sin comandos para
  copiar.
- Manual/headless: instrucciones legibles, confirmación explícita y ninguna
  degradación silenciosa de seguridad.

## Idiomas

La implementación debe separar texto de lógica y permitir al menos español,
inglés y portugués. Los nombres de estados y códigos de error deben conservar
una forma estable para agentes y scripts.
