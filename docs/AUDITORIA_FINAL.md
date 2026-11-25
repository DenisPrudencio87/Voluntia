# Auditoría técnica y académica previa al despliegue

Fecha: 24/11/2026, America/Lima. Revisión independiente desde main `fbdd430`, rama
`feature/auditoria-final`. La rúbrica original de [RUBRICA.pdf](RUBRICA.pdf) prevalece.
Se contrastaron AGENTS, PROMPT_MAESTRO y documentos activos; `referencia/` no se
utilizó como especificación. Este informe distingue implementación, comprobación
local y evidencias remotas todavía pendientes.

**Dictamen:** se encontraron defectos reales pese a la CI anterior verde. Se
corrigieron localmente los problemas reproducibles descritos abajo. No se ha
autorizado ni realizado migración/grants remotos, creación de buckets, despliegue
Render ni activación de Auto-Deploy. No se acredita todavía una URL pública
funcional ni una integración real con el proyecto Supabase del propietario.

## Hallazgos y correcciones

La primera ejecución de las nuevas regresiones sobre el código previo produjo
**10 fallos backend y 2 Angular**. No se desactivaron pruebas para corregirlos.

| ID / gravedad previa | Hallazgo comprobado | Corrección y evidencia versionada |
|---|---|---|
| A01 alta | Retirar el rol organización dejaba membresías activas; crear otra organización recuperaba acceso a registros anteriores | `admin.user_roles` retira membresías; `test_new_organization_does_not_restore_revoked_old_membership` |
| A02 alta | Inactivar una membresía concedía de nuevo el rol global retirado | `organizations.save_member` solo concede con estado activo; regresión `test_deactivating_member_does_not_regrant_global_role` |
| A03 alta | Función/trigger de aceptación comprobaban membresía, sin exigir rol global vigente | Migración 0003 exige roles activos de organización y voluntario; dos regresiones SQL |
| A04 alta | `now()` conservaba la hora de inicio de transacción; podía aceptarse tras el inicio real | Comparación con `clock_timestamp()` después de bloquear; regresión abre transacción, espera y comprueba rechazo |
| A05 media | Motivo de rechazo documental no llegaba a la organización | Consulta incorpora `revision_documento`; `test_document_rejection_reason_reaches_owner` |
| A06 media | Logout de sesión vencida devolvía 401 y no limpiaba cookies | Limpieza idempotente con CSRF/origen todavía exigidos; regresión y navegador |
| A07 media | Un CSRF Unicode causaba TypeError/500 | Formato exacto ASCII antes de comparación constante; `test_non_ascii_csrf_fails_closed` |
| A08 alta | PDF con nombres activos escapados `#xx` eludía búsqueda textual | Recorrido de objetos PDF decodificados, referencias visitadas y límite; PDF válido con acción escapada rechazado |
| A09 media | GIF presentado como JPEG se aceptaba | MIME debe coincidir con firma JPEG/PNG/WEBP; recodificación sin metadatos y límite de salida |
| A10 media | Disco no disponible producía excepción sin respuesta controlada | Lectura/escritura local devuelve 503; contención de ruta resuelta; regresión de fallo de disco |
| A11 media | Mensajes de registro/verificación/reset se borraban al terminar Feedback | Conservación de confirmaciones; regresión Angular y flujo real Mailpit por navegador |
| A12 media | Una petición terminada quitaba busy aunque quedara otra en curso | Contador de pendientes; regresión de concurrencia Angular |
| A13 media | Cambiar contraseña o recibir 401 dejaba interfaz protegida obsoleta | SessionState independiente, invalidación/redirect y regreso a acceso tras cambiar clave; navegador |
| A14 media | Cambios rápidos de organización podían mezclar respuestas/cargos | Selección con generación, carga atómica y cargo obtenido del servidor; no se deriva autorización del listado antiguo |
| A15 media | Actividad ajena/inexistente mostraba formulario de creación tras fallar GET | Formulario nuevo solo en ruta de creación; cambios de parámetros limpian datos previos; navegador 404 sin botón Crear borrador |
| A16 media | Content-Length no protegía solicitudes chunked; un valor enorme podía fallar al convertirse | Middleware ASGI limita bytes efectivos a 11 MiB antes del parser; validación acotada de cabecera y prueba chunked |
| A17 media | Readiness aceptaba un esquema atrasado si existían tres roles | Exige head Alembic y 23 tablas; diagnóstico Windows también; permiso runtime para leer tabla técnica |
| A18 media | URL migradora remota podía omitir TLS en modo local | Validación de ambas URL, driver y Session pooler 5432; regresiones sin conexión remota |
| A19 media | Startup `options` hacía depender search_path del protocolo del pooler | SET al abrir conexión en autocommit, conservado tras rollback; pool máximo 5 sin overflow; regresión |
| A20 media | Exportar Alembic offline intentaba usar cursor real | Cargador SQL común online/offline; SQL exportado ejecutado íntegramente en otra base local vacía |
| A21 media | Clave Supabase actual `sb_secret_*` se enviaría como Bearer inválido | Solo apikey para nueva clave; compatibilidad JWT legacy; prueba de ambas cabeceras y documentación oficial |
| A22 media | Asistencia positiva muy corta podía subir PDF y luego fallar al redondear horas a cero | Redondeo decimal consistente con PostgreSQL y rechazo 409 antes de subir; regresión de dos segundos |
| A23 baja | Setup admitía Node 24 anterior al mínimo de Angular instalado | Comprobación 24.15 o posterior dentro de serie 24; sin instalar Node global |
| A24 baja | Detalles se cerraban al refrescar y selector conservaba archivo ya enviado | Se conserva la misma organización al refrescar y se limpia input tras subida; recorridos de miembros/documentos/evidencia |
| A25 media | Repr de Settings podía incluir secretos | Campos privados excluidos de repr y valores ocultos en errores; regresión |
| A26 media | Historial recibido por HTTP 200 no aparecía al abrirlo en Angular sin zonas | Selección convertida en signal; prueba de navegador exige sus tres eventos |
| A27 baja | Confirmación de logout se perdía al cargar el inicio | Regreso a acceso y cierre de menú; prueba de navegador exige confirmación persistente |

