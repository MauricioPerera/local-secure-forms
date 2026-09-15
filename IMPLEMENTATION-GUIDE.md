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
5. Devolver solo checks booleanos registrados y estados de existencia.
6. Añadir confirmación humana explícita y los factores exigidos por riesgo.
7. Ejecutar el kit de conformidad antes de publicar una versión.

## Presentación dinámica opcional

Para una interfaz generada, renderiza directamente los `fields`. Para formato
dinámico, acepta únicamente `PresentationSpec`: sus secciones organizan todos
los campos sin cambiar tipos o sensibilidad. Para una experiencia especializada,
registra localmente un `PresentationSpec` en `PresentationRegistry` y permite
que la solicitud lo seleccione por nombre. Un perfil desconocido se rechaza.

El renderer puede ignorar sugerencias que no soporte y volver a `auto`. Debe
usar controles propios para secretos y una superficie separada para confirmar.
No conviertas presentación en HTML, callbacks ni código proporcionado por el
agente.

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
python -m pip install -r requirements-dev.txt
python scripts/validate_conformance.py
python scripts/validate_examples.py
python -m pytest tests -q
```

Publica la versión, plataforma, adaptadores disponibles y cualquier excepción
conocida. LSFA 0.2 es experimental y esta declaración no es una certificación
externa.

## API de referencia actual

Seguir [SDK-MIGRATION.md](SDK-MIGRATION.md): registrar `OperationPolicy`, usar
un `AuthorizationStore` persistente compartido, emitir con `LocalClient.issue`
y ejecutar `adapter.run(ticket)`. El antiguo `run(request, execute)` se retiró
porque no proporcionaba una frontera de autorización verificable.

No copiar los verificadores sintéticos de tests para producción. La UI y los
factores reales siguen siendo responsabilidad del integrador. `accepted`
requiere retorno normal del ejecutor y salida válida; un error posterior a un
posible efecto deja la autorización consumida y requiere investigación.
