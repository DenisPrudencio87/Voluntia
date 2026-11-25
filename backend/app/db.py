from sqlalchemy import create_engine, text, event
from backend.app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,
    pool_timeout=10,
    connect_args={"connect_timeout": 10},
)


@event.listens_for(engine, "connect")
def configure_search_path(connection, record):
    # SET en autocommit persiste tras rollback y funciona en Session pooler;
    # no depende de la opción de protocolo startup "options".
    previous = connection.autocommit
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO voluntia, public")
    finally:
        connection.autocommit = previous


def transaction():
    with engine.begin() as connection:
        yield connection


def actor_context(connection, user_id):
    connection.execute(
        text("SELECT set_config('app.actor_id', :actor, true)"), {"actor": str(user_id)}
    )


def one(connection, sql, **params):
    return connection.execute(text(sql), params).mappings().first()


def rows(connection, sql, **params):
    return list(connection.execute(text(sql), params).mappings())


def execute(connection, sql, **params):
    return connection.execute(text(sql), params)
