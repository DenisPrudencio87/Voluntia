"""Auditoría: autorización SQL y reloj efectivo de aceptación."""

from backend.migrations.sql import apply_sql

revision = "0003"
down_revision = "0002"
branch_labels = depends_on = None


def upgrade():
    apply_sql("audit.sql")


def downgrade():
    raise RuntimeError("No desactivar controles de autorización de la auditoría")
