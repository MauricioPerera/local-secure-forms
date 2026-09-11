---
type: LSFA Conformance Guide
id: lsfa-conformance
version: 0.2
status: draft
---

# Kit de conformidad LSFA

Una implementación puede declararse conforme al nivel experimental LSFA 0.2
cuando valida los esquemas, ejecuta las pruebas del protocolo y demuestra que
no expone secretos.

## Nivel 1 — Protocolo

- valida solicitudes y resultados contra `schemas/`;
- reconoce los seis estados normativos;
- aplica expiración y confirmación por riesgo;
- mantiene `soft_delete`, `restore` y `purge` separados;
- ejecuta los ejemplos y pruebas congeladas.

## Nivel 2 — Seguridad

- no incluye secretos en resultados, argumentos, logs o temporales;
- no permite confirmación por parte del agente;
- invalida confirmaciones consumidas o expiradas;
- ofrece recuperación o informa estados parciales;
- mantiene controles equivalentes en GUI, terminal y modo manual.

La matriz de referencia ejecuta estas comprobaciones en Linux y Windows;
otras plataformas pueden añadir una variante equivalente.

## Verificación

```text
python scripts/validate_conformance.py
python -m pytest tests -q
```

La conformidad es una declaración sobre una versión concreta y no implica una
certificación externa ni aprobación como estándar.
