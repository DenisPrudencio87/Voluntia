import os
import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command

# Solo una base explícita descartable. Nunca usar DATABASE_URL de la aplicación.
test_url = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://voluntia:voluntia_local@127.0.0.1:55432/voluntia_test",
)
if not make_url(test_url).database.endswith("_test") or make_url(test_url).host not in (
    "localhost",
    "127.0.0.1",
    "postgres",
    "db",
):
    raise RuntimeError("Pruebas requieren base terminada en _test")
os.environ["DATABASE_URL"] = test_url
os.environ["MIGRATION_DATABASE_URL"] = test_url
os.environ["APP_ENV"] = "test"
os.environ.update(
    {
        "PUBLIC_SIGNUP_ENABLED": "true",
        "EMAIL_MODE": "smtp",
        "SMTP_HOST": "127.0.0.1",
        "SMTP_PORT": "1025",
        "SMTP_TLS": "false",
        "SMTP_USER": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM": "no-reply@voluntia.test",
        "STORAGE_BACKEND": "local",
        "STORAGE_PATH": ".local/test-storage",
        "PUBLIC_BASE_URL": "http://localhost:4200",
    }
)
os.environ["JWT_SECRET"] = (
    "test-only-secret-64-characters-not-for-use-in-any-real-environment"
)


@pytest.fixture(scope="session")
def db_engine():
    command.upgrade(Config("backend/alembic.ini"), "head")
    from backend.app.db import engine

    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(db_engine):
    from backend.app.security.session import limiter

    limiter.hits.clear()
    with db_engine.begin() as c:
        names = (
            c.execute(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname='voluntia' AND tablename NOT IN ('rol','estado_inscripcion','categoria','habilidad')"
                )
            )
            .scalars()
            .all()
        )
        # Identificadores obtenidos del catálogo, nunca del cliente; base dedicada.
        c.exec_driver_sql(
            "TRUNCATE "
            + ",".join("voluntia." + n for n in names)
            + " RESTART IDENTITY CASCADE"
        )


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from backend.app.main import app

    with TestClient(
        app,
        base_url="http://localhost:4200",
        headers={"Origin": "http://localhost:4200"},
    ) as client:
        client.get("/api/v1/auth/csrf")
        yield client


def post(client, path, data=None, **kwargs):
    return client.post(
        "/api/v1" + path,
        json=data,
        headers={"x-csrf-token": client.cookies.get("voluntia_csrf", "")},
        **kwargs,
    )


@pytest.fixture
def scenario(db_engine):
    from backend.app.db import one, execute, actor_context

    with db_engine.begin() as c:
        actors = []
        for n in range(4):
            u = one(
                c,
                "INSERT INTO usuario(correo,clave_hash,email_verificado) VALUES(:correo,'hash-test',true) RETURNING id_usuario",
                correo=f"persona{n}@example.org",
            )["id_usuario"]
            actors.append(u)
            execute(
                c,
                "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre=:r",
                u=u,
                r="organizacion" if n == 0 else "voluntario",
            )
        org = one(
            c,
            "INSERT INTO organizacion(nombre,descripcion,correo_contacto,estado_verificacion) VALUES('Organización ficticia','Prueba','org@example.org','verificada') RETURNING id_organizacion",
        )["id_organizacion"]
        execute(
            c,
            "INSERT INTO organizacion_miembro(id_organizacion,id_usuario,cargo) VALUES(:o,:u,'administrador')",
            o=org,
            u=actors[0],
        )
        a = one(
            c,
            """INSERT INTO actividad(id_organizacion,id_categoria,titulo,descripcion,fecha_inicio,fecha_fin,fecha_cierre_inscripcion,cupo_maximo,modalidad,estado)
        VALUES(:o,1,'Actividad ficticia','Prueba',now()+interval '2 days',now()+interval '2 days 2 hours',now()+interval '1 day',1,'virtual','publicada') RETURNING id_actividad""",
            o=org,
        )["id_actividad"]
        ins = []
        for u in actors[1:]:
            v = one(
                c,
                "INSERT INTO voluntario(id_usuario,nombres,apellidos) VALUES(:u,'Persona','Ficticia') RETURNING id_voluntario",
                u=u,
            )["id_voluntario"]
            actor_context(c, u)
            ins.append(
                one(
                    c,
                    "INSERT INTO inscripcion(id_actividad,id_voluntario,id_estado,motivacion) VALUES(:a,:v,1,'Prueba') RETURNING id_inscripcion",
                    a=a,
                    v=v,
                )["id_inscripcion"]
            )
    return {
        "actor": actors[0],
        "usuarios": actors,
        "org": org,
        "actividad": a,
        "inscripciones": ins,
    }
