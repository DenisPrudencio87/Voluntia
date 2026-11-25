# Decisiones de diseño
Alcance y arquitectura inicial: documentos activos. Registrar aquí decisiones adicionales, motivo, impacto y alternativas.

## Revisión 2 — 24/11/2026
- Python 3.13 por instalación disponible; venv y pip asociados al intérprete, sin instalaciones globales.
- Resend suspendido y Brevo sin correo de verificación: Mailpit local + adaptador SMTP, proveedor real pendiente. Supabase Storage es integración externa principal. Demo remota con cuentas ficticias provisionadas, sin registro público ni recuperación por correo mientras falte proveedor. No se altera el modelo de 23 tablas. Producción real sigue bloqueada para registro abierto.
- Repo y servicio Render ya existentes; Auto-Deploy desactivado, no recrear. Autorización separada para migraciones remotas, Storage y despliegue. Sin secretos en Git.
- Portabilidad: scripts Windows sin Docker para ejecución con base de demo accesible; Docker local para pruebas aisladas. Guía y clon limpio obligatorios.
- Simplificación y modos de demo son decisiones de implementación, no requisitos textuales adicionales de la rúbrica. No garantizan nota.

## Implementación — 24/11/2026
- Esquema privado `voluntia`, SQL consumido por Alembic y SQLAlchemy Core con parámetros. Las 23 tablas conservan el diccionario aprobado; Alembic añade solo su tabla técnica.
- PostgreSQL 17.7 y Mailpit 1.27.8 en Compose local, puertos en loopback y volumen exclusivo. Python efectivo 3.13.15. npm.cmd evita modificar la política de PowerShell.
- Todos los cambios de ocupación bloquean primero actividad y después inscripción. Historial, bitácora y aviso se generan en trigger para evitar duplicaciones. Las cuatro funciones no son ejecutables por PUBLIC.
- Dependencias se resolverán desde registros oficiales y se fijarán completas tras instalación. Compatibilidad Angular/Node contrastada en https://angular.dev/reference/versions y metadatos oficiales npm; versión estable actual Angular 22.3.0 compatible con Node 24.21.0.
- `usuario.fecha_actualizacion` representa exclusivamente la versión de seguridad de sesiones; editar perfil no la cambia. Contraseña, cierre de sesión, suspensión o cambios de roles la actualizan y revocan todas las sesiones. Perfil tiene su propio timestamp. Limitador en memoria para un worker, requiere almacén compartido al escalar.
- Las rutas de escritura exigen Origin exacto y CSRF firmado incluso en login. No se configura CORS: Angular usa proxy local y mismo origen en artefacto desplegable.
