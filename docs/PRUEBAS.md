# Plan de pruebas obligatorio
Usar PostgreSQL descartable; jamás ejecutar limpieza contra producción. Mailpit para pruebas integradas locales de correo; adaptadores fake para pruebas unitarias y almacenamiento local aislado en desarrollo. Datos ficticios, fechas relativas a reloj de prueba; separar fixtures de seeds demo. CI debe fallar si falla cualquier prueba requerida.

| ID | Escenario | Resultado esperado |
|---|---|---|
| DB01 | Migrar BD vacía y consultar restricciones | 23 tablas producto, FK/PK/UNIQUE/CHECK válidas |
| DB02 | Correo duplicado con mayúsculas | Rechazo, una cuenta |
| DB03 | Inscripción duplicada concurrente | Una inscripción, conflicto |
| DB04 | Dos aceptaciones simultáneas para último cupo, conexiones separadas | Una aceptación, otra conflicto; historial y notificación coherentes |
| DB05 | Error dentro de aceptación | Rollback total, sin historial/aviso huérfano |
| DB06 | Fechas/cupo inválidos, FK inexistente | Rechazo |
| DB07 | Horas/estadísticas con múltiples inscritos/evidencias | Sin duplicación |
| API01 | Registro, verificar, login, logout, recuperar | Tokens de un uso, sesión válida, contraseña anterior inválida |
| API02 | Usuario suspendido con token vigente | 403/401 |
| API03 | Visitante/voluntario intenta ruta admin | 401/403 |
| API04 | Organización A modifica actividad/documento B | 403/404 sin fuga |
| API05 | Organización pendiente publica | Rechazo |
| API06 | Borrador, vencida, cancelada/finalizada recibe postulación | Rechazo |
| API07 | Habilidad obligatoria ausente | Rechazo claro |
| API08 | Espera, cancelación y promoción | Cupo liberado, historial y avisos |
| API09 | Asistencia inválida o certificado sin asistencia | Rechazo |
| API10 | Certificado duplicado y código inválido | Sin duplicación, respuesta pública mínima |
| API11 | Archivo falso, demasiado grande, descarga ajena | Rechazo |
| API12 | CSRF inválido, abuso de login/registro | Rechazo/429 |
| API13 | Proveedor correo falla | Error controlado, reintento de envío disponible |
| API14 | Cancelación actividad | Historial y avisos de todos los afectados, transacción |
| API15 | Suspensión organización y último admin | Bloqueos correctos |
| UI01 | Formularios inválidos y error API | Mensajes claros |
| UI02 | Catálogo filtros combinados y paginación | Resultados reales |
| E2E01 | Admin aprueba organización, publica, voluntario postula, acepta, asistencia, impacto, certificado y verificación | Flujo completo con datos persistentes; reloj/fixture de test para fechas, no saltarse reglas en producción |
| E2E02 | Recorrido móvil 360px y escritorio 1280px | Sin overflow horizontal general, navegación usable |
| OPS01 | Docker build y smoke test | /, /api/health, /api/ready funcionales |
| OPS02 | CI en PR | Build frontend y tests backend/DB exitosos, E2E según workflow |
| OPS03 | URL real, Storage real, reinicio | HTTPS, persistencia y operaciones reales tras autorización |
| OPS04 | Mailpit: verificación y recuperación de cuenta local | Mensajes y tokens funcionales, sin correo a usuarios reales |
| OPS05 | Demo remota sin correo | Registro/recuperación por correo deshabilitados, sin bypass; cuentas ficticias provisionadas de manera segura |
| OPS06 | Clon limpio Windows, scripts setup/start/check/stop | Instalación reproducible, puertos comprobados, solo procesos propios detenidos; sin Docker para ejecución con BD de demo accesible |
| OPS07 | Correo real en producción (pendiente de proveedor) | Entrega real, verificación y recuperación probadas antes de habilitar registro público |

Registrar comando, duración si disponible, fecha, éxito/fallo y evidencia. No inventar resultados. Añadir pruebas cuando se detecte una regresión. Usar Playwright y Pytest; TestSprite opcional únicamente si ya disponible y sin transmitir datos sensibles, no es requisito.

