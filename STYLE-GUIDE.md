---
type: LSFA Style Guide
id: lsfa-style-guide
version: 0.2
status: draft
---

# Guía de estilos LSFA

## Lenguaje

- Usar frases cortas y verbos directos.
- Explicar términos como IMAP, PIN o segundo factor la primera vez.
- Decir qué ocurrirá, sobre qué recurso y con qué permanencia.
- No usar miedo, urgencia artificial ni mayúsculas como única protección.

## Acciones

Usar siempre etiquetas inequívocas:

- `Sí, confirmar`: ejecuta la operación mostrada.
- `Rechazar`: niega la solicitud del agente.
- `Cancelar`: cierra el flujo sin aceptar ni rechazar la intención.
- `Volver`: regresa sin ejecutar efectos.

Para `purge`, la etiqueta debe incluir permanencia, por ejemplo `Eliminar
permanentemente`.

## Riesgo

Mostrar el nivel de riesgo junto al resumen y explicar el control requerido.
El usuario no debe tener que interpretar un código interno para comprender el
impacto.

## Consistencia técnica

Los adaptadores deben conservar los mismos nombres de campos, estados,
`error_code` y semántica de cancelación. Solo la presentación y la traducción
pueden variar entre plataformas.