Además: se controla el error de recarga documental administrativa y se descartan
selecciones antiguas; no se bloquea erróneamente al modificar un administrador ya
inactivo; banner de modo demo declara datos ficticios. Login mantiene 10 intentos
por cuenta y 50 por IP/5 minutos para una universidad con NAT compartida.

## Cobertura de los veinte puntos solicitados

| Punto | Revisión y resultado |
|---|---|
| 1. Cinco criterios | Descriptores originales leídos; puntuación conservadora más abajo. No se presume sustentación ni despliegue |
| 2. Pantallas/acciones | Inventario siguiente, revisión de plantillas y handlers, tests HTTP y recorridos reales. No se afirma cubrir todas las combinaciones posibles |
| 3. Responsive | Chromium 1280×800 y 360×800; aserciones de ancho y capturas inspeccionadas. Tablas tienen scroll interno, menú móvil y formularios apilados |
| 4. Modularización | Angular standalone con rutas lazy, componentes RecordForm/SkillsEditor, servicios/guardas/modelos; FastAPI routers/schemas/services/security, transacciones y adaptadores separados |
| 5. Validaciones | Angular required/email/longitudes/enteros/fechas/coincidencia; Pydantic extra forbid, normalización, enums/rangos/HTTPS; PostgreSQL restricciones/trigger. Backend no confía en validación del navegador |
| 6–7. Auth/permisos | Argon2, JWT HttpOnly 30 minutos, versión de sesión, CSRF firmado y origen exacto; verificación/tokens hash de uso único; roles consultados en cada petición, pertenencia por organización, archivos privados autorizados |
| 8. 3FN | Revisión de dependencias funcionales de las 23 relaciones, descrita abajo. No se considera prueba de normalización contar tablas |
| 9. Claves/índices | 23 PK, 29 FK, unicidad de correo/inscripción/certificado y pares N:M; CHECK de estado/horario/cupos/coordenadas, índices FK y de catálogo/notificaciones |
| 10. SQL/transacciones | Cuatro funciones de negocio, triggers de ocupación/historial/notificación/asistencia/impacto/certificado; último cupo concurrente, duplicado concurrente y rollback inyectado |
| 11. Migraciones | 0001→0002→0003, upgrade incremental y no-op en head; exportación offline ejecutada. SQL histórico intacto; ninguna migración en startup/Docker build |
| 12. Errores/vacíos | Estados vacíos catálogo/panel/listas, 404/409/422/503, mensajes de formulario y proveedor; se corrigieron silencios y UI obsoleta. No se devuelven trazas al cliente |
| 13. Datos ficticios | Seeds explícitos solo local/demo o *_test; claves aleatorias privadas. Producción sin mocks; MockTransport vive únicamente en tests. Preactivación demo no representa correo verificado real |
| 14. Secretos | .env/.local/.runtime/venv ignorados, contención de archivos, escaneo de versionados y revisión del diff; sin credenciales reales documentadas. Clave Storage solo servidor |
| 15. Git/CI | Repo privado original, ramas por hitos, PR #1–#5 integrados con CI; auditoría también se entrega por PR y checks verificables |
| 16. Render/Docker | Build multietapa, proceso sin root, SPA/API mismo origen, 0.0.0.0:$PORT, un worker; build y arranque local con PORT=10000 comprobados |
| 17. Session pooler | psycopg3, TLS, Session 5432, SET search_path y pool acotado. Compatibilidad preparada según documentación; conexión real remota no ejecutada |
| 18. Windows/clon | Setup/check/start/stop sin rutas personales versionadas ni herramientas globales. Evidencia del clon de auditoría se registra al cerrar validación |
| 19. Demo sin correo | EMAIL_MODE=disabled y PUBLIC_SIGNUP_ENABLED=false, cierre en UI y servidor, cuentas ficticias provisionadas privadamente; producción exige SMTP |
| 20. Sustentación | Guías, ERD/diccionario y recorrido trazable; se requiere explicación personal del alumno, imposible inferirla del código |

