"""Refuerza invariantes de ocupación e inmutabilidad sin nuevas tablas."""

from backend.migrations.sql import apply_sql

revision = "0002"
down_revision = "0001"
branch_labels = depends_on = None


def upgrade():
    apply_sql("invariants.sql")


def downgrade():
    raise RuntimeError("No degradar invariantes de seguridad automáticamente")
