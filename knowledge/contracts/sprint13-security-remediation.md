---
type: KDD Task Contract
task: sprint13_security_remediation
status: implemented
repository: MauricioPerera/local-secure-forms
audit_commit: fed1723a6e8c73074765fabb1e0fa80bea421a8f
---

# Sprint 13 — Garantías de seguridad ejecutables en LSFA

## Objetivo

Corregir los cinco hallazgos de la auditoría del SDK de referencia y alinear
implementación, esquemas, validadores, documentación y pruebas. El resultado
debe impedir filtraciones por el canal de resultados, ejecución de solicitudes
vencidas o reutilizadas, degradación de confirmaciones y ejecución de entradas
inválidas. El kit debe detectar incumplimientos reales.

Este contrato está incorporado a knowledge/contracts y a su índice en el
repositorio indicado. No corresponde al repositorio email-agent-kdd.

## Secuencia KDD

Para cada hallazgo: reproducir el fallo antes del cambio, establecer el contrato
y las decisiones, implementar, ejecutar pruebas positivas y adversarias, y
registrar evidencia. No modificar expectativas para ocultar fallos.

### 1. Frontera de salida segura — prioridad alta

- Sustituir la devolución libre de execute(values) por resultados explícitos
  y validados; limitar checks y referencias a tipos y campos permitidos.
- Rechazar valores sensibles en resultados anidados y errores; no depender
  únicamente de buscar claves como password. Documentar el límite de confianza:
  un callback arbitrario con acceso al secreto no queda aislado por validación.
- Separar resultado de ejecución y serialización: un error posterior a un
  efecto externo no autoriza repetición automática de la operación.
- Aceptación: ejecutores que devuelven el diccionario de entrada, secretos bajo
  otras claves o estructuras anidadas no los exponen; errores de captura,
  confirmación y ejecución no filtran datos. Resultados legítimos siguen útiles.
- Verificar con señuelos sintéticos stdout, stderr y logs emitidos por el SDK.

### 2. Caducidad y consumo único — prioridad alta

- Establecer identidad y plazo verificables de la solicitud y autorización.
- Comprobar caducidad antes de capturar y después de captura/confirmación,
  inmediatamente antes del efecto externo; rechazar confirmaciones vencidas.
- Ligar autorización a request_id, operación, destino, alcance y contenido
  mostrado. Un cambio invalida la autorización.
- Consumir la autorización atómicamente antes de ejecutar; conservar el estado
  frente a concurrencia y reinicio. Definir recuperación sin reejecución ciega
  cuando el proceso cae o el efecto externo queda incierto.
- Aceptación: expiración durante formulario o confirmación, replay secuencial,
  concurrencia y reinicio no permiten ejecutar una autorización más de una vez;
  una solicitud nueva válida mantiene el flujo normal.

### 3. Política mínima por operación — prioridad alta

- El cliente confiable registra operaciones y riesgo mínimo; la solicitud del
  agente no puede reducirlos. Operaciones no registradas se rechazan.
- purge exige irreversible y pin_and_totp; mantener soft_delete y restore
  separados. No considerar el simple nombre del método prueba de autenticación.
- Definir la interfaz del verificador local confiable y las responsabilidades
  del integrador; no simular como implementados captura GUI, PIN o TOTP reales.
- Aceptación: purge con riesgo low/medium/high, confirmación básica, prueba
  ausente, vencida o de otra operación no ejecuta; política legítima sí permite
  proceder. Aplicar las mismas reglas a todos los adaptadores de referencia.

### 4. Validación anterior a efectos — prioridad alta

- Validar solicitudes y valores: nombres únicos, sensibilidad, tipos, campos
  obligatorios, null/vacíos, extras y límites. Rechazar booleanos como enteros.
- Resolver las reglas y preflight mediante un registro de validadores del
  cliente, sin eval ni ejecución de instrucciones provenientes del agente.
- Validar estructura antes de preflight y persistencia; preflight fallido
  impide ejecutar/persistir. Documentar los efectos permitidos del preflight.
- Aceptación: None en password obligatorio, tipos erróneos, campos extra,
  duplicados, validadores desconocidos y preflight fallido no llegan al ejecutor.

### 5. Conformidad verificable — prioridad media

- Validar esquemas y ejemplos con un motor JSON Schema compatible; componer
  confirmation/lifecycle con request y aplicar las restricciones entre campos.
- Prohibir defaults sensibles y combinaciones operación/riesgo/método inválidas.
- Alinear modelos Python, esquemas, SPEC y ejemplos; preservar request_id y
  riesgo efectivo en resultados para correlacionar la decisión.
- Añadir casos negativos a CI: deben fallar por comportamiento, no solo por
  ausencia de una palabra o archivo. Separar validación estructural de pruebas
  de seguridad y de cualquier declaración de conformidad de un integrador.
- Aceptación: los cinco fallos de auditoría son detectados; datos válidos pasan
  y cada entrada inválida obtiene diagnóstico estable sin secretos.

## Entregables

- SDK y esquemas corregidos, con migración documentada si cambia la API.
- Contratos KDD afectados e índice actualizados.
- Pruebas reproducibles positivas/adversarias y CI Windows, Linux y macOS.
- SPEC, SECURITY, THREAT-MODEL, IMPLEMENTATION-GUIDE y CONFORMANCE consistentes
  con las garantías implementadas y sus límites.
- Reporte de cierre con hallazgo, reproducción, corrección, pruebas, commit
  validado y enlaces CI; PR revisable usando gh.

## Definición de terminado

Los cinco hallazgos están corregidos y cuentan con evidencia de regresión.
Suite completa, validadores reales y matriz CI aprobados en el commit final.
La revisión final contrasta cada criterio con código y pruebas, no solo con el
conteo de tests. No declarar protección contra un host o callback comprometido
fuera del límite de confianza documentado. El objetivo no se cierra con trabajo
pendiente, pruebas omitidas que oculten un fallo o garantías sin evidencia.

## Alcance y restricciones

Solo local-secure-forms. Usar secretos, identidades, servicios y efectos externos
sintéticos; no leer credenciales reales, enviar correo, borrar datos del usuario
ni modificar email-agent-kdd. No implementar nuevas interfaces visuales ni
convertir la propuesta experimental en una certificación. No publicar detalles
de seguridad en issues públicos antes de disponer de la corrección.
