---
type: LSFA Integration Specification
id: lsfa-email-integration
version: 0.2
status: draft
---

# Integración de referencia con email-agent-kdd

La integración usa LSFA como frontera de captura y confirmación. El agente
solicita `connect_email` o `send_email`; el cliente local presenta la
solicitud, valida y entrega los valores únicamente al ejecutor de correo.

`connect_email` requiere preflight IMAP/SMTP antes de guardar la credencial y
devuelve solo referencias opacas y verificaciones. `send_email` muestra
destinatarios, asunto y alcance; requiere confirmación de alto riesgo antes de
llamar a SMTP. La contraseña nunca forma parte del resultado.

La configuración manual sigue siendo válida cuando no hay UI. El puente debe
mapear cancelación, rechazo, expiración y fallo a los estados LSFA sin
interpretarlos como aceptación.
