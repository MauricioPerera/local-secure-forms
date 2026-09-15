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

La extensión de presentación 0.3 permite que el formulario se genere y se
organice en el momento de mostrarlo. Una solicitud puede sugerir secciones,
idioma y tema, o seleccionar por nombre un perfil instalado localmente. Esa
presentación no puede añadir u ocultar campos, ejecutar HTML o scripts, cambiar
la política de riesgo ni controlar secretos o confirmaciones.

```json
{
  "presentation": {
    "mode": "form",
    "locale": "es",
    "theme": "system",
    "layout": {
      "sections": [
        {"id": "account", "title": "Tu cuenta", "fields": ["email", "password"]},
        {"id": "advanced", "title": "Configuración avanzada", "fields": ["imap_host", "imap_port"], "collapsed": true}
      ]
    }
  }
}
```

El cliente valida que todas las secciones cubran exactamente los campos de la
operación. Los perfiles especializados se registran mediante
`PresentationRegistry`; una referencia desconocida se rechaza de forma segura.

## Companion CloudPress + FastWebMCP

[`examples/cloudpress_loopback_broker.py`](examples/cloudpress_loopback_broker.py) es un companion de referencia para CloudPress. Escucha sólo en loopback, valida el origen configurado, liga la ejecución a una URL exacta de CloudPress y utiliza el ciclo de autorización de un solo uso del SDK. Requiere un verificador local real configurado mediante `--verifier modulo:funcion`; no incluye PIN/TOTP falso ni ejecuta acciones irreversibles sin una confirmación local conforme.

```text
python examples/cloudpress_loopback_broker.py --origin https://cms.example --verifier my_trusted_verifier:verify
```

El verificador recibe `(summary, method, binding, expires_at)` y, sólo después de realizar la autenticación local exigida, devuelve `VerifiedConfirmation(binding, method, expires_at)`. Un `True`, una cadena o un JSON no son confirmación válida. Para las acciones irreversibles, `method` es `pin_and_totp`; para recuperación TOTP, `pin`.

El mismo companion atiende la recuperación TOTP de CloudPress en la ruta loopback /v1/cloudpress/totp-recovery. CloudPress verifica primero el código de Google Authenticator o un código de respaldo; sólo entonces LSFA solicita el PIN local (riesgo high) y ejecuta el restablecimiento de contraseña ligado a la solicitud. Los códigos, contraseñas y tokens no se devuelven al agente.

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
- [specs/lsfa-presentation.md](specs/lsfa-presentation.md): presentación automática, composición declarativa y perfiles locales.
- [schemas/presentation.schema.json](schemas/presentation.schema.json): contrato JSON de presentación 0.3.
- [examples/dynamic-presentation.json](examples/dynamic-presentation.json): formulario organizado dinámicamente.
- [CONTRIBUTING.md](CONTRIBUTING.md): reglas para contribuir al protocolo.
- [FEEDBACK.md](FEEDBACK.md): preguntas y canal para retroalimentación.
- [specs/lsfa-attachments.md](specs/lsfa-attachments.md): extensión segura para adjuntos.
- [examples/connect-email.json](examples/connect-email.json): solicitud de ejemplo.
- [examples/send-email.json](examples/send-email.json): acción con confirmación de alto riesgo.
- `python scripts/validate_examples.py`: valida los ejemplos contra esquemas compuestos Draft 2020-12 (instalar `requirements-dev.txt`).
- Presentación declarativa 0.3: generación automática, secciones seguras o perfiles visuales registrados localmente, sin HTML ni código del agente.
- [RELEASE-v0.3.md](RELEASE-v0.3.md): contrato y límites de la extensión de presentación.
- [RELEASE-v0.2.md](RELEASE-v0.2.md): notas de la versión experimental 0.2.

## Estado

LSFA 0.2 y su extensión de presentación 0.3 son propuestas experimentales, no
un estándar aprobado. Se buscan
implementaciones, críticas y casos de uso antes de proponer una extensión a
protocolos de agentes existentes.

El SDK de referencia ofrece modelos y adaptadores por callbacks; no implementa
por sí solo una GUI, un almacén del sistema ni autenticación PIN/TOTP real.
El endurecimiento del Sprint 13 requiere políticas locales y un verificador
confiable; su adopción cambia la API anterior de los adaptadores.
