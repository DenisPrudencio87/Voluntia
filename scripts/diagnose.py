from sqlalchemy import text
from backend.app.config import settings
from backend.app.db import engine

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
    print("Configuración válida. PostgreSQL accesible y esquema de 23 tablas presente.")
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
