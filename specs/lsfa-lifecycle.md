---
type: LSFA Protocol Specification
id: lsfa-lifecycle
version: 0.2
status: draft
---

# Ciclo de vida y borrado LSFA

Las acciones destructivas se modelan como operaciones distintas:

1. `soft_delete`: mueve o marca el recurso como eliminado y conserva una
   referencia de recuperación.
2. `restore`: recupera un recurso que sigue en la papelera.
3. `purge`: elimina permanentemente un recurso y no promete recuperación.

`soft_delete` y `restore` deben poder cancelarse antes del efecto externo y
usar confirmación visible. `purge` debe declarar `risk: irreversible`, usar
`pin_and_totp` y mostrar el recurso, alcance y advertencia de permanencia.

Si falla una etapa de preparación, no debe ejecutarse el efecto. Si falla una
etapa posterior a un cambio parcial, el adaptador debe intentar rollback o
devolver `failed` con `recovery_required: true`; nunca debe reportar
`accepted` mientras el estado sea desconocido.
