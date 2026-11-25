"""Datos ficticios SOLO para Playwright: base *_test, local o CI, sin limpieza."""

import json
import os
import secrets
from pathlib import Path
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine
from backend.app.security.session import passwords
from backend.app.db import actor_context, one, execute


def seed(url, output, rotate=False):
    parsed = make_url(url)
    if not parsed.database.endswith("_test") or parsed.host not in (
        "127.0.0.1",
        "localhost",
        "postgres",
    ):
        raise RuntimeError("Seed E2E limitado a PostgreSQL local dedicado *_test")
    engine = create_engine(
        url, connect_args={"options": "-csearch_path=voluntia,public"}
    )
    credentials = {}
    with engine.begin() as c:
        for name, role in [
            ("admin", "administrador"),
            ("org", "voluntario"),
            ("vol", "voluntario"),
        ]:
            email = "e2e-" + name + "@example.org"
            existing = one(c, "SELECT id_usuario FROM usuario WHERE correo=:e", e=email)
            if existing and not rotate:
                raise RuntimeError(
                    "Las cuentas E2E ya existen. Usar otra base _test vacía."
                )
            password = secrets.token_urlsafe(24)
            if existing:
                user = one(
                    c,
                    "UPDATE usuario SET clave_hash=:h,fecha_actualizacion=clock_timestamp() WHERE id_usuario=:u RETURNING id_usuario",
                    h=passwords.hash(password),
                    u=existing["id_usuario"],
                )
            else:
                user = one(
                    c,
                    "INSERT INTO usuario(correo,clave_hash,email_verificado) VALUES(:e,:h,true) RETURNING id_usuario",
                    e=email,
                    h=passwords.hash(password),
                )
            execute(
                c,
                "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre=:r ON CONFLICT DO NOTHING",
                u=user["id_usuario"],
                r=role,
            )
            credentials[name] = {
                "email": email,
                "password": password,
                "id": user["id_usuario"],
            }
        actor_context(c, credentials["admin"]["id"])
        execute(
            c,
            "INSERT INTO bitacora_evento(id_usuario,accion,entidad,detalle) VALUES(:u,'provisionamiento_fixture','usuario','Cuentas ficticias E2E sin comprobación real de correo')",
            u=credentials["admin"]["id"],
        )
    engine.dispose()
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(credentials), encoding="utf-8")
    print("Cuentas E2E creadas. Archivo privado ignorado; no publicar.")


if __name__ == "__main__":
    import sys

    seed(
        os.environ["TEST_DATABASE_URL"],
        ".local/e2e-credentials.json",
        rotate="--rotate" in sys.argv,
    )
