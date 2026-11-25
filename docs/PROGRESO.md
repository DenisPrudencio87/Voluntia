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

Siguiente acción: registrar PR de auth, continuar perfiles/organizaciones y ciclo de actividad con pruebas de autorización y fechas.
