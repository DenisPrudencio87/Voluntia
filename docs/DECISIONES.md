# Decisiones de diseño
Alcance y arquitectura inicial: documentos activos. Registrar aquí decisiones adicionales, motivo, impacto y alternativas.

## Revisión 2 — 24/11/2026
- Python 3.13 por instalación disponible; venv y pip asociados al intérprete, sin instalaciones globales.
- Resend suspendido y Brevo sin correo de verificación: Mailpit local + adaptador SMTP, proveedor real pendiente. Supabase Storage es integración externa principal. Demo remota con cuentas ficticias provisionadas, sin registro público ni recuperación por correo mientras falte proveedor. No se altera el modelo de 23 tablas. Producción real sigue bloqueada para registro abierto.
- Repo y servicio Render ya existentes; Auto-Deploy desactivado, no recrear. Autorización separada para migraciones remotas, Storage y despliegue. Sin secretos en Git.
- Portabilidad: scripts Windows sin Docker para ejecución con base de demo accesible; Docker local para pruebas aisladas. Guía y clon limpio obligatorios.
- Simplificación y modos de demo son decisiones de implementación, no requisitos textuales adicionales de la rúbrica. No garantizan nota.