### Inventario de interfaz

| Pantalla | Acciones implementadas y verificadas por código/test |
|---|---|
| Inicio y navegación | Estadísticas SQL, categorías, enlaces de oportunidades, menú móvil, acceso/panel/salir; vacíos reales |
| Catálogo/detalle | Filtros, limpiar, paginar, cupos SQL, organización pública, postular, validación y cerrado por plazo/estado |
| Cuenta | Registro, reenvío, verificación, login, olvido, recuperación, cambio de contraseña y logout; correo local real capturado en Mailpit |
| Voluntario | Perfil/ubicación/habilidades, postulaciones, cancelar, historial, horas, certificado y notificaciones leídas |
| Organización | Crear/editar, estadísticas, miembros por cargo, documentos privados/revisión/motivo, listar/paginar actividades |
| Gestión actividad | Crear/editar borrador, publicar/cerrar/iniciar/finalizar/cancelar, cupos, aceptar/rechazar/espera, asistencia, impacto, evidencia privada, certificado |
| Administración | Revisar/descargar documento pendiente, aprobar/rechazar/suspender organización, usuarios/roles/suspensión, último administrador, catálogos, cancelación y bitácora |
| Certificado público | Código válido/inexistente, datos mínimos y aviso de visibilidad; PDF privado del titular |

Playwright ejecuta los recorridos principales y regresiones de UI. Las alternativas
de espera/rechazo/cancelación, separación de datos, estados y permisos se cubren
también por HTTP/SQL. Revisión estática no equivale a pulsar manualmente cada
combinación de botón, estado, rol y condición de red. No hay enlaces simulados ni
handlers vacíos encontrados. Safari/iOS y teléfono físico no se han probado.

## Base de datos: revisión de 3FN e integridad

| Relaciones | Claves y dependencias revisadas |
|---|---|
| usuario, rol | Identificadores y correo/nombre alternativos; credenciales/estado pertenecen al usuario, descripción al rol |
| usuario_rol | PK(usuario,rol); activo/fecha dependen del par completo |
| token_cuenta | Token hash único determina titular, tipo y vigencia; no guarda texto del token ni duplica usuario |
| ubicacion | Identidad propia para lugar/dirección/coordenadas; referencias desde perfiles, organizaciones y actividades |
| voluntario | ID y usuario único; datos del perfil dependen de su titular, sin correo/contraseña duplicados |
| organizacion | Identidad y datos propios; miembros y documentos separados |
| organizacion_miembro | PK(organización,usuario); cargo/estado/fecha corresponden a esa pertenencia |
| documento_organizacion | ID determina organización, referencia, objeto privado y revisión; responsable/motivo auditados en bitácora |
| categoria, habilidad | Nombre único y atributos del catálogo, sin listas en columnas |
| voluntario_habilidad | PK(voluntario,habilidad); nivel/verificada corresponden a la relación completa |
| actividad | ID determina organización/categoría/ubicación y datos de la oportunidad; sin nombres de esas entidades duplicados |
| actividad_habilidad | PK(actividad,habilidad); nivel requerido/obligatoria por par |
| estado_inscripcion | ID y nombre únicos, reutilizados por inscripción e historial |
| inscripcion | ID y par(actividad,voluntario) únicos; estado y motivación de esa postulación |
| historial_inscripcion | Evento con identidad, estado, inscripción, actor y fecha; append-only |
| asistencia | ID e inscripción únicos; intervalo/estado de esa participación |
| impacto_actividad | ID y actividad únicos; beneficiarios/resultado de la actividad |
| evidencia_actividad | Cada evidencia determina actividad, autor, tipo y objeto; no modifica el número de asistencias |
| certificado | ID, inscripción y código únicos; emisión y horas de ese certificado inmutable |
| notificacion | Cada aviso determina destinatario, texto, enlace interno y lectura |
| bitacora_evento | Evento determina actor/entidad/acción/registro/fecha/detalle; no sustituye las tablas de dominio |

