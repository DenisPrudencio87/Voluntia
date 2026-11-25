# Seguridad y operación

## Fronteras de confianza

El navegador no decide roles, organización autorizada, actor de SQL ni horas.
El backend verifica JWT, estado de cuenta, correo, roles activos y membresía en
cada operación. Los administradores generales revisan documentación pendiente;
no disponen de un explorador indiscriminado de archivos privados. Los certificados
se descargan solo por su titular, aunque su código permite verificar datos mínimos.

Las contraseñas usan Argon2id. JWT de 30 minutos en cookie HttpOnly, SameSite=Lax,
Secure remoto. No se guarda JWT en localStorage. Las escrituras requieren Origin
exacto y CSRF firmado en cookie/cabecera, incluso login. Cambiar contraseña,
cerrar sesión y cambios administrativos de seguridad revocan sesiones mediante
`usuario.fecha_actualizacion`. El perfil tiene timestamp independiente.

El limitador es por IP/cuenta, con claves hash y un worker. No se confía en cabeceras
X-Forwarded-For arbitrarias. En Render se debe comprobar la configuración real del
proxy; antes de escalar a varios workers se necesita un almacén compartido para
límites. Las restricciones no se desactivan en demo. Si se repiten pruebas sobre
una instancia, un 429 acumulado es esperado; usar fixtures aisladas.

## Transacciones y permisos

SQLAlchemy Core parametriza todos los valores. Los únicos identificadores variables
de catálogos proceden de una lista cerrada. SQL está versionado con Alembic; no se
duplica el diccionario mediante un ORM paralelo. El esquema `voluntia` tiene 23 tablas.

Toda ocupación/cancelación/edición de cupo del backend bloquea primero ACTIVIDAD
y luego INSCRIPCION. La aceptación llama a `fn_aceptar_inscripcion`. El trigger genera
historial, bitácora y notificación en la misma transacción; un fallo intermedio
revierte todo. `Depends(..., scope="function")` asegura commit antes de enviar HTTP;
la carrera detectada en CI y su corrección están documentadas en PROGRESO.

La segunda migración refuerza invariantes ante escrituras SQL accidentales: plazas,
fechas, titular de inscripción, asistencia y coherencia/inmutabilidad de certificados.
La auditoría/historial son append-only. El rol runtime no puede crear tablas ni borrar
usuarios; grants preparados en `database/permissions.sql` y probados con un rol
NOLOGIN equivalente en PostgreSQL local. Crear/login y conexión remotos requieren
configuración y comprobación autorizadas. El propietario local de Compose es solo
para desarrollo aislado, no una credencial válida para la aplicación remota.

## Archivos

PDF se valida con firma/parser, límite 10 MB, sin cifrado ni contenido activo; imagen
JPEG/PNG/WebP hasta 5 MB se verifica y reencodifica. Nombre aleatorio y prefijo interno,
sin rutas elegidas por el cliente. PDFs/certificados se descargan como adjuntos.
Portadas/logos opcionales usan HTTPS y no se descargan desde backend.

Documentos, evidencias y certificados son privados. En Supabase se guardan claves
permanentes y se generan URLs firmadas por 60 s tras autorización. Una URL firmada
puede funcionar hasta expirar después de revocar al usuario: limitar su vida es parte
del diseño. Storage real continúa pendiente; sus pruebas con transporte simulado
se limitan al contrato y fallo controlado, nunca se presentan como operación remota.

Storage y SQL no comparten transacción distribuida. Un fallo DB después de un upload
puede dejar un objeto sin referencia; no se entrega URL al cliente sin registro.
Conciliar esos objetos con backup antes de cualquier limpieza autorizada. No existe
una ruta pública de archivos locales. Compose comparte `.local/storage` con el host
para conservar referencias al alternar ejecución Windows/Docker; esa carpeta queda
fuera del build y de Git. En otro SO, comprobar permisos de escritura del usuario
del contenedor sobre ese directorio de desarrollo.

## Correo y modo cerrado

SMTP tiene timeout y fallo 503 controlado. La operación revierte si no se pudo enviar;
el reintento no finge éxito. Tokens aleatorios de un uso, solo hash en DB, 30 minutos,
rotación en reenvío y revocación al cambiar contraseña. Respuestas de recuperación no
revelan si existe una cuenta. Mailpit únicamente localhost, sin envío a terceros.

Sin proveedor real, demo remota tiene registro/recuperación cerrados en API e interfaz.
Las cuentas ficticias preactivadas no son evidencia de verificación de correo real.
El CLI usa getpass y nunca imprime contraseñas. El seed exige base vacía local/demo.
Producción se niega a arrancar sin configuración de correo/HTTPS/Storage válida.

## Respaldo y recuperación local

No se borra ningún volumen ni se resetea una base compartida. Para detener: stop de
scripts o `docker compose --profile app stop`. Un backup de DB no contiene archivos.
Respaldar también `.local/storage` o los objetos del bucket autorizado.

Con PostgreSQL local de Compose:

```powershell
New-Item -ItemType Directory -Force .local/backup
docker compose exec -T db pg_dump -U voluntia -d voluntia -Fc -f /tmp/voluntia.backup
docker cp voluntia-local-db-1:/tmp/voluntia.backup .local/backup/voluntia.backup
docker compose exec -T db createdb -U voluntia voluntia_restore_test
docker compose exec -T db pg_restore -U voluntia -d voluntia_restore_test --no-owner --no-acl --exit-on-error /tmp/voluntia.backup
```

Crear un nombre dedicado nuevo si ya existe. Verificar conteo 23 tablas y registros
en la restauración, sin sustituir la base original. En remoto, usar herramientas y
credenciales autorizadas y nunca poner una contraseña en argumentos de shell.

## Límites de la evidencia

Las auditorías de paquetes son consultas puntuales, no una auditoría de seguridad
completa. Quedan por verificar Storage/pooler/SMTP/HTTPS reales, políticas remotas,
respaldo remoto y recuperación operacional. La advertencia de tamaño inicial Angular
permanece visible. El proyecto busca una demo académica explicable; no se declara
listo para usuarios reales sin esas verificaciones.
