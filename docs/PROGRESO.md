# Progreso
Estado inicial revisado 24/11/2026: documentación actualizada; implementación aún no iniciada. Herramientas locales verificadas por el propietario, Docker hello-world correcto; repositorio privado existente y sincronizado en 0ed76f1 antes de esta actualización. Supabase Session pooler seleccionado, conexión aún no probada. Render clona repositorio; primer deploy falló por ausencia de Dockerfile; Auto-Deploy desactivado. Correo real pendiente. Ninguna prueba de aplicación, CI, Storage real ni URL funcional se ha ejecutado/verificado todavía.

## Fase 0 — 24/11/2026

- Leídos íntegramente AGENTS, PROMPT y documentos activos. Rúbrica extraída con pypdf (3 páginas); caracteres acentuados defectuosos en extracción, cotejado resumen operativo.
- Repositorio limpio en `60d0dab`, origin correcto; fetch exitoso. Rama `feature/fase-0-1-base-datos`.
- Verificados Node 24.21.0, npm.cmd 11.19.0, Python 3.13.15, Docker 29.9.3 / Desktop 4.100.1, Compose 5.7.1 y gh autenticado. El sandbox no accede al keyring/Python/Docker: se requiere ejecución elevada de esas herramientas, sin cambiar configuración global.
- `.gitignore` ya protege secretos; añadidos `.env.example`, Compose aislado (puertos solo loopback), venv local, requisitos de backend, README y estructura inicial.
- Instalación de dependencias y descarga de imágenes iniciadas; aún sin resultado de pruebas de aplicación.
- No se ha accedido a Supabase ni Render, ni aplicado migraciones remotas.

## Fase 1 — en curso

Implementados SQL de 23 tablas, catálogos, cuatro funciones, trigger de historial/avisos, protección de auditoría, validación de asistencia y sincronización de impacto. Alembic es el único instalador del esquema.

Resultado local: `python -m alembic -c backend/alembic.ini upgrade head` exitoso. `python -m pytest backend/tests/test_database.py -q`: **8 passed, 1.00 s**. Cubiertos conteo 23/29, correo, último cupo concurrente (dos conexiones), rollback, actor, historial inmutable, fechas/cupo, duplicado y agregación. Corregida ejecución de scripts Alembic con cursor sin parámetros para preservar `%I` de PostgreSQL. Corregida expectativa inicial de FK (29 según diccionario).

Generados `docs/DICCIONARIO_FISICO.md` y `docs/ERD.md` desde PostgreSQL. Fijados requisitos completos en UTF-8 mediante `scripts/lock_dependencies.py`. CI backend configurado, todavía sin ejecución remota verificada.

PR #1: https://github.com/DenisPrudencio87/Voluntia/pull/1. CI aprobado en ejecuciones 45535945305 y 45535945762. Diff revisado, PR integrado (merge `202f240`), sin cambios ajenos ni conflictos.

## Fase 2 — autenticación

- Implementados routers/esquemas/servicios de cuenta, Argon2id, JWT 30 min en cookie HttpOnly, CSRF firmado y Origin, roles revalidados, bloqueo de suspendidos, revocación por timestamp de seguridad, límites por cuenta/IP, errores sin secretos.
- SMTP configurable con timeout y TLS remoto. Registro, verificación, reenvío y recuperación con tokens hash, expiración, rotación y uso único. Demo sin correo cierra registro y recuperación en servidor.
- `python -m pytest backend/tests -q`: **14 passed, 15.12 s** con PostgreSQL y Mailpit reales. Pruebas de SMTP fallido/rollback/reintento, token reutilizado, contraseña anterior, sesión revocada, suspensión, CSRF, rate limit y campos privilegiados.
- Aviso de deprecación de TestClient/httpx en Starlette; no afecta resultado, pendiente evaluar actualización del adaptador de pruebas.

PR #2: https://github.com/DenisPrudencio87/Voluntia/pull/2. CI aprobado (45536422012 y 45536428105), diff revisado, integrado en `8ba686b`. Última suite auth/DB: 14 passed en 14.66 s.

