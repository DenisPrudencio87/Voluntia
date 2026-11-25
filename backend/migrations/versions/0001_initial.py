"""Modelo aprobado, catálogos y funciones transaccionales (23 tablas)."""

from backend.migrations.sql import apply_sql

revision = "0001"
down_revision = None
branch_labels = depends_on = None


def upgrade():
    for name in ("schema.sql", "functions.sql", "triggers.sql", "catalogs.sql"):
        apply_sql(name)


def downgrade():
    raise RuntimeError(
        "No se permite borrado automático del historial. Restaurar backup aislado."
    )
