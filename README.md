# Voluntia

Plataforma académica de voluntariado. Angular + Bootstrap, FastAPI y PostgreSQL.
Estado y evidencia: [docs/PROGRESO.md](docs/PROGRESO.md). Implementación en curso.

## Desarrollo local

Requisitos: Python 3.13, Node 24, npm.cmd y PostgreSQL 17. Docker es opcional
para ejecutar la aplicación y facilita PostgreSQL y Mailpit aislados.
No se han aplicado migraciones remotas ni desplegado en Render.

```powershell
docker compose up -d
# Configuración y comandos completos se incorporan durante las fases de implementación.
```

Los secretos viven en `.env` (ignorado). `.env.example` contiene únicamente
valores de desarrollo local y nombres de variables. No usar sus credenciales
de PostgreSQL local en servicios remotos.