## Ejecución implementada

Las fixtures migran mediante Alembic y solo limpian `voluntia_test` (sufijo `_test`
obligatorio). La base de demo `voluntia` no se limpia. No ejecutar Pytest mientras
Playwright usa esa misma base de test; CI utiliza contenedores independientes por job.
No se usa SQLite. Mailpit debe estar disponible para la suite de autenticación.

```powershell
docker compose up -d --wait db mailpit
# Solo la primera vez:
docker compose exec -T db createdb -U voluntia voluntia_test
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm.cmd test -- --watch=false
npm.cmd run build
cd ..
```

Playwright integrado contra el build servido por FastAPI, en una terminal exclusiva:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://voluntia:voluntia_local@127.0.0.1:55432/voluntia_test'
$env:DATABASE_URL=$env:TEST_DATABASE_URL
$env:MIGRATION_DATABASE_URL=$env:TEST_DATABASE_URL
$env:PUBLIC_BASE_URL='http://localhost:8000'
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m scripts.e2e_seed
# Si ya existen solo cuentas de ese fixture: e2e_seed --rotate, sin borrar datos.
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd frontend
$env:E2E_BASE_URL='http://localhost:8000'
$env:TEST_DATABASE_URL='postgresql+psycopg://voluntia:voluntia_local@127.0.0.1:55432/voluntia_test'
$env:PLAYWRIGHT_BROWSERS_PATH='../.local/ms-playwright'
npx.cmd --cache ../.local/npm-cache playwright install chromium
npx.cmd --cache ../.local/npm-cache playwright test
```

Si falta `.env`, primero ejecutar setup para generar secreto local. Los valores
anteriores son exclusivamente credenciales locales ficticias de Compose. Para CI,
el workflow configura todos los valores efímeros y usa Python por `E2E_PYTHON`.
El reloj E2E es un script que se niega a operar fuera de base local `_test`; no hay
endpoint de bypass en aplicación. Tras finalizar, detener el servidor propio.

## Trazabilidad de pruebas

| IDs | Archivos / comprobación |
|---|---|
| DB01–DB06 | `test_database.py`: 23 tablas/29 FK, correo, conexiones concurrentes, rollback posterior e inyectado dentro del trigger, constraints y actor/historial. |
| DB07 | `test_aggregation.py`, `test_domain.py`: varias inscripciones/evidencias, asistencia y horas/beneficiarios sin multiplicación. |
| API01–API03, API12–API13 | `test_auth.py`, `test_security.py`: SMTP real Mailpit, token único, sesión/revocación, suspensión, roles, CSRF, rate limit, fallo SMTP y reintento. |
| API04–API10, API14–API15 | `test_domain.py`, `test_security.py`: propiedad, revisión, plazos/habilidades, espera/cancelación/promoción, asistencia/certificado, suspensión y último admin. |
| API11 | `test_storage.py`, recorrido domain: firmas/tamaño/reencodificación y descarga ajena denegada. |
| UI01 | `record-form.spec.ts`: campos, confirmación, fechas, conservación de edición; `guards/auth.spec.ts` y `services/api.spec.ts`. |
| UI02, E2E01–E2E02 | `frontend/e2e/journey.spec.ts`: catálogo y ciclo completo, tamaños 1280×800 y 360×800; sin overflow general. |
| OPS01 | Build/run Docker local, health/ready/SPA y HEALTHCHECK healthy. |
| OPS02 | Jobs backend, frontend e integración de CI; URLs de ejecuciones en PROGRESO/MATRIZ_RUBRICA. |
| OPS04–OPS05 | Mailpit y bloqueo de registro/recuperación en tests y validadores Settings. |
| OPS06 | Scripts setup/check/start/stop Windows, prueba desde clon limpio; registrar commit/resultado en PROGRESO. |
| OPS03, OPS07 | PENDIENTES: URL remota, persistencia/Storage real y correo real tras autorización/proveedor. |

`test_supabase_adapter_contract_and_failure` usa MockTransport de test para verificar
contrato y errores HTTP; no prueba Storage remoto. Archivos/credenciales E2E y logs
quedan ignorados; no publicar snapshots de credenciales de cuentas ficticias.
