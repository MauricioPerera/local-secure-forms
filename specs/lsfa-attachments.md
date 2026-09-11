# Extensión LSFA 0.2: adjuntos

Esta extensión define cómo solicitar una operación que materializa bytes de un
adjunto en almacenamiento local. Listar metadatos no requiere esta solicitud;
extraer contenido sí requiere autorización explícita del usuario.

## Solicitud

La operación usa el contrato `request` existente:

- `operation`: `extract_attachment`;
- `risk`: `medium` como mínimo;
- `fields`: referencias opacas al mensaje y al adjunto, índice o hash, y un
  destino local validado;
- `validation.preflight`: `attachment_reference_and_destination`;
- `confirmation.method`: `user_accept` o una política más fuerte;
- `confirmation.single_use`: `true`.

El agente puede preparar referencias y mostrar metadatos, pero no puede incluir
los bytes, seleccionar una ruta fuera del almacén autorizado ni confirmar por
el usuario.

## Reglas de almacenamiento

- Sin autorización no se escribe ningún byte.
- El nombre recibido por correo es dato no confiable y nunca compone una ruta.
- El blob se direcciona por un SHA-256 validado; se verifica hash, tamaño y
  colisión antes y después de escribir.
- Se aplican límites por archivo, presupuesto total y lista de tipos/extensiones
  permitidos. Un rechazo conserva metadatos y explica un código estable.
- La segunda extracción del mismo hash es idempotente si el blob coincide.

## Resultado

El cliente devuelve `accepted` con un `stored_ref` opaco y metadatos no
sensibles, o un estado terminal (`declined`, `cancelled`, `invalid`, `failed`,
`expired`). Nunca devuelve bytes, secretos, tokens ni la ruta absoluta del
usuario. Los códigos recomendados son `confirmation-required`,
`type-not-allowed`, `size-limit-exceeded`, `hash-mismatch` y `unsafe-path`.

La extensión se aplica igual en GUI, terminal y headless; este último requiere
una política explícita para el destino.
