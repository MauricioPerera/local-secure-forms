# LSFA Threat Model

## Activos

- Contraseñas, tokens y claves API.
- Identidad y configuración privada del usuario.
- Autorización para ejecutar acciones externas.

## Amenazas principales

- El agente imprime el secreto o lo incluye en un comando.
- Un log, historial de shell o archivo temporal conserva el secreto.
- Una instrucción maliciosa induce al agente a confirmar una acción.
- Un formulario falso solicita más datos de los necesarios.
- Una composición visual oculta campos, suplanta la confirmación o ejecuta código.
- Una respuesta de error devuelve información sensible.
- Un proceso local malicioso observa la máquina del usuario.
- Un agente intenta reducir el riesgo mínimo o reutilizar una confirmación anterior.
- Un borrado aparentemente reversible termina siendo permanente sin aviso.

## Mitigaciones

- Separar el proceso del formulario del canal del agente.
- Declarar sensibilidad por campo y bloquear secretos en resultados.
- Usar almacenes seguros nativos del sistema operativo.
- Validar propósito, esquema, expiración y operación.
- Limitar la composición a secciones inertes que cubren exactamente los campos
  de la política y resolver perfiles solo desde un registro local.
- Mostrar al usuario qué aplicación solicita el dato y por qué.
- Exigir confirmación humana independiente.
- Usar códigos de error estables y sanitizados.
- Probar explícitamente ausencia de secretos en argv, logs y salidas.
- Asociar cada operación con un nivel de riesgo y una confirmación no
  delegable al agente.
- Separar `soft_delete`, `restore` y `purge`, con controles crecientes.
- Expirar solicitudes, PIN y códigos de segundo factor para impedir replay.

## Límites

LSFA reduce la exposición accidental al agente y a sus canales. No puede
garantizar protección contra malware con control total del equipo, keyloggers,
captura de pantalla o un usuario que voluntariamente comparta el secreto.

## Frontera implementada en el Sprint 13

Se confían el registro local de operaciones, callbacks, verificador de factores,
reloj y base SQLite persistente con permisos apropiados. El agente solo aporta
datos; no comparte sus privilegios ni ejecuta código dentro de ese cliente.
Una huella HMAC liga solicitud y valores; la reserva atómica evita dos efectos
con la misma autorización, incluso ante concurrencia o caída del proceso.

La base guarda IDs, plazos, estados y huellas con clave, no valores capturados.
Un proceso caído puede dejar una acción ambigua: no hay transacción distribuida
ni garantía de exactamente una ejecución. Restaurar una copia vieja de la base
o cambiar sus permisos puede invalidar la protección. Un nuevo ID tampoco
deduplica una acción de negocio ya realizada.

El SDK no implementa UI aislada ni verificación real de PIN/TOTP; exige un
verificador confiable. No impide que un callback comprometido filtre secretos
por red, logs o canales encubiertos. Ver [límites completos](SDK-MIGRATION.md).
