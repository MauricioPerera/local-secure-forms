# Solicitud de retroalimentación para LSFA 0.2

LSFA propone formularios locales y contextuales para que agentes de terminal
soliciten datos sensibles sin leerlos. Antes de proponer una versión estable
queremos validar si el modelo es útil, seguro e interoperable.

## Preguntas para implementadores

- ¿Qué interfaz usas: GUI, terminal, headless o una combinación?
- ¿Qué almacén seguro y plataformas soportas?
- ¿El contrato `request`/`result` cubre tus integraciones?
- ¿Qué acciones requieren PIN, segundo factor o confirmación adicional?
- ¿Qué información mínima necesita el agente para continuar sin ver secretos?
- ¿Qué parte del flujo causa más fricción o errores?

## Preguntas para revisores de seguridad

- ¿Detectas una ruta por la que un secreto pueda aparecer en logs, procesos,
  temporales, telemetría o resultados?
- ¿La confirmación humana es resistente a solicitudes ambiguas o engañosas?
- ¿El modelo de `soft_delete`, `restore` y `purge` separa correctamente las
  acciones reversibles de las irreversibles?
- ¿Qué amenazas faltan en `THREAT-MODEL.md`?

## Cómo responder

Abre un issue en GitHub usando un ejemplo sintético. Para vulnerabilidades,
consulta `SECURITY.md` y no publiques detalles explotables antes de coordinar
la corrección.

LSFA 0.2 es un borrador experimental; los comentarios pueden producir cambios
incompatibles antes de una eventual propuesta de estándar.
