# Local Secure Forms for Agent CLIs (LSFA)

LSFA es una propuesta experimental para que un agente que opera una CLI pueda
solicitar datos al usuario mediante un formulario local y contextual, sin
exponer secretos al agente ni obligar al usuario a copiar comandos complejos.

La CLI presenta la interfaz apropiada —gráfica, terminal o headless—, valida
los datos, ejecuta las comprobaciones necesarias y guarda los secretos en el
almacén seguro del sistema operativo. El agente recibe únicamente un resultado
estructurado.

LSFA 0.2 añade niveles de riesgo, confirmaciones graduadas, PIN y segundo
factor para acciones de mayor impacto, además de separar borrado reversible de
borrado permanente. El formulario puede abrirse por iniciativa del usuario o
por solicitud de un agente, manteniendo el mismo límite de seguridad.

## Caso de referencia

La primera implementación es [email-agent-kdd](https://github.com/MauricioPerera/email-agent-kdd),
que usa este flujo para configurar cuentas IMAP/SMTP, comprobar la conexión y
guardar la credencial sin devolver la contraseña al agente.

## Documentos

- [SPEC.md](SPEC.md): protocolo y requisitos de conformidad.
- [THREAT-MODEL.md](THREAT-MODEL.md): límites, amenazas y mitigaciones.
- [SECURITY.md](SECURITY.md): reglas de seguridad para implementaciones.
- [IMPLEMENTATION-GUIDE.md](IMPLEMENTATION-GUIDE.md): ruta de adopción para implementadores.
- [SDK-MIGRATION.md](SDK-MIGRATION.md): API endurecida, pruebas y límites de confianza del SDK.
- [CONTRIBUTING.md](CONTRIBUTING.md): reglas para contribuir al protocolo.
- [FEEDBACK.md](FEEDBACK.md): preguntas y canal para retroalimentación.
- [specs/lsfa-attachments.md](specs/lsfa-attachments.md): extensión segura para adjuntos.
- [examples/connect-email.json](examples/connect-email.json): solicitud de ejemplo.
- [examples/send-email.json](examples/send-email.json): acción con confirmación de alto riesgo.
- `python scripts/validate_examples.py`: valida los ejemplos contra esquemas compuestos Draft 2020-12 (instalar `requirements-dev.txt`).
- [RELEASE-v0.2.md](RELEASE-v0.2.md): notas de la versión experimental 0.2.

## Estado

Esta es una propuesta experimental 0.2, no un estándar aprobado. Se buscan
implementaciones, críticas y casos de uso antes de proponer una extensión a
protocolos de agentes existentes.

El SDK de referencia ofrece modelos y adaptadores por callbacks; no implementa
por sí solo una GUI, un almacén del sistema ni autenticación PIN/TOTP real.
El endurecimiento del Sprint 13 requiere políticas locales y un verificador
confiable; su adopción cambia la API anterior de los adaptadores.
