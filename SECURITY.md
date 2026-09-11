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
