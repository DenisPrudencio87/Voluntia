"""Un mismo SQL versionado para ejecución online y exportación --sql de Alembic."""

from pathlib import Path
from alembic import context, op


def apply_sql(filename):
    sql = (Path(__file__).resolve().parents[2] / "database" / filename).read_text(
        encoding="utf-8"
    )
    if context.is_offline_mode():
        op.execute(sql)
    else:
        with op.get_bind().connection.driver_connection.cursor() as cursor:
            cursor.execute(sql, prepare=False)