Son 23 tablas de producto; `public.alembic_version` es metadato técnico. No se
encontraron dependencias parciales de claves compuestas ni atributos descriptivos
de otra entidad copiados en las tablas principales. Los valores son atómicos y
las relaciones N:M están descompuestas. El total de horas de impacto es una
agregación materializada mantenida por trigger; horas certificadas son una
instantánea de emisión validada por trigger e inmutable. Deben explicarse como
redundancias calculadas controladas, no como datos editables arbitrariamente.

Las FK impiden huérfanos; no se elimina el historial con cascadas de producto.
Existen algunos índices FK redundantes con el prefijo de PK/UNIQUE: coste menor
de escritura, sin pérdida de integridad; no se emprendió optimización sin carga
representativa. La bitácora usa referencia genérica entidad/id_registro, no FK
polimórfica: se justifica por eventos de distintas entidades, y no autoriza acceso.

El runtime no es propietario: SELECT/INSERT/UPDATE de tablas necesarias, sin DDL,
sin DELETE general ni UPDATE de historial/bitácora/certificado. SQL es SECURITY
INVOKER, parámetros ligados y catálogos dinámicos en lista cerrada. La API pone
`app.actor_id` transaccional tras validar sesión. El usuario SQL de servidor puede
establecer ese contexto; no sustituye autenticación ni RLS por usuario final y
nunca debe entregarse a Angular o a evaluadores no confiables. Esquema privado
no expuesto a PostgREST; revocación de PUBLIC/anon/authenticated en migración.

## Pruebas y evidencias

| Comprobación | Resultado observado en esta auditoría |
|---|---|
| Pytest completo, PostgreSQL 17 aislado | **52 passed**, 26.64 s; incluye 24 regresiones nuevas |
| Angular unitario | **8 passed**, 4 archivos; 3 pruebas nuevas |
| Angular build | Éxito; initial 615.64 kB, aviso frente al presupuesto 500 kB; no se elevó presupuesto para ocultarlo |
| Playwright, escritorio y móvil | **8 passed**, 57.2 s; incluye archivos privados, historial, notificaciones y logout |
| Migración incremental | 0002→0003 correcta, catálogo conservado; repetir head no modifica revisión |
| Exportación Alembic --sql | SQL ejecutado en `voluntia_audit_offline_test`: 23 tablas, 3 roles, head 0003 |
| SQL original histórico | `git diff main -- database/schema.sql database/functions.sql database/invariants.sql`: vacío |
| Catálogo físico consultado | 23 PK, 29 FK, 12 UNIQUE, 66 índices y 9 triggers de aplicación; cuatro funciones fn_* |
| Privilegios | SET LOCAL ROLE runtime: aceptación funciona, DDL/DELETE usuario/UPDATE historial rechazados |
| Docker | Imagen voluntia-audit; PORT=10000, ready y ruta SPA 200; uid/gid 999; pruebas locales |
| Dependencias | pip check correcto; pip-audit producción y npm audit --omit=dev: sin vulnerabilidades conocidas reportadas |
| Revisión Python | ruff check --select F backend scripts aprobado. Ruff exploratorio con reglas adicionales encontró estilo pendiente; no es el control acordado ni se declara aprobado |
| Secretos | scripts.check_secrets y diff revisados; archivos privados ignorados. Ningún escáner garantiza ausencia absoluta de secretos |