## Fase 3 — ciclo funcional

Rama `feature/fase-3-ciclo-voluntariado`. Implementados catálogo público con filtros, perfiles/habilidades, organizaciones/membresías/documentos privados, revisión administrativa, roles/estados/catálogos, actividades/inscripciones/espera/historial, asistencia, impacto, evidencia privada, certificados PDF y verificación pública mínima.

`python -m pytest backend/tests/test_domain.py -q`: **3 passed, 6.73 s**. Recorrido completo comprobado con PostgreSQL y archivos locales, incluyendo certificado leído con pypdf, descarga ajena denegada, duplicación idempotente, inmutabilidad de asistencia certificada, espera/cancelación/promoción e historial. Fixture modifica fechas exclusivamente en `_test` para simular el paso de días; no existe bypass temporal en API. Corregido error PostgreSQL 42P08 de publicación tras identificarlo en pruebas.

Supabase Storage integrado por HTTP (upload y URL firmada 60 s, timeout y error controlado); prueba remota pendiente de autorización. No se ha probado con credenciales remotas ni se afirma lo contrario.

Suite completa de backend: **17 passed, 19.13 s**. PR #3 https://github.com/DenisPrudencio87/Voluntia/pull/3, CI verde (45537546526 y 45537555391), diff revisado e integrado en `496b9c2`.

## Fases 4 y 5 — Angular e integración en curso

Angular 22.3.0, Bootstrap e Icons, formularios reactivos reutilizables, modelos, servicios, interceptor CSRF, guards, rutas lazy, inicio/catálogo/detalle/perfil público, auth completa, panel voluntario/perfil/historial/certificados/notificaciones, organización/documentos/miembros/actividades/participantes/asistencia/impacto/evidencias, administración y seguridad.

- `npm.cmd run build`: exitoso; 614.8 kB iniciales, transferencia estimada 114.4 kB. Advertencia del presupuesto inicial de 500 kB conservada, sin ocultarla.
- `npm.cmd test -- --watch=false`: **4 pruebas aprobadas en 3 archivos**, validación/confirmación de claves, conservación de formulario durante carga, guard de roles e interceptor CSRF.
- Playwright instalado localmente en `.local/ms-playwright` sin instalación global. Cuentas ficticias E2E en `voluntia_test`; claves aleatorias en archivo ignorado, sin imprimirlas.
- Primera ejecución E2E detectó ruta incorrecta del build en FastAPI (404 de SPA). Corregida y verificados `/` y `/api/ready` con HTTP 200. Repetición E2E en curso; todavía no se declara aprobada.

`npx playwright test`: **4 passed, 23.8 s** (1280×800 y 360×800). Catálogo/filtros/validación y recorrido admin→documento→organización→publicación→perfil→postulación→aceptación→asistencia→impacto→certificado→verificación, con persistencia PostgreSQL. Sin overflow horizontal en páginas de roles. Revisión visual de capturas local; ajustados gutters móviles.

Corregidos durante E2E: CSP frente a script inline de optimización CSS (deshabilitado inlineCritical, CSP conservada), etiquetas con asterisco y estado asíncrono de selección documental con signal. Una repetición móvil alcanzó rate limit por intentos acumulados: ejecución limpia aprobada con límites activos y claves ficticias rotadas. No se publican credenciales de fixtures.

CI ampliado con jobs frontend e integración Playwright; pendiente verificar en PR. Suite backend ampliada: **21 passed, 17.87 s**, incluido fallo inyectado dentro de aceptación, duplicación concurrente real y contrato/error del adaptador Storage mediante MockTransport de prueba (no evidencia remota).

## Fase 8 — verificación local adelantada

Dockerfile multietapa construido (`docker compose --profile app build app`). Imagen ejecutada: `/`, `/api/health`, `/api/ready` HTTP 200 en localhost:8080; HEALTHCHECK `healthy`. Usuario no root; sin migración automática al iniciar. Ningún despliegue remoto.

