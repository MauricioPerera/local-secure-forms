---
type: Architecture Knowledge
id: lsfa-boundaries
status: draft
---

# Límites de arquitectura

```text
Agente
  │ solicitud estructurada (sin secretos)
  ▼
Cliente LSFA ──► Presentación local (GUI / terminal / manual)
  │                         │
  │                         └── usuario confirma o cancela
  ├──► Validador y política de riesgo
  ├──► Almacén seguro nativo
  └──► Adaptador de operación ──► Sistema externo
  ▲
  └──── resultado estructurado sin secretos
```

El agente solo cruza la frontera con intención y resultado. Los secretos,
PIN, códigos de segundo factor y detalles de almacenamiento permanecen en el
cliente local.
