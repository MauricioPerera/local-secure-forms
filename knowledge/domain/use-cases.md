---
type: Domain Knowledge
id: lsfa-priority-use-cases
status: draft
---

# Casos de uso prioritarios

1. **Conectar correo:** capturar IMAP/SMTP, validar conexión y guardar una
   credencial sin devolverla.
2. **Enviar correo:** revisar destinatario, asunto y cuerpo, y exigir
   confirmación de alto riesgo.
3. **Desvincular cuenta:** retirar la referencia local y el secreto de forma
   segura, conservando los datos que no sean credenciales.
4. **Borrado reversible:** ejecutar `soft_delete` y permitir `restore`.
5. **Borrado permanente:** ejecutar `purge` solo con confirmación reforzada.
6. **Configuración manual:** permitir terminal o modo manual cuando no exista
   una interfaz gráfica.
