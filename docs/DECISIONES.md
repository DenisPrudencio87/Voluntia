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
- Los documentos, evidencias y certificados usan un bucket privado con prefijos separados; referencias permanentes son claves de objetos, no URLs firmadas. Las evidencias se conservan privadas en esta versión para evitar publicación accidental; imágenes de portada opcionales son URLs HTTPS sin descarga en backend. Validación PDF por firma/parser y rechazo de contenido activo, imágenes reencodificadas para eliminar metadatos.
- Integración Storage según documentación primaria: https://supabase.com/docs/guides/storage/serving/downloads y https://supabase.github.io/storage/. Mailpit real según https://mailpit.axllent.org/docs/api-v1/.
- SQLAlchemy Core y SQL versionado son la fuente ejecutable del modelo. Evitamos duplicar 23 tablas en un ORM paralelo; diccionario/ERD se obtienen del catálogo PostgreSQL. Los routers delegan reglas compartidas a servicios y usan parámetros en consultas.
- CI detectó que el cierre de una dependencia de alcance request confirmaba DB después de enviar 201; se adoptó alcance function para transacciones y dependencias de autorización. Commit antes de respuesta, sin reintentos artificiales de frontend.
- CSP permanece sin scripts inline. Deshabilitada optimización `inlineCritical` de Angular porque generaba script inline para activar la hoja CSS. Mantener Bootstrap completo facilita explicar el estilo; advertencia de tamaño inicial registrada, sin elevar el presupuesto para ocultarla.
- Invariantes adicionales en migración 0002 sin tablas nuevas; runtime de privilegios mínimos sin DDL/borrado de usuarios. Usuarios de migración y ejecución separados para remoto, pendiente comprobar pooler autorizado.
- PowerShell 5 requiere BOM en scripts con texto español; JSON del proxy requiere UTF-8 sin BOM. Los scripts generan proxy según el puerto configurado y registran procesos por PID/hora/ruta para detener solo procesos propios.
- La demo seed genera claves aleatorias privadas y datos/archivos ficticios, exige base vacía local/demo y registra que no comprobó correo real. Un escenario histórico permite sustentación de asistencia/certificado sin bypass HTTP. Fechas de eventos en UTC; PDF muestra fecha de emisión en Lima.
# Auditoría previa al despliegue — 24/11/2026

- Autorización posterior, 25/11/2026: conectar y migrar Supabase existente, configurar runtime/Storage/demo y cambiar repo original a público tras revisar secretos. Preservar claves del propietario y demo local; secretos remotos en archivos distintos. El propietario importa render.env y hace deploy manual. No repetir auditoría ni instalación aprobadas.

- Revocar el rol global de organización desactiva también sus membresías activas. Crear otra organización no restaura acceso retirado. Solo activar una membresía concede/reactiva el rol; la inactivación no lo concede.
- La autorización SQL exige roles activos de organizador y participante además de membresía y estado. Los plazos de aceptación se comparan con `clock_timestamp()` tras adquirir bloqueos, manteniendo orden actividad→inscripción.
- Migración 0003 aditiva: reemplaza funciones sin cambiar las 23 tablas. SQL publicado de 0001/0002 no se modifica; cargador compartido admite ejecución y exportación offline. La tabla técnica Alembic se fija en public y readiness exige la revisión vigente.
- Pool SQLAlchemy limitado a cinco conexiones sin overflow; search_path mediante SET al conectar, sin parámetro startup `options`, para Session pooler. TLS obligatorio en conexiones remotas, migrador incluido. Puerto compartido Supabase permitido: Session 5432.
- Supabase conserva el nombre de configuración `SUPABASE_SERVICE_ROLE_KEY` por compatibilidad; admite nueva clave secreta sb_secret_* solo en apikey, o JWT legacy en Bearer/apikey. Nunca clave privilegiada en Angular.
- Inspección PDF sobre objetos decodificados, validación MIME/firma de imágenes y límite ASGI de bytes efectivos. Fallos de disco producen 503 controlado. URLs firmadas ligadas al bucket/key esperado y descarga por adjunto.
- Estado de sesión independiente del cliente HTTP para evitar ciclos de inyección; un 401 expulsa de pantallas protegidas. Logout limpia sesión caducada y cambio de contraseña lleva a acceso. Feedback cuenta operaciones concurrentes y conserva confirmaciones.
- Login limita diez intentos por cuenta y cincuenta por IP en cinco minutos, para permitir varios evaluadores detrás de una IP sin quitar protección por cuenta. Reenvío/recuperación mantienen sus límites más estrictos.
- Las pruebas remotas y la sustentación no se presumen. El informe final diferencia evidencia local, contrato de API y evidencia que requiere autorización/demostración del estudiante.
