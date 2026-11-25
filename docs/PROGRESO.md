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
