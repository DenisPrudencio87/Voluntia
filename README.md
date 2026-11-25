# Voluntia

Plataforma académica de voluntariado. Angular + Bootstrap, FastAPI y PostgreSQL.
Aplicación local implementada con paneles de voluntariado, organización y administración.
Estado y evidencia verificable: [docs/PROGRESO.md](docs/PROGRESO.md).
No se ha publicado en Render ni migrado Supabase remoto.

## Desarrollo local

Requisitos: Python 3.13, Node 24, npm.cmd y PostgreSQL 17. Docker es opcional
para ejecutar la aplicación y facilita PostgreSQL y Mailpit aislados.
No se han aplicado migraciones remotas ni desplegado en Render.

Desde la raíz del clon, en PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup.ps1 -Docker
.\.venv\Scripts\python.exe -m scripts.seed_demo
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1
# Abrir http://localhost:4200 — Swagger: http://localhost:8000/docs
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop.ps1
```

`ExecutionPolicy Bypass` se limita al proceso invocado, sin cambiar políticas globales.
El seed se niega a modificar una base con usuarios. Las cuentas son ficticias y sus
claves aleatorias quedan en `.local/demo-credentials.json`, ignorado por Git.
Leer el archivo privadamente; no pegarlo en chat, CI ni capturas. La cuenta de
administración se mantiene separada. La demo preactivada no demuestra correo real.

Sin Docker: ejecutar `setup.ps1 -ClosedDemo`, configurar privadamente en `.env` una
base PostgreSQL de demo ya migrada y usar `start.ps1 -Built` (una URL en puerto 8000)
o `start.ps1` (Angular 4200 y API 8000). No se aplican migraciones remotas al iniciar.
Ver [guía universitaria](docs/GUIA_EJECUCION_UNIVERSIDAD.md).

## Contenedores

```powershell
docker compose up -d --wait db mailpit
.\.venv\Scripts\python.exe -m scripts.migrate --local
docker compose --profile app up -d --build app
# http://localhost:8080 — Mailpit local: http://localhost:8025
docker compose --profile app stop
```

No usar `down -v` para detener: borra datos locales. El Dockerfile no migra ni
provisiona usuarios al arrancar. Supabase Storage es obligatorio en modo remoto;
el almacenamiento local es exclusivamente de desarrollo/pruebas.

## Validación

```powershell
# Crear una vez la BD de pruebas exclusiva, separada de voluntia:
docker compose exec -T db createdb -U voluntia voluntia_test
.\.venv\Scripts\python.exe -m pytest backend/tests -q
Set-Location frontend
npm.cmd test -- --watch=false
npm.cmd run build
Set-Location ..
```

La suite se niega a limpiar una BD cuyo nombre no termine en `_test`. Playwright
requiere su fixture y servidor exclusivos; instrucciones en [PRUEBAS](docs/PRUEBAS.md).

Versiones fijadas: Python 3.13 (local 3.13.15), Node 24.21.0, npm 11.19.0,
Angular 22.3.0, Bootstrap 5.3.9, Bootstrap Icons 1.13.2, PostgreSQL 17.7,
FastAPI 0.165.0, SQLAlchemy 2.1.9, psycopg 3.3.9, Alembic 1.20.1.
Los lockfiles incluyen dependencias transitivas.

## Documentación

- [Arquitectura](docs/ARQUITECTURA.md), [23 tablas y reglas](docs/BASE_DE_DATOS.md), [ERD](docs/ERD.md), [diccionario físico/3FN](docs/DICCIONARIO_FISICO.md).
- [Despliegue preparado](docs/GUIA_DESPLIEGUE.md), [seguridad y operación](docs/SEGURIDAD_Y_OPERACION.md).
- [Matriz de rúbrica](docs/MATRIZ_RUBRICA.md), [sustentación](docs/GUIA_SUSTENTACION.md), [ejecución universitaria](docs/GUIA_EJECUCION_UNIVERSIDAD.md).

El despliegue HTTPS y Storage real requieren autorización específica posterior.
El proveedor de correo real sigue pendiente. No se garantiza una calificación.

Los secretos viven en `.env` (ignorado). `.env.example` contiene únicamente
valores de desarrollo local y nombres de variables. No usar sus credenciales
de PostgreSQL local en servicios remotos.
