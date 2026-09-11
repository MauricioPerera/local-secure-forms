---
type: KDD Contract
id: lsfa-sprint10-public-proposal
objective: Publicar una guía de implementación y un canal reproducible de feedback
status: frozen
---

# Contrato del Objetivo 10

## Resultado esperado

El repositorio debe permitir que un implementador externo entienda la ruta
mínima de adopción, conozca las prohibiciones de seguridad y pueda reportar
interoperabilidad o riesgos sin compartir secretos.

## Entregables

- `IMPLEMENTATION-GUIDE.md` con ruta mínima, seguridad, plataformas y
  conformidad.
- `CONTRIBUTING.md` con reglas para cambios de protocolo y pruebas.
- `FEEDBACK.md` con preguntas de interoperabilidad, UX y seguridad.
- Índice KDD actualizado.
- Pruebas congeladas que impidan eliminar los puntos esenciales.

## Criterios de aceptación

- la guía declara que el agente no recibe secretos;
- la guía declara que el agente no confirma por el usuario;
- se documentan GUI, terminal y headless;
- existe un canal de feedback con ejemplos sintéticos;
- la batería de pruebas y los validadores siguen pasando.

## Seguridad

No se realizan envíos, borrados, conexiones externas ni uso de modelos para
validar este objetivo. Si una comprobación requiere datos reales, PARAR y
reportar el bloqueo.
