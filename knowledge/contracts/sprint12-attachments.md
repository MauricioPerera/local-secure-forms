---
type: KDD Contract
id: lsfa-sprint12-attachments
objective: Definir la extensión segura de extracción de adjuntos
status: frozen
---

# Contrato del Objetivo 12

## Resultado esperado

LSFA debe distinguir metadatos de contenido binario y permitir que una
implementación solicite la extracción de un adjunto con autorización humana,
límites verificables y rutas seguras.

## Criterios de aceptación

- listar metadatos no implica escribir bytes;
- `extract_attachment` exige confirmación de un solo uso;
- el agente no recibe bytes ni puede confirmar;
- el nombre del archivo nunca compone una ruta;
- hash, tamaño, tipo y presupuesto se validan antes de persistir;
- la operación es idempotente y devuelve una referencia opaca;
- GUI, terminal y headless conservan las mismas garantías.

## Seguridad

No se ejecutan descargas reales durante la validación. Si una prueba requiere
un servidor, credenciales o un archivo real, PARAR y reportar el bloqueo.
