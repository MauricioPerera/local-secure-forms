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
- Una respuesta de error devuelve información sensible.
- Un proceso local malicioso observa la máquina del usuario.

## Mitigaciones

- Separar el proceso del formulario del canal del agente.
- Declarar sensibilidad por campo y bloquear secretos en resultados.
- Usar almacenes seguros nativos del sistema operativo.
- Validar propósito, esquema, expiración y operación.
- Mostrar al usuario qué aplicación solicita el dato y por qué.
- Exigir confirmación humana independiente.
- Usar códigos de error estables y sanitizados.
- Probar explícitamente ausencia de secretos en argv, logs y salidas.

## Límites

LSFA reduce la exposición accidental al agente y a sus canales. No puede
garantizar protección contra malware con control total del equipo, keyloggers,
captura de pantalla o un usuario que voluntariamente comparta el secreto.
