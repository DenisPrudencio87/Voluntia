from alembic import context
from sqlalchemy import create_engine, pool
from backend.app.config import settings

url = settings.migration_database_url or settings.database_url
if context.is_offline_mode():
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="public",
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url, poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection, version_table_schema="public")
        with context.begin_transaction():
            context.run_migrations()
