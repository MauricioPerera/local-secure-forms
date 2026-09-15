---
type: LSFA Protocol Specification
id: lsfa-presentation
version: 0.3
status: draft
---

# Adaptadores de presentación LSFA

Una implementación puede presentar la solicitud como formulario gráfico,
preguntas de terminal o configuración manual/headless. Los tres modos deben
usar la misma solicitud, política de riesgo, validación y resultado.

El adaptador recibe valores dentro del proceso local y los entrega directamente
al ejecutor autorizado. No debe serializarlos al agente ni imprimirlos. Un
callback de colección puede devolver `null` para cancelar; la confirmación
debe devolver una decisión explícita antes de ejecutar.

Desde el Sprint 13 se usa `adapter.run(client.issue(request))`, con política y
verificador registrados en el cliente. Una decisión positiva requiere recibo
verificado, no un booleano; `False`/`None` pueden rechazar. El callback recibe
una copia privada del contexto, nunca propiedad sobre el snapshot ejecutado.

La ausencia de GUI no autoriza degradar la seguridad: terminal y manual deben
ocultar secretos, respetar expiración y exigir el mismo método de confirmación.

Los adaptadores del SDK no implementan esas interfaces visuales ni factores
reales; aplican un flujo común a callbacks confiables. No ejecutan headless
automáticamente ni convierten ausencia de UI en autorización.

## Presentación declarativa 0.3

`presentation` conserva las cadenas de 0.2 y también admite un objeto con
`mode`, `locale`, `theme` y, de forma mutuamente exclusiva, `layout` o
`profile`. Es una sugerencia inerte: no puede contener HTML, scripts, URLs,
acciones, validadores, riesgo ni confirmación.

Un `layout` contiene secciones con título, estado inicial plegado y nombres de
campos. Debe incluir exactamente una vez todos los campos autorizados por la
política. No puede añadir, ocultar ni repetir campos. El cliente puede ignorar
el orden, tema, idioma o agrupación cuando su plataforma no los soporte, pero
debe conservar todos los campos y su semántica.

Un `profile` identifica una plantilla instalada en el registro del cliente.
La solicitud solo aporta el nombre: nunca transporta código o contenido de la
plantilla. Un perfil desconocido falla cerrado. Perfil y layout inline no se
pueden combinar.

Los controles `secret`, PIN y segundo factor, así como el resumen y los botones
de confirmación, pertenecen al chrome confiable del cliente. Una plantilla no
puede renderizarlos, reemplazarlos ni alterar su prominencia. GUI, terminal y
manual/headless derivan de la misma solicitud; la falta de soporte visual
degrada a generación automática, nunca a menor seguridad.
