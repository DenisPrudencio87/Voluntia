"""Refuerza invariantes de ocupación e inmutabilidad sin nuevas tablas."""

from pathlib import Path
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = depends_on = None


def upgrade():
    root = Path(__file__).resolve().parents[3] / "database"
    with op.get_bind().connection.driver_connection.cursor() as cursor:
        cursor.execute(
            (root / "invariants.sql").read_text(encoding="utf-8"), prepare=False
        )


def downgrade():
    raise RuntimeError("No degradar invariantes de seguridad automáticamente")
