from alembic import context
from sqlalchemy import create_engine, pool
from backend.app.config import settings

url = settings.migration_database_url or settings.database_url
if context.is_offline_mode():
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with create_engine(url, poolclass=pool.NullPool).connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()
