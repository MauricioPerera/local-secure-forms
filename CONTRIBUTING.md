# Participar en LSFA

LSFA es una propuesta experimental abierta a implementaciones y crítica
técnica. Las contribuciones deben explicar qué problema resuelven y conservar
la separación entre solicitud, presentación, validación, persistencia y
resultado.

## Cambios de protocolo

Para cambiar un campo, estado o regla de seguridad:

1. abre una discusión o issue describiendo el caso de uso;
2. actualiza la especificación, los esquemas y al menos un ejemplo;
3. añade o modifica una prueba congelada;
4. documenta impacto, compatibilidad y riesgos;
5. ejecuta la validación completa antes de abrir el pull request.

No se aceptan cambios que expongan secretos al agente o permitan que el agente
confirme acciones en nombre del usuario.

## Reportes de experiencia

Usa los issues para reportar interoperabilidad, UX, accesibilidad, seguridad o
casos de uso. No incluyas credenciales, contenido real de correos ni datos
personales; redacta los ejemplos o usa valores ficticios.

## Validación local

```text
python scripts/validate_conformance.py
python scripts/validate_examples.py
python -m pytest tests -q
```