Scripts Windows check/start -Built/stop probados con Python y base accesible: versiones y 23 tablas correctas, HTTP 200 en puerto propio 8010, detenido solo proceso registrado. Aplicación ejecutada sin Docker como dependencia del proceso (PostgreSQL local provenía de contenedor); no es evidencia de una PC universitaria ni de Supabase remoto.

Siguiente acción: PR de Angular/CI, fase 6 de seguridad y pruebas negativas; completar setup/start desarrollo, clon limpio, guías y matriz. Publicación/Storage remoto continúan pendientes de autorización específica.

## Fases 6–9 — seguridad, operación y documentación

- PR #4 detectó carrera real: 201 antes del commit, GET inmediato 404. Artefactos de CI 45541184011 confirmaron la secuencia. Corregido con dependencias de alcance function en commit `1e0cb25`. CI 45541698923 y 45541705244: backend/frontend/integration aprobados; diff revisado, PR integrado en `90d75a5`.
- Migración 0002 aplicada solo local: invariantes adicionales, certificado inmutable, grants privados; siguen 23 tablas. Rol NOLOGIN equivalente a runtime probado sin DDL/DELETE de usuarios y con aceptación SQL funcional. No se aplicó ningún grant ni migración remota.
- Última suite: `python -m pytest backend/tests -q`: **28 passed, 21.86 s**. Incluye agregación con múltiples evidencias, documento nuevo fuerza revisión, suspensión/plazos y configuración cerrada. `ruff check --select F backend scripts`: aprobado. Formato Python/Angular aplicado para legibilidad. Aviso de deprecación HTTPX/TestClient conservado; no afecta resultado.
- `npm.cmd test -- --watch=false`: **5 passed, 3 archivos**. `npm.cmd run build`: exitoso, advertencia ~615 kB iniciales registrada. Auditorías `pip_audit -r backend/requirements.txt` y `npm audit --omit=dev`: sin vulnerabilidades conocidas reportadas en la consulta realizada.
- Rúbrica renderizada completa (3 páginas) e inspeccionada. Certificado ficticio renderizado: una página, texto/acentos legibles. PDF fecha de emisión en Lima, eventos almacenados UTC.
- Windows: setup exitoso con dependencias fijadas; check/start -Built/stop y start de desarrollo con puertos 8011/4211 aprobados, `/` y `/api/ready` por proxy 200. Detectado y corregido BOM en JSON generado por PowerShell 5. Solo procesos propios detenidos. No se cambió ninguna política global.
- Docker imagen final reconstruida; usuario no root, health/ready/SPA 200 y HEALTHCHECK healthy. Smoke HTTP de archivos existente/nuevo contra contenedor: upload/download autorizado y revisión documental aprobados; visitante 401. Storage local compartido con host en carpeta ignorada. Esto no es prueba Supabase Storage real.
- Demo ficticia local creada en base inicialmente vacía: tres cuentas con claves aleatorias en `.local/demo-credentials.json`, manifiesto privado, organizaciones/documentos ficticios y actividades futuras/histórica. No se imprimen credenciales ni se simula correo real. Seed rechaza base con usuarios y producción.
- Backup `pg_dump -Fc`, restauración `pg_restore --no-owner --no-acl --exit-on-error` en base exclusiva `voluntia_restore_test`: **23 tablas y 3 usuarios**, original intacta.
- Creadas guías de ejecución universitaria, despliegue, sustentación, seguridad/operación y matriz. Proveedor correo, URL HTTPS y Storage remoto pendientes.

## Clon limpio y evidencia final — 24/11/2026, Lima

