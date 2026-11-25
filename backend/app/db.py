from sqlalchemy import create_engine, text
from backend.app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True,
                       connect_args={'options': '-csearch_path=voluntia,public'})


def transaction():
    with engine.begin() as connection:
        yield connection


def actor_context(connection, user_id):
    connection.execute(text("SELECT set_config('app.actor_id', :actor, true)"), {'actor': str(user_id)})


def one(connection, sql, **params):
    return connection.execute(text(sql), params).mappings().first()


def rows(connection, sql, **params):
    return list(connection.execute(text(sql), params).mappings())


def execute(connection, sql, **params):
    return connection.execute(text(sql), params)
