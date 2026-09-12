# Seguridad

Las implementaciones deben tratar todos los valores de tipo `secret` como
datos no retornables. No deben aparecer en argumentos, prompts, stdout, stderr,
logs, telemetría, archivos temporales ni mensajes de excepción.

Los reportes de seguridad deben abrirse de forma privada con los mantenedores
antes de publicar detalles reproducibles. Las propuestas y ejemplos no deben
contener credenciales reales ni datos personales reales.

## Confirmaciones y acciones destructivas

El cliente LSFA es el único que puede confirmar una acción. El agente puede
solicitarla, pero no puede generar un `Sí`, introducir un PIN ni aprobar un
segundo factor. La confirmación debe mostrar operación, destino, alcance y
nivel de riesgo.

Las acciones de bajo riesgo pueden usar confirmación visible. Las de alto
riesgo requieren PIN local y las irreversibles requieren además un segundo
factor. Los códigos no deben aparecer en logs, argumentos, historial,
resultados ni telemetría.

Siempre que sea posible, el borrado debe ser reversible (`soft_delete` y
`restore`). El borrado permanente (`purge`) debe ser una operación distinta,
con advertencia clara y confirmación reforzada.

## Garantías y límites del SDK de referencia

El Sprint 13 incorpora política local por operación, entradas acotadas,
confirmación ligada al contenido, caducidad y reserva atómica persistente.
Los errores emitidos por el SDK no incluyen texto de excepciones de callbacks;
los resultados de ejecución solo aceptan checks booleanos registrados.

Esto no aísla código Python arbitrario que ya puede leer el secreto. Captura,
preflight, ejecutor y verificador pertenecen al cliente confiable: sus propios
logs o accesos al sistema no son bloqueados por el SDK. GUI, PIN, TOTP, permisos
del almacén y aislamiento del agente deben implementarse y probarse aparte.

Después de un fallo con `values_consumed=True`, no repetir automáticamente:
la acción puede haberse realizado. Conservar el registro, inspeccionar el
efecto externo y solicitar una nueva aprobación si procede. Véase
[migración y recuperación](SDK-MIGRATION.md).
