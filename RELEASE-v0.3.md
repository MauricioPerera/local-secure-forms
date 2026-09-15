# LSFA Presentation v0.3 (draft)

Esta extensión compatible con LSFA 0.2 añade presentación dinámica sin añadir
una superficie ejecutable al protocolo.

- `presentation` conserva las cadenas de LSFA 0.2.
- Un objeto declarativo puede seleccionar modo, idioma, tema y secciones.
- Cada layout debe cubrir exactamente una vez los campos de la política.
- Los perfiles se resuelven desde `PresentationRegistry`, instalado localmente.
- HTML, scripts, URLs, riesgo, validación y confirmación quedan fuera del formato.
- Secretos, PIN, TOTP y confirmación pertenecen al cliente confiable.
- GUI, terminal y manual usan el mismo ciclo de autorización.

La extensión sigue siendo experimental y no constituye una certificación de
seguridad de los renderers que la implementen.
