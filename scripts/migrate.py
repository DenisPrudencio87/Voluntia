"""Migración explícita: destino local por defecto, nunca se ejecuta al iniciar web."""

import argparse
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command
from backend.app.config import settings

parser = argparse.ArgumentParser()
parser.add_argument("--local", action="store_true")
parser.add_argument("--allow-remote", action="store_true")
parser.add_argument("--confirm-database")
args = parser.parse_args()
url = make_url(settings.migration_database_url or settings.database_url)
local = url.host in ("localhost", "127.0.0.1", "db") and settings.app_env in (
    "local",
    "test",
)
if args.local and not local:
    raise SystemExit("Destino no local: no se aplicó ninguna migración")
if not local and not (args.allow_remote and args.confirm_database == url.database):
    raise SystemExit(
        "Migración remota bloqueada. Requiere autorización del propietario y confirmación explícita de base."
    )
print(f"Destino: host={url.host}, base={url.database}; no se muestran credenciales")
command.upgrade(Config("backend/alembic.ini"), "head")
print("Migración completada")
