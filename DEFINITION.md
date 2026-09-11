---
type: LSFA Project Definition
id: lsfa-definition
status: draft
version: 0.1
---

# Definición del producto LSFA

## Problema

Los agentes que operan una terminal necesitan datos sensibles para completar
operaciones, pero pedirlos por chat o mediante comandos complejos expone
secretos y aumenta los errores del usuario.

## Solución

LSFA define una frontera local en la que un agente solicita una operación, un
cliente presenta únicamente los campos necesarios, valida los datos y ejecuta
la acción. El agente recibe estado estructurado, nunca el secreto.

## Usuarios y actores

- **Usuario:** revisa, completa, confirma, rechaza o cancela.
- **Agente:** expresa intención y consume el resultado; no controla secretos
  ni confirmaciones.
- **Cliente LSFA:** coordina presentación, validación, confirmación y ejecución.
- **Adaptador de presentación:** GUI, terminal o modo manual/headless.
- **Almacén seguro:** conserva secretos fuera del contexto del agente.
- **Sistema externo:** correo, archivos u otro servicio afectado por la acción.

## Alcance inicial

LSFA cubrirá captura segura de datos, validación, confirmación graduada,
almacenamiento seguro, acciones reversibles e integración con agentes locales.
El primer caso de referencia será la configuración y operación de correo.

## Fuera de alcance

LSFA no define un modelo de agente, un proveedor de identidad universal, un
almacén remoto de secretos, una UI única ni un proveedor específico de correo.

## Principios no negociables

1. El secreto no aparece en el resultado, argumentos, logs, historial ni
   telemetría.
2. El agente no puede confirmar acciones en nombre del usuario.
3. La cancelación y el rechazo son estados distintos de la aceptación.
4. Las acciones irreversibles requieren controles reforzados.
5. GUI, terminal y configuración manual comparten las mismas reglas.
