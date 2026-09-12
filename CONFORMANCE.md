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

La matriz de referencia ejecuta pruebas sintéticas en Linux, Windows y macOS.
Esto no prueba la UI, el almacén ni los factores de otra implementación.

## Verificación

```text
python -m pip install -r requirements-dev.txt
python scripts/validate_conformance.py
python -m pytest tests -q
```

La conformidad es una declaración sobre una versión concreta y no implica una
certificación externa ni aprobación como estándar.

Desde el Sprint 13 los scripts aplican Draft 2020-12, referencias locales,
formatos de fechas y restricciones entre campos; no solo comprueban archivos.
Su resultado es **estructural**, no una declaración automática de Nivel 2.
Las pruebas `test_*.py` y `frozen_*.py` se descubren juntas y cubren efectos
sintéticos, expiración, replay, concurrencia y recuperación tras caída real.
Cada integrador debe aportar evidencia adicional para sus componentes reales.

La migración y las precondiciones de confianza están en
[SDK-MIGRATION.md](SDK-MIGRATION.md).
