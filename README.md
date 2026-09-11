# Local Secure Forms for Agent CLIs (LSFA)

LSFA es una propuesta experimental para que un agente que opera una CLI pueda
solicitar datos al usuario mediante un formulario local y contextual, sin
exponer secretos al agente ni obligar al usuario a copiar comandos complejos.

La CLI presenta la interfaz apropiada —gráfica, terminal o headless—, valida
los datos, ejecuta las comprobaciones necesarias y guarda los secretos en el
almacén seguro del sistema operativo. El agente recibe únicamente un resultado
estructurado.

## Caso de referencia

La primera implementación es [email-agent-kdd](https://github.com/MauricioPerera/email-agent-kdd),
que usa este flujo para configurar cuentas IMAP/SMTP, comprobar la conexión y
guardar la credencial sin devolver la contraseña al agente.

## Documentos

- [SPEC.md](SPEC.md): protocolo y requisitos de conformidad.
- [THREAT-MODEL.md](THREAT-MODEL.md): límites, amenazas y mitigaciones.
- [SECURITY.md](SECURITY.md): reglas de seguridad para implementaciones.
- [examples/connect-email.json](examples/connect-email.json): solicitud de ejemplo.

## Estado

Esta es una propuesta experimental, no un estándar aprobado. Se buscan
implementaciones, críticas y casos de uso antes de proponer una extensión a
protocolos de agentes existentes.
