# Matriz de cumplimiento y evidencia

Objetivo: aspirar al nivel Excelente en los cinco criterios de la rúbrica original,
sin garantizar nota. Estado local al 24/11/2026 (Lima); consultar PROGRESO para últimos
resultados y commits. El PDF original fue leído y renderizado en sus tres páginas.

| Criterio /4 | Implementación y evidencia real | Estado / brecha |
|---|---|---|
| Frontend | Angular 22.3 + Bootstrap, rutas lazy, modelos/servicios/guards, formularios reactivos, módulos en `frontend/src/app`. Build exitoso, 5 pruebas unitarias. Clon limpio: Playwright catálogo y ciclo de roles a 1280 y 360 px, 4 passed en 29.4 s. Capturas inspeccionadas localmente. | Comprobado local y CI; advertencia inicial ~615 kB sin ocultar. |
| Backend | FastAPI modular, Swagger, esquemas Pydantic, servicios y autorización de propiedad. Cookies/CSRF/roles, SMTP Mailpit real, ciclo hasta PDF verificable. `backend/tests` con escenarios positivos/negativos. Adaptador Supabase Storage con upload/descarga privada, timeout y error 503, contrato probado mediante transporte de test. | Comprobado local; API externa Storage real pendiente de autorización y credenciales. Correo real pendiente. |
| Base de datos | 23 tablas producto, 29 FK, PK/UNIQUE/CHECK/índices; migraciones 0001/0002; `database/functions.sql` e `invariants.sql`. ERD y diccionario generado con claves/dependencias 3FN. Último cupo y duplicado concurrentes con conexiones PostgreSQL distintas; fallo inyectado revierte estado/historial/aviso/bitácora. Privilegios mínimos probados localmente. | PostgreSQL local comprobado. Migración/pooler/grants remotos pendientes. |
| Integración, despliegue y Git | UI/API/DB locales integradas; Docker multietapa construido, health/ready/SPA HTTP 200 y HEALTHCHECK healthy. Ramas y PR #1–#4 reales integrados con CI verde. `.github/workflows/ci.yml` backend/frontend/Playwright, sin tests desactivados. Scripts Windows setup/check/start/stop. | URL HTTPS pública, persistencia remota, Storage real y despliegue Render pendientes de autorización. Este criterio no está cerrado solo por pruebas locales. |
| Sustentación | Guía detallada por roles/archivos/SQL, matriz, consultas, guías Windows/despliegue y demo ficticia reproducible. Código formateado para lectura. | Ensayo y dominio técnico del estudiante pendientes de su ejecución; no los puede certificar Codex. La falta de sustentación implica cero según rúbrica. |

## Git verificable

| Hito | PR | Evidencia CI / integración |
|---|---|---|
| 23 tablas y funciones | [#1](https://github.com/DenisPrudencio87/Voluntia/pull/1) | 45535945305 y 45535945762, aprobados; merge 202f240 |
| Autenticación/SMTP | [#2](https://github.com/DenisPrudencio87/Voluntia/pull/2) | 45536422012 y 45536428105, aprobados; merge 8ba686b |
| Ciclo funcional | [#3](https://github.com/DenisPrudencio87/Voluntia/pull/3) | 45537546526 y 45537555391, aprobados; merge 496b9c2 |
| Angular e integración | [#4](https://github.com/DenisPrudencio87/Voluntia/pull/4) | Carrera de commit detectada y corregida; 45541698923 y 45541705244 aprobados (backend/frontend/integration); merge 90d75a5 |
| Seguridad/operación/guías | [#5](https://github.com/DenisPrudencio87/Voluntia/pull/5) | Código 4637e14: 45543601332 y 45543606686 aprobados (backend/frontend/integration). Clon limpio: 28 Pytest, 5 Angular, 4 Playwright aprobados; scripts y archivos privados comprobados. Estado/checks finales en enlace. |

Las evidencias privadas requieren acceso del propietario/docente.
No confundir workflow definido con una ejecución exitosa ni prueba simulada con API real.
# Actualización tras auditoría previa al despliegue

La evidencia y evaluación conservadora vigentes están en
[AUDITORIA_FINAL.md](AUDITORIA_FINAL.md). Se corrigieron defectos que la CI previa
no detectaba. Se mantienen separados los resultados locales y los pendientes de
Storage real, URL de Render y sustentación personal; no se acredita 20/20.