Comandos reproducibles (cada test requiere base local exclusiva terminada `_test`):

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://voluntia:voluntia_local@127.0.0.1:55432/voluntia_audit_test'
.\.venv\Scripts\python.exe -m pytest backend/tests -q
.\.venv\Scripts\python.exe -m ruff check --select F backend scripts
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip_audit -r backend/requirements.txt
.\.venv\Scripts\python.exe -m scripts.check_secrets
Set-Location frontend
npm.cmd ci
npm.cmd test -- --watch=false
npm.cmd run build
npm.cmd audit --omit=dev
# Con servidor de prueba, seed E2E, Mailpit y TEST_DATABASE_URL de ese servidor:
npx.cmd playwright test
```

Evidencias de ejecución permanecen en `.local/audit-evidence`, capturas
`.local/audit-*.png`, Playwright report/test-results locales y registros de CI.
No publicar credenciales, inbox ni enlaces con tokens. Los reportes CI solo
contienen datos ficticios del runner. Un primer intento Docker con hostname
host.docker.internal sin TLS fue rechazado por Settings: la invocación correcta
usa red Docker del proyecto y host `db`. Un reintento E2E sobre servidor reutilizado
alcanzó el límite correcto de reenvío; se reinició antes de validar la suite entera.
El cierre de detalles detectado por E2E se corrigió en la aplicación.

PR previos verificables: [#1](https://github.com/DenisPrudencio87/Voluntia/pull/1),
[#2](https://github.com/DenisPrudencio87/Voluntia/pull/2),
[#3](https://github.com/DenisPrudencio87/Voluntia/pull/3),
[#4](https://github.com/DenisPrudencio87/Voluntia/pull/4),
[#5](https://github.com/DenisPrudencio87/Voluntia/pull/5).
Main previo: [CI 45544534877](https://github.com/DenisPrudencio87/Voluntia/actions/runs/45544534877)
con backend/frontend/integration aprobados. Esto acredita el estado anterior,
no reemplaza la CI específica del cambio auditado.

## Evaluación preliminar estricta sobre 20

Se usan exclusivamente los niveles **4, 3, 2 o 0** del profesor. La reserva por
evidencia faltante no afirma que el código haya fallado en un servicio remoto.

| Criterio /4 | Acreditación conservadora actual | Razón |
|---|---:|---|
| Frontend | 4 | Funcional, Bootstrap, responsive, modular y validado; recorridos en ambas resoluciones y correcciones comprobadas |
| Backend | 2 provisional | Rutas/lógica/seguridad funcionales; la demostración de la integración externa exigida sigue incompleta. Sin consumo real comprobado de Storage no se acredita Bueno/Excelente todavía |
| Base de datos | 4 | 23 relaciones coherentes, análisis 3FN, funciones/triggers y comprobación transaccional real |
| Integración/despliegue/versiones | 0 provisional | Integración local y Git/PR/CI sí; falta despliegue accesible mediante URL, exigido para los niveles superiores |
| Sustentación | 0 reservado, no evaluado | No se ha observado exposición ni respuestas del estudiante; una guía no acredita dominio personal |
| **Total documental conservador** | **10/20** | No es calificación oficial ni pronóstico de la sustentación |

No se propone 20/20 antes de demostrar Storage/URL y dominio técnico. Con esos
tres elementos comprobados y sin nuevos defectos, existe una base para aspirar
al nivel Excelente; no se garantiza. La nota inicial de la rúbrica dice que no
sustentar implica cero global, y que no poder explicar partes sustanciales puede
afectar otros criterios. No se aplica esa penalización por el simple hecho de que
esta auditoría ocurra antes de la exposición.

## Variables exactas y ubicación de configuración

Nunca copiar valores reales a este documento, Git, Angular, screenshots o chat.
Local: `.env` ignorado, generado desde `.env.example`; consola migradora: entorno
privado temporal; remoto: **servicio Render existente → Environment**.

| Nombre exacto | Finalidad / valor no secreto orientativo | Dónde |
|---|---|---|
| APP_ENV | `demo` para demostración; `production` solo al habilitar usuarios reales | Render; local usa local/test |
| DATABASE_URL | `postgresql+psycopg://USUARIO_RUNTIME:CLAVE_CODIFICADA@HOST_SESSION:5432/postgres?sslmode=require` | Render y .env privado local cuando corresponda |
| MIGRATION_DATABASE_URL | Igual formato, propietario/migrador distinto; nunca cuenta web | Solo consola privada de migración, omitir en Render |
| JWT_SECRET | Aleatorio único, mínimo 32 caracteres; no es JWT de Supabase | Render; secreto distinto por entorno |
| PUBLIC_BASE_URL | Origen exacto HTTPS del servicio, sin ruta/query/credenciales; sin localhost remoto | Render |
| PUBLIC_SIGNUP_ENABLED | `false` mientras no exista correo real | Render demo |
| EMAIL_MODE | `disabled` demo cerrada; `smtp` tras pruebas del proveedor | Render |
| STORAGE_BACKEND | `supabase` remoto; `local` desarrollo | Render |
| SUPABASE_URL | Origen HTTPS del proyecto, sin /storage/v1 ni otras rutas | Render; copiar desde proyecto existente |
| SUPABASE_SERVICE_ROLE_KEY | Clave secreta sb_secret_* recomendada o service_role JWT legacy; nombre conservado por compatibilidad; privilegios servidor | Render exclusivamente backend; no es contraseña PostgreSQL |
| SUPABASE_BUCKET | ID exacto bucket privado separado, p.ej. `voluntia-demo-private` | Render; debe coincidir con Storage |
| STORAGE_PATH | `.local/storage`, solo adaptador local | .env local; no confiar en disco efímero Render |
| SMTP_HOST | Host proveedor real; Mailpit 127.0.0.1 únicamente local | Render solo cuando EMAIL_MODE=smtp |
| SMTP_PORT | Puerto del proveedor STARTTLS, habitualmente 587; 1025 Mailpit local | Igual |
| SMTP_USER | Usuario proveedor | Igual, privado |
| SMTP_PASSWORD | Contraseña proveedor | Igual, secreto |
| SMTP_FROM | Remitente autorizado por proveedor | Igual |
| SMTP_TLS | `true` remoto: adaptador implementa STARTTLS; no SMTP implícito 465 | Igual |
| PORT | Lo entrega Render; servidor usa 0.0.0.0 y un worker; probado con 10000 | Render; no hace falta fijarlo manualmente |

