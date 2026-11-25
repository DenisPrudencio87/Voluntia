"""Modelo aprobado, catálogos y funciones transaccionales (23 tablas)."""

from pathlib import Path
from alembic import op

revision = "0001"
down_revision = None
branch_labels = depends_on = None


def upgrade():
    root = Path(__file__).resolve().parents[3] / "database"
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        for name in ("schema.sql", "functions.sql", "triggers.sql", "catalogs.sql"):
            cursor.execute((root / name).read_text(encoding="utf-8"), prepare=False)


def downgrade():
    raise RuntimeError(
        "No se permite borrado automático del historial. Restaurar backup aislado."
    )
