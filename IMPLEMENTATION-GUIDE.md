# Guía de implementación LSFA 0.2

Esta guía permite construir una primera integración LSFA sin adoptar toda la
propuesta de una vez. La implementación debe conservar el límite principal:
el agente puede solicitar un formulario y recibir un resultado, pero nunca
recibe secretos ni puede confirmar por el usuario.

## Ruta mínima

1. Implementar `request` y `result` según `schemas/`.
2. Presentar el formulario en GUI, terminal o modo headless.
3. Validar localmente antes de persistir; los errores deben ser accionables.
4. Guardar secretos en el almacén seguro del sistema operativo.
5. Devolver solo identificadores, campos no sensibles y estado de validación.
6. Añadir confirmación explícita para acciones de riesgo medio o alto.
7. Ejecutar el kit de conformidad antes de publicar una versión.

## Reglas de seguridad

- Nunca coloques contraseñas, tokens o PIN en JSON de salida, logs, URLs,
  argumentos de shell o archivos temporales.
- La confirmación debe ser una acción humana verificable y de un solo uso.
- El agente puede explicar una acción, pero no pulsar “Sí”, introducir el PIN
  ni generar el segundo factor.
- En caso de duda, error de validación o estado parcial: detén la operación y
  reporta el siguiente paso al usuario.

## Adaptación por plataforma

La capa de presentación puede variar entre Windows, macOS, Linux y terminal,
pero el contrato y las garantías deben ser equivalentes. Una implementación
headless debe documentar cómo entrega la solicitud a una interfaz segura y no
debe convertir secretos en variables de entorno visibles.

## Declaración de conformidad

Para una versión concreta, ejecuta:

```text
python scripts/validate_conformance.py
python scripts/validate_examples.py
python -m pytest tests -q
```

Publica la versión, plataforma, adaptadores disponibles y cualquier excepción
conocida. LSFA 0.2 es experimental y esta declaración no es una certificación
externa.