Variables de test, excluidas del servicio web: TEST_DATABASE_URL, E2E_BASE_URL,
E2E_PYTHON y opcional PLAYWRIGHT_BROWSERS_PATH. No usar una base compartida para
pytest: fixture hace TRUNCATE solamente del destino local `_test` protegido.

La contraseña de URL debe codificarse en porcentaje (incluidos @, :, /, #, %);
copiar host y usuario desde **Connect → Session pooler**. Para roles personalizados
el usuario del pooler incorpora `voluntia_runtime.PROJECT_REF`; no usar un hostname
supuesto a partir de región. El pool de cinco conexiones debe caber en los límites
reales del proyecto. TLS require cifra, pero verify-full con CA y hostname añade
verificación de identidad; comprobar la CA siguiendo el panel del proyecto.
[Conexión oficial](https://supabase.com/docs/guides/database/connecting-to-postgres),
[usuarios del pooler](https://supabase.com/kb/troubleshooting/tenant-or-user-not-found),
[roles](https://supabase.com/docs/guides/database/postgres/roles).

## Procedimiento de Supabase Storage, pendiente de autorización

1. Obtener autorización específica para **el proyecto existente y entorno demo**.
   Confirmar separación de datos/usuarios/objetos respecto de producción. No crear
   otro proyecto ni pagar por ampliar cuotas.
2. En Dashboard del proyecto → **Storage → New bucket**, indicar el ID elegido
   `voluntia-demo-private`, desactivar **Public bucket** y crear solo tras autorización.
   Si ya existe, comprobar su configuración sin recrearlo ni borrar objetos.
3. En restricciones del bucket configurar máximo **10 MiB = 10485760 bytes** y MIME
   `application/pdf`, `image/jpeg`, `image/png`, `image/webp`. El límite global de
   Storage debe permitir al menos ese tamaño. La aplicación limita imágenes a
   5 MiB y documentos/PDF a 10 MiB; un bucket común usa el máximo mayor.
4. No crear políticas públicas SELECT/INSERT/UPDATE/DELETE para anon/authenticated.
   No publicar el bucket. El backend usa su clave secreta; esta evita RLS y por eso
   la autorización de cada archivo se ejecuta antes en FastAPI. Revisar políticas
   existentes con el propietario; no borrarlas indiscriminadamente.
5. En **Project Settings → API Keys** tomar privadamente una clave secreta servidor
   `sb_secret_*`; guardarla como SUPABASE_SERVICE_ROLE_KEY. También se admite el
   JWT legacy service_role mientras esté disponible. No usar anon, publishable,
   JWT_SECRET de Voluntia ni contraseña DB. No exponer nunca una clave privilegiada
   al navegador. Las nuevas secret keys se envían en apikey, no como Bearer.
6. Copiar Project URL al SUPABASE_URL y el ID del bucket a SUPABASE_BUCKET; activar
   STORAGE_BACKEND=supabase. No se crean carpetas manualmente: las claves son
   `documents/ID/aleatorio.pdf`, `evidence/ID/aleatorio.ext`,
   `certificates/ID/aleatorio.pdf`. DB guarda esas claves, no URLs firmadas.
7. Tras autorización, subir un PDF ficticio desde la organización. Confirmar
   objeto en bucket, registro DB y descarga autorizada. Visita sin sesión debe
   fallar 401; otra organización/otro titular debe fallar 403/404. Revisar documento
   como administrador solamente durante revisión pendiente. Probar evidencia y PDF
   certificado propio. No subir DNI, datos personales ni documentos reales.
8. Confirmar que GET de objeto privado sin firma/clave no permite leerlo. La API
   solicita firma por 60 segundos, valida ruta bucket/key y redirige 303 para
   descarga. No compartir ni registrar URL firmada; probar que deja de funcionar
   tras expirar y que una nueva descarga autorizada obtiene otra firma.
9. Probar fallo de proveedor con configuración temporal controlada, observar 503
   sin secretos y restaurar configuración. Registrar evidencia real con fecha,
   commit y resultados, sin claves/tokens. Contratos MockTransport no sustituyen
   estos pasos. Respaldar objetos y DB coordinadamente.

Fuentes: [bucket privado](https://supabase.com/docs/guides/storage/buckets/fundamentals),
[restricciones](https://supabase.com/docs/guides/storage/buckets/creating-buckets),
[acceso](https://supabase.com/docs/guides/storage/security/access-control),
[claves actuales](https://supabase.com/docs/guides/getting-started/api-keys).

## Migración segura a Supabase, no ejecutada

1. Autorizar destino exacto y revisión Git con CI verde. Comprobar Session 5432,
   nombre de base, versión servidor y esquema voluntia/alembic existentes. Si el
   destino contiene datos o una revisión desconocida, detener la migración y
   evaluar un upgrade; no borrar esquema, hacer stamp ni resetear la base.
2. Crear backup lógico con pg_dump custom del esquema de aplicación y metadato
   Alembic, más objetos Storage. Registrar inventario y probar restore en una base
   aislada. No restaurar completo ni usar --clean contra una base compartida.
   El dump no contiene los archivos Storage. [Operación](SEGURIDAD_Y_OPERACION.md).
3. Usar propietario/migrador de Supabase solamente desde consola privada. Puede
   ser el propietario existente postgres; no instalarlo como usuario de ejecución.
   Mediante psql con host/usuario copiados de Session y contraseña solicitada por
   `--password`, comprobar `current_database(), current_user, version()`; revisar
   conexión TLS. Evitar DSN con contraseña en argumentos, historial y logs.
4. Crear una sola vez el rol de aplicación, si no existe, con propietario:

   ```sql
   CREATE ROLE voluntia_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
     NOREPLICATION NOBYPASSRLS;
   -- En psql, pedir la contraseña privadamente:
   \password voluntia_runtime
   GRANT CONNECT ON DATABASE postgres TO voluntia_runtime;
   ```

   Confirmar que postgres es el nombre real antes del GRANT. Si el rol ya existe,
   revisar atributos y permisos; no recrearlo ni rotar claves sin autorización.
5. Preparar `.local/supabase-migration.env` privado/ignorado con APP_ENV=local,
   JWT_SECRET propio, DATABASE_URL runtime y MIGRATION_DATABASE_URL migrador,
   ambas con TLS. EMAIL_MODE=disabled y PUBLIC_SIGNUP_ENABLED=false permiten
   migrar sin credenciales SMTP/Storage. No copiar el archivo al repositorio.
6. Exportar el SQL para revisión en una consola situada en raíz:

   ```powershell
   .\.venv\Scripts\python.exe -c "from dotenv import load_dotenv; load_dotenv('.local/supabase-migration.env',override=True); from alembic import command; from alembic.config import Config; c=Config('backend/alembic.ini'); c.output_buffer=open('.local/migracion-revisar.sql','w',encoding='utf-8'); command.upgrade(c,'head',sql=True)"
   ```

   Esto solo exporta. Para destino en 0002, revisar exportación de rango
   `0002:head`; el SQL base→head no se ejecuta sobre una base ya migrada.
7. **Solo después de autorización específica**, ejecutar upgrade controlado:

   ```powershell
   .\.venv\Scripts\python.exe -c "from dotenv import load_dotenv; load_dotenv('.local/supabase-migration.env',override=True); import runpy; runpy.run_module('scripts.migrate',run_name='__main__')" --allow-remote --confirm-database postgres
   ```

   Sustituir postgres por nombre confirmado, conservar --allow-remote explícito.
   Alembic aplica transacción y versiones; no se ejecuta al arrancar la web.
   No ejecutar pytest/fixtures ni e2e_clock contra Supabase.
8. En la sesión psql del propietario, ejecutar archivo revisado
   `\i database/permissions.sql`. Solo aplica grants del rol runtime y lectura
   de public.alembic_version. No confundir con políticas Storage ni exponer el
   esquema en Data API.
9. Conectar con runtime por Session pooler usando su usuario exacto. Verificar
   23 tablas, 29 FK, revisión 0003, cuatro funciones, triggers y catálogo. Confirmar
   operaciones reales de API y denegación de DDL/DELETE usuario/UPDATE historial.
   No cambiar al propietario para ocultar un problema de permisos.
10. Si la base demo estaba vacía, provisionar cuentas ficticias privadamente con
    `scripts.seed_demo --allow-remote` únicamente en APP_ENV=demo, Storage real y
    permiso específico para ese seed. El script rechaza producción y usuarios
    existentes; genera claves en `.local/demo-credentials.json`. Si ya hay demo,
    usar el procedimiento administrativo existente, sin resetearla.
11. Ante error, guardar diagnóstico sin secretos. Si falla transacción, comprobar
    revisión antes de reintentar. Las revisiones no admiten downgrade destructivo:
    usar reparación hacia adelante o restauración probada y autorizada. Conciliar
    objetos que pudieron subirse antes de un rollback DB; no hay transacción
    distribuida entre PostgreSQL y Storage.

## Despliegue exacto en Render existente, no ejecutado

1. Obtener autorización específica posterior para desplegar el commit validado.
   Abrir el **servicio Voluntia existente** del repositorio privado original.
   Verificar rama main y **Auto-Deploy = Off**; conservarlo así. No crear servicio
   ni modificar plan/cobros/región como parte de esta guía.
2. En Settings comprobar runtime Docker, Root Directory vacío, Dockerfile Path
   `./Dockerfile`, contexto raíz. Dockerfile compila Angular y copia su build al
   backend; no usar Docker Compose en Render. Mantener CMD de la imagen
   `python -m backend.app.serve`, sin migraciones ni seeds en start/pre-deploy.
3. Environment: configurar exactamente la tabla anterior para demo cerrada:
   APP_ENV=demo, EMAIL_MODE=disabled, PUBLIC_SIGNUP_ENABLED=false,
   STORAGE_BACKEND=supabase, URL/key/bucket reales, DATABASE_URL runtime y
   PUBLIC_BASE_URL igual a la URL HTTPS del servicio. No definir credencial
   migradora en el servicio. No subir .env local ni Mailpit.
4. Guardar variables con **Save only** si todavía se está preparando; las opciones
   **Save and deploy** y **Save, rebuild, and deploy** disparan despliegue y requieren
   la autorización específica. Configurar health check **/api/ready**, que exige DB
   y revisión; /api/health solo demuestra proceso vivo. Cualquier cambio de servicio
   remoto se deja para la fase autorizada, no se ha realizado en esta auditoría.
5. Confirmar que la migración/grants y prueba Storage autorizadas ya terminaron.
   Elegir SHA de main con los tres jobs CI verdes. En **Manual Deploy → Deploy a
   specific commit**, seleccionar ese SHA. Si la interfaz ofrece solamente latest,
   comprobar antes que main sigue exactamente en el SHA revisado y usar **Deploy
   latest commit**. No activar On Commit ni After CI Checks Pass.
6. Revisar logs de build/runtime sin copiar secretos. La app debe escuchar
   0.0.0.0 en PORT de Render; imagen comprobada localmente con PORT=10000. Esperar
   estado Live y /api/ready=200. Una compilación exitosa sola no acredita despliegue.
7. En navegador externo comprobar HTTPS, SPA recargada en /panel, visitante y tres
   roles, cookies Secure/HttpOnly/SameSite, CSRF, registro/recuperación cerrados,
   advertencia demo, archivos privados, certificado y errores/vacíos. Confirmar
   persistencia tras reiniciar servicio y realizar prueba de arranque en frío antes
   de clase. No almacenar archivos en disco efímero como persistencia remota.
8. Registrar URL funcional, SHA, evento de deploy y prueba real Storage con evidencia
   sin secretos. Solo entonces actualizar matriz y reevaluar integración/backend.
   Si falla, conservar logs, revertir únicamente el código a una versión compatible
   por despliegue manual autorizado; no hacer downgrade ciego de DB.

Referencias: [Docker](https://render.com/docs/docker),
[variables y Save only](https://render.com/docs/configure-environment-variables),
[despliegues manuales y Off](https://render.com/docs/deploys),
[health checks](https://render.com/docs/health-checks).

## Limitaciones pendientes y sustentación

- Supabase/Storage/Render reales: autorización y evidencia pendientes. No se
  garantiza conectividad, permisos/quota/CA, bucket o URL a partir de tests locales.
- Correo real: pendiente; demo cerrada preparada. No habilitar producción real
  sin probar proveedor, verificación y recuperación completos.
- Sustentación personal: no evaluada. Explicar transacción/bloqueos, 23 tablas y
  redundancias controladas, roles frente a membresías, cookies/CSRF, Storage frente
  a DB y diferencias demo/producción. Usar [GUIA_SUSTENTACION](GUIA_SUSTENTACION.md).
- Windows universidad: clon probado localmente según cierre siguiente; no se ha
  probado la computadora física universitaria ni conexión Supabase desde su red.
- Archivo subido y transacción DB no son atómicos conjuntamente: una caída posterior
  a la subida puede dejar objeto huérfano; reconciliación administrativa necesaria.
- Certificado inmutable en PDF conserva emisión; consulta pública usa nombres
  actuales de perfil/actividad/organización mediante joins. Un cambio posterior de
  nombre puede diferir del PDF histórico; no es firma digital ni acreditación oficial.
- Sin prueba de carga o auditoría profesional externa; limitador en memoria requiere
  un worker/una instancia. No escalar horizontalmente sin almacén compartido.
- Avisos no bloqueantes: bundle inicial sobre presupuesto y deprecación
  Starlette/TestClient HTTPX. No se ocultaron ni se cambiaron umbrales de aprobación.

### Cierre de validación del cambio

Este apartado se completa con resultados observados del clon y PR de auditoría;
los resultados anteriores no deben interpretarse como despliegue remoto.
