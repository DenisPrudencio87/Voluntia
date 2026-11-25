from sqlalchemy import text
from backend.app.config import settings
from backend.app.db import engine
from alembic.config import Config
from alembic.script import ScriptDirectory

try:
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM rol")).scalar() == 3
        assert (
            c.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema='voluntia'"
                )
            ).scalar()
            == 23
        )
        head = ScriptDirectory.from_config(
            Config("backend/alembic.ini")
        ).get_current_head()
        assert (
            c.execute(text("SELECT version_num FROM public.alembic_version")).scalar()
            == head
        )
    print("Configuración válida. PostgreSQL accesible, 23 tablas y migración vigente.")
    print(
        "Modo:",
        settings.app_env,
        "| correo:",
        settings.email_mode,
        "| storage:",
        settings.storage_backend,
    )
except Exception:
    raise SystemExit(
        "No se pudo validar PostgreSQL/esquema. Revisar .env privado, conectividad y migración explícita; no se muestran secretos."
    )
