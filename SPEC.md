# LSFA Specification 0.2

## Propósito

LSFA define una frontera local entre un agente y un usuario. El agente expresa
qué operación necesita y qué campos son necesarios; el cliente local decide
cómo pedirlos y ejecuta la operación sin filtrar campos sensibles.

LSFA no define un modelo de agente, un gestor de secretos ni una interfaz
visual universal. Puede transportarse por stdio, sockets locales, MCP, ACP u
otro canal.

## Actores

- Agente: solicita una operación y recibe el resultado.
- Cliente LSFA: muestra el formulario, valida y ejecuta la operación.
- Usuario: revisa, completa, acepta, rechaza o cancela.
- Almacén seguro: conserva secretos fuera del contexto del agente.

## Solicitud

Una solicitud debe incluir `operation`, `purpose`, `fields`, `presentation`,
`validation` y `expires_in_seconds`. Cada campo debe declarar `name`, `type` y
`sensitivity`. Los campos `secret` nunca pueden aparecer en el resultado.

```json
{
  "operation": "connect_email",
  "purpose": "Configurar una cuenta de correo",
  "presentation": "auto",
  "fields": [
    {"name": "email", "type": "email", "sensitivity": "private", "required": true},
    {"name": "password", "type": "secret", "sensitivity": "secret", "required": true},
    {"name": "imap_host", "type": "hostname", "sensitivity": "public", "required": true},
    {"name": "imap_port", "type": "integer", "sensitivity": "public", "default": 993}
  ],
  "validation": {"preflight": "imap_authentication"},
  "expires_in_seconds": 600
}
```

## Modos

- `form`: formulario gráfico local.
- `terminal`: preguntas interactivas con entrada secreta oculta.
- `headless`: referencia previamente autorizada a un almacén de secretos.
- `auto`: gráfico si existe UI, terminal si existe TTY y headless solo con
  política explícita.

El usuario no debe copiar comandos generados por el agente para completar el
flujo.

## Resultado

Los estados son `accepted`, `declined`, `cancelled`, `invalid`, `failed` y
`expired`. Un resultado exitoso puede incluir verificaciones y un identificador
opaco, pero nunca el valor de un campo secreto.

```json
{
  "status": "accepted",
  "operation": "connect_email",
  "credential_stored": true,
  "imap_verified": true,
  "smtp_verified": true
}
```

## Validación y confirmación

El cliente debe validar primero el esquema y después ejecutar el preflight de
la operación. En correo, esto significa autenticar IMAP y SMTP sin descargar
mensajes ni enviar correo. Guardar un secreto, enviar, borrar o desvincular
requiere confirmación humana independiente del agente.

Cerrar el formulario equivale a `cancelled`, no a aceptar.

## Niveles de riesgo y confirmación

Toda solicitud puede declarar `risk` como `low`, `medium`, `high` o
`irreversible`. El cliente debe mostrar el riesgo y la acción concreta antes
de ejecutar cualquier efecto externo. Las acciones de alto riesgo requieren
PIN local; las irreversibles requieren además un segundo factor configurado
por el usuario, como TOTP. El agente nunca puede confirmar, ver el PIN o
recibir el código.

La interfaz puede ofrecer un botón `Sí, confirmar` para reducir fricción,
pero debe mostrar operación, destino y alcance en el mismo paso. Toda
confirmación expira y no puede reutilizarse.

## Acciones reversibles

Las operaciones que lo permitan deben implementar `soft_delete` y `restore`.
El borrado permanente (`purge`) debe ser una operación separada, declarar
`risk: irreversible` y requerir confirmación reforzada.

## Resultado estructurado

El cliente puede devolver `request_id`, `risk`, `checks`, `stored_refs` y
`error_code`, además de `status` y `operation`. `stored_refs` contiene solo
identificadores opacos o estados de existencia; nunca secretos, PIN, tokens,
códigos ni valores completos de campos sensibles.

## Integración manual y asistida

El mismo contrato funciona cuando el usuario inicia el formulario manualmente
o cuando un agente solicita abrirlo. Un entorno sin UI puede usar terminal o
configuración manual, manteniendo las mismas validaciones y confirmaciones.

## Requisitos de conformidad

Una implementación conforme debe demostrar que:

1. No coloca secretos en argumentos, stdout, stderr, logs o archivos temporales.
2. Distingue aceptación, rechazo, cancelación, fallo y expiración.
3. Valida entradas y operaciones antes de persistir.
4. Usa el almacén seguro nativo cuando está disponible.
5. Ofrece fallback terminal o headless sin degradar silenciosamente la seguridad.
6. Mantiene confirmación humana para acciones sensibles o irreversibles.
7. Puede devolver presencia o estado del secreto sin devolver su contenido.
8. Declara el nivel de riesgo y aplica el método de confirmación correspondiente.
9. Separa las operaciones reversibles de las irreversibles y permite cancelar.
