# Despliegue preparado: Supabase + Render existentes

No se ejecutaron migraciones remotas, creación de buckets ni despliegue. Auto-Deploy
permanece fuera de las acciones realizadas. Se requiere autorización específica
del propietario para ejecutar esta guía contra servicios remotos.

## Variables implementadas

Todas están en `.env.example`; usar variables del servicio para remoto, nunca Git.

| Variable | Uso |
|---|---|
| APP_ENV | `local`, `test`, `demo` o `production` |
| DATABASE_URL | SQLAlchemy `postgresql+psycopg://...`, usuario de ejecución; URL-encode de contraseña, TLS remoto `?sslmode=require` o verificación completa con CA |
| MIGRATION_DATABASE_URL | Usuario migrador propietario, separado; solo entorno de consola de migraciones |
| JWT_SECRET | Aleatorio, mínimo 32 caracteres; generar fuera de Git y no imprimir |
| PUBLIC_BASE_URL | Origen exacto HTTPS de Render, sin ruta ni comodines |
| PUBLIC_SIGNUP_ENABLED | `false` para demo sin correo |
| EMAIL_MODE | `disabled` en demo sin correo; `smtp` al configurar/probar proveedor |
| SMTP_HOST, SMTP_PORT | Proveedor; Mailpit solo local |
| SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_TLS | Credenciales servidor y remitente; TLS `true` remoto |
| STORAGE_BACKEND | `supabase` remoto; `local` únicamente desarrollo |
| STORAGE_PATH | `.local/storage` local; no persistencia remota mediante filesystem de Render |
| SUPABASE_URL | URL HTTPS del proyecto existente |
| SUPABASE_SERVICE_ROLE_KEY | Clave servidor de Storage, jamás en Angular; no se usa para consultas SQL |
| SUPABASE_BUCKET | Bucket privado de demo, separado del futuro de producción |
| PORT | Proporcionado por Render; servidor escucha `0.0.0.0` y usa un worker |

No guardar `MIGRATION_DATABASE_URL` privilegiada en el servicio web si no se necesita.
La configuración rechaza JWT corto, registro sin SMTP, modo remoto sin TLS/Storage,
HTTP remoto y producción sin correo. Los errores de configuración ocultan valores.

## Supabase: pasos posteriores autorizados

1. Confirmar proyecto y destino de demo. Usar Session pooler puerto 5432 acordado.
   La cadena debe corresponder a ese pooler; no improvisar usuario ni hostname.
2. Obtener por un canal privado credenciales de migración. No pegarlas en chat.
   La migración crea esquema `voluntia` y 23 tablas; Alembic añade su tabla técnica.
3. Crear un rol login `voluntia_runtime` sin superusuario, CREATEDB ni CREATEROLE.
   Asignar contraseña con `\password voluntia_runtime` desde consola segura.
   Autorizar conexión a la base correspondiente. Mantener propietario/migrador aparte.
4. Desde consola con configuración privada, tras autorización:

   ```powershell
   .\.venv\Scripts\python.exe -m scripts.migrate --allow-remote --confirm-database postgres
   ```

   `postgres` es un ejemplo frecuente; sustituir únicamente por el nombre confirmado
   del destino. El script imprime host/base sin credenciales y no hace downgrade.
   Migraciones nunca se ejecutan al iniciar FastAPI ni en el Dockerfile.
5. Aplicar `database/permissions.sql` con el propietario después de migrar. Las
   funciones son SECURITY INVOKER; el backend establece actor transaccional desde
   la sesión validada. No exponer el esquema a PostgREST. Se revocan PUBLIC,
   anon y authenticated sobre esquema/objetos cuando esos roles existen.
6. Probar conexión con el rol de ejecución, cuatro funciones y restricciones. La
   prueba local de privilegios mínimos está automatizada; privilegios del pooler
   remoto siguen pendientes de verificar. No sustituir por la cuenta propietaria
   como solución permanente si el pooler rechaza el rol: resolver su configuración.
7. Crear un bucket **privado** autorizado de demo. Separar datos reales. Límites:
   documentos/PDF 10 MB, imágenes 5 MB; prefijos documents/evidence/certificates.
   La API controla el acceso y firma descargas por 60 segundos. No crear políticas
   de lectura públicas. Configurar políticas/grants conforme al proyecto existente.
8. Probar upload, descarga autorizada, rechazo ajeno y errores de proveedor con un
   documento ficticio. Registrar evidencia de API externa real; MockTransport de
   pruebas no cuenta como dicha evidencia.

Referencias primarias: [Supabase Storage](https://supabase.github.io/storage/),
[descargas privadas](https://supabase.com/docs/guides/storage/serving/downloads),
[control de acceso](https://supabase.com/docs/guides/storage/security/access-control).

## Render: pasos posteriores autorizados

1. Usar el servicio existente conectado al repositorio privado. No crear otro ni
   cambiar visibilidad. Conservar Auto-Deploy desactivado.
2. Elegir el commit de main con CI verde; Dockerfile raíz y contexto raíz.
3. Configurar las variables anteriores, `APP_ENV=demo`, Storage real y origen HTTPS.
   Sin proveedor SMTP: `EMAIL_MODE=disabled`, `PUBLIC_SIGNUP_ENABLED=false`.
4. Aplicar migración controlada antes del despliegue, con backup y destino revisados.
   Provisionar cuentas ficticias privadamente con CLI. `scripts.seed_demo --allow-remote`
   solo se considera después de autorización expresa y base de demo vacía. No usar
   el seed en producción ni presentar cuentas preactivadas como correo verificado.
5. Ejecutar despliegue manual únicamente tras autorización. Health `/api/health`;
   readiness `/api/ready` comprueba conexión y catálogo. Un health verde por sí solo
   no demuestra DB/Storage funcionales.
6. Desde un navegador externo, recorrer visitante y tres roles, confirmar HTTPS,
   cookies Secure/HttpOnly, restricciones CSRF, documentos privados y certificado.
   Reiniciar servicio y verificar persistencia DB/Storage. Comprobar arranque en frío.

## Producción real y respaldo

La demo académica no habilita producción. Se requiere correo real probado, entornos
y cuentas separados, revisión de privacidad/consentimiento, backups/restauración,
retención, monitoreo y respuesta a incidentes. Nunca exponer Mailpit en Render.

Usar `pg_dump --format=custom --file=...` y `pg_restore --list ...` con credenciales
por variables `PG*` privadas o servicio de conexión, sin DSN en argumentos/logs.
Probar restauración en una base aislada antes de cambios remotos. El respaldo de
PostgreSQL no incluye objetos Storage: respaldar ambos y conciliar referencias.
No ejecutar `pg_restore --clean` en una base compartida. Ver SEGURIDAD_Y_OPERACION.