- Clon real desde GitHub privado en `.local/clean-clone`, rama final, commit de código `4637e142f1c4bf027b03632af6b1dfddf98d75e8`. Sin reutilizar venv, node_modules, build ni `.env` del directorio original. Se reutilizó únicamente el navegador descargado como dependencia de pruebas.
- `setup.ps1 -ClosedDemo`: venv nueva Python 3.13.15, pip desde lockfile, npm ci, Angular build aprobados. Configuración nueva con secreto aleatorio. Se detectó necesidad de fixtures independientes de `.env`; corregido para forzar SMTP local/Storage de test y rechazar bases de tests remotas.
- Bases exclusivas nuevas `voluntia_clone_demo` y `voluntia_clean_test`, sin tocar la demo original. Migración local vacía 0001→0002 aprobada y seed ficticio completo creado desde clon.
- `check.ps1`, `start.ps1 -BackendPort 8012 -Built`, smoke HTTP y `stop.ps1`: aprobados. SPA/readiness 200, login y descarga de documento propios, recuperación cerrada 403. `git status --short` del clon sin cambios versionados. Solo detenido proceso propio.
- Pytest desde clon: **28 passed, 21.06 s**. Angular desde clon: **5 passed, 3 archivos**. Playwright desde clon: **4 passed, 29.4 s**, escritorio/móvil, incluyendo ciclo completo hasta verificación de certificado con PostgreSQL y archivos del clon.
- PR final [#5](https://github.com/DenisPrudencio87/Voluntia/pull/5). CI del código `4637e14`: [45543601332](https://github.com/DenisPrudencio87/Voluntia/actions/runs/45543601332) y [45543606686](https://github.com/DenisPrudencio87/Voluntia/actions/runs/45543606686), jobs backend/frontend/integration aprobados. Estado de integración y checks del último commit documental se consulta en el PR.
- Sin patrones de claves privadas/GitHub/Supabase detectados por `scripts.check_secrets` en versionados; revisión manual y `.gitignore` comprobados. No se publican `.env`, claves de demo, archivos privados ni logs de fixtures.

Estado: implementación y verificación local terminadas; publicación remota no realizada. Docker demo disponible en `http://localhost:8080`, Mailpit exclusivamente `http://localhost:8025`. Credenciales ficticias privadas en `.local/demo-credentials.json`; no mostrarlas al proyectar. Los servidores temporales de tests se detienen al cerrar la verificación.

Siguiente acción que requiere propietario: autorizar específicamente migración/grants y prueba de Storage en la demo Supabase, y posteriormente despliegue manual del servicio Render existente conforme a GUIA_DESPLIEGUE. Configurar secretos por canal privado, no chat. Mantener registro/recuperación remotos cerrados mientras falte correo. Ver INFORME_BRECHAS para límites académicos y producción.

## Auditoría final solicitada — 24/11/2026, Lima (en curso)

- Rama `feature/auditoria-final` desde main `fbdd430`; revisión independiente de implementación, especificaciones y PDF original. Sin modificaciones remotas de Supabase/Render.
- Se reprodujeron antes de corregir **10 fallos backend y 2 de Angular**: permisos organizativos recuperables, rechazo documental invisible, logout vencido, CSRF Unicode, aceptación SQL sin rol vigente o fuera de plazo real, archivos MIME/PDF activos y error de disco, confirmaciones borradas y concurrencia de Feedback.
- Corregidos con regresiones. Primera suite ampliada: **49 passed** backend; Angular **7 passed**. Compilación aprobada; advertencia inicial 615.62 kB pendiente de optimización opcional. Ruff con selección F y pip check aprobados. La ejecución exploratoria de Ruff sin selección encontró reglas de estilo adicionales; no se declara aprobada esa configuración.
- Revisión 0003 mantiene 23 tablas. Probadas migración incremental 0002→0003, idempotencia y exportación SQL seguida de ejecución real en base vacía. SQL original 0001/0002 conservado; adaptado únicamente el cargador Python para soportar `--sql`. Readiness exige head y 23 tablas; runtime recibe lectura de `public.alembic_version`.
- Navegador ampliado detectó cierre de detalles tras refrescar organización; corregido manteniendo selección y cargo autoritativo. Segundo recorrido: 7/8; único fallo restante de esa ejecución fue límite correcto de reenvío acumulado entre repeticiones, por lo que se reinicia el servidor de pruebas antes de una ejecución completa nueva. No se eliminan límites para pasar pruebas.
- Docker construido y arrancado en red local propia, `PORT=10000`, SPA/ready HTTP 200, UID 999 sin root. Primer intento con alias host sin TLS rechazado por configuración; corregida la invocación usando el servicio PostgreSQL local `db`.
- Consultas de seguridad: pip-audit producción y npm audit `--omit=dev` sin vulnerabilidades conocidas en esta consulta. Storage admite claves actuales `sb_secret_*` vía apikey y JWT legacy vía Bearer; adaptador real remoto aún no probado.

Siguiente: cerrar recorridos completos desde servidor limpio, revisión visual, clon limpio Windows, informe con puntuación conservadora, PR y CI del cambio.

### Auditoría: cierre funcional y clon (continuación)

- 8 recorridos ampliados de navegador aprobados en **57.2 s**, ahora con upload/download de evidencia, descarga de certificado, historial, notificaciones y logout. Se detectaron y corrigieron historial no reactivo y confirmación de salida perdida. Capturas escritorio/móvil inspeccionadas; sin overflow global, tablas con scroll interno.
- Protección de query tokens en uvicorn.access sin ocultar errores ni estados; respuestas inesperadas de firma Storage producen 503. Primera ejecución en clon: **57 pytest passed**, Angular **8 passed**.
- PR real [#6](https://github.com/DenisPrudencio87/Voluntia/pull/6), rama propia. CI señaló error en expectativa de coordinador del test: lectura documental permitida, escritura/miembros restringidos. Se corrigió el test y su sincronización sobre H2 del detalle; regresión HTTP añadida. No se cambió autorización de producción para el test.
- Clon limpio desde GitHub, setup nuevo, descubierto/corregido quoting de Node en PowerShell 5 (`10d079d`); repetición correcta. Base nueva, rol LOGIN mínimo, migración 0003/seed con runtime y scripts check/start compilado/start desarrollo/stop aprobados. Smoke con tres roles, archivos, IDOR y recuperación cerrada aprobado. No se reutilizó venv/node_modules/build/.env.
- Docker final reconstruido desde `e22325c`; falta registrar arranque final y CI tras corregir expectativa. No se integrará PR mientras sus checks no estén verdes.

### Cierre local y nueva autorización — 25/11/2026

- Clon `6bc74fb`: backend **58 passed, 26.24 s**; Angular **8 passed, 2.96 s**; navegador **8 passed, 55.9 s**, escritorio/móvil, con fixtures y servidor del clon. No se repite auditoría general.
- Docker final arrancado con runtime SQL limitado, Storage local persistido del clon y PORT=10000; UID 999, healthy, smoke de tres roles y archivos aprobado. Se conserva demo local original.
- Nueva instrucción del propietario autoriza Supabase remoto, runtime, migraciones/grants/Storage/demo y GitHub público después de revisión específica de exposición. Claves existentes no se rotan. Render lo desplegará el propietario, sin CLI ni Auto-Deploy.
- Entrada `.local/supabase-input.env` presente y gitignored; inspeccionados solo nombres, sin imprimir valores. Destinos privados remotos serán separados de demo local. Generado registro EVIDENCIAS_DESPLIEGUE con resultados pendientes explícitos.
- Bloqueo operativo: revisión automática de comandos protegidos devolvió límite de uso antes de ejecutar consulta GitHub. No se conoce aún resultado final de CI/estado PR; no integrar ni operar Supabase hasta resolver el control y verificar versión estable. Solicitada intervención para restablecer disponibilidad; preparación documental independiente continuada.
- Revisión local específica de exposición, sin repetir auditoría: 285 objetos blobs/commits en 17 refs locales, sin coincidencias de las dos credenciales Supabase reales ni patrones de claves y sin rutas privadas versionadas. Valores comparados en memoria, no impresos ni pasados como argumentos Git. Faltan refs remotas actualizadas, PR, logs y artefactos para publicar con seguridad.
