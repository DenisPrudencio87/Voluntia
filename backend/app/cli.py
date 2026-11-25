"""Provisionamiento por consola local; ninguna ruta web crea administradores."""

import argparse
import getpass
from sqlalchemy.engine import make_url
from backend.app.config import settings
from backend.app.db import engine, one, execute, actor_context
from backend.app.security.session import passwords
from email_validator import validate_email


def main():
    parser = argparse.ArgumentParser(
        description="Voluntia: crear cuenta desde consola protegida"
    )
    parser.add_argument("command", choices=["create-user"])
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--role", choices=["administrador", "voluntario"], required=True
    )
    parser.add_argument(
        "--fictional-demo",
        action="store_true",
        help="Preactivar exclusivamente una cuenta ficticia en modo local/demo",
    )
    parser.add_argument("--allow-remote", action="store_true")
    args = parser.parse_args()
    target = make_url(settings.database_url)
    if target.host not in ("localhost", "127.0.0.1", "db") and not args.allow_remote:
        raise SystemExit(
            "Destino remoto bloqueado; requiere autorización específica y --allow-remote"
        )
    if args.fictional_demo and settings.app_env not in ("local", "demo", "test"):
        raise SystemExit("No se permite preactivar cuentas ficticias en producción")
    email = validate_email(args.email, check_deliverability=False).normalized.lower()
    if args.fictional_demo and not email.endswith("@example.org"):
        raise SystemExit(
            "La cuenta ficticia debe usar el dominio reservado example.org"
        )
    password = getpass.getpass("Contraseña privada (12 a 128 caracteres): ")
    confirmation = getpass.getpass("Repetir contraseña: ")
    if password != confirmation or not 12 <= len(password) <= 128:
        raise SystemExit("Contraseña inválida o confirmación distinta")
    with engine.begin() as c:
        if one(c, "SELECT id_usuario FROM usuario WHERE correo=:e", e=email):
            raise SystemExit("La cuenta ya existe; no se modificó")
        user = one(
            c,
            "INSERT INTO usuario(correo,clave_hash,email_verificado) VALUES(:e,:h,:v) RETURNING id_usuario",
            e=email,
            h=passwords.hash(password),
            v=args.fictional_demo,
        )
        execute(
            c,
            "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre=:r",
            u=user["id_usuario"],
            r=args.role,
        )
        actor_context(c, user["id_usuario"])
        execute(
            c,
            "INSERT INTO bitacora_evento(id_usuario,accion,entidad,id_registro,detalle) VALUES(:u,'cuenta_provisionada','usuario',:u,:d)",
            u=user["id_usuario"],
            d="Cuenta ficticia preactivada sin comprobación real de correo"
            if args.fictional_demo
            else "Cuenta por consola, verificación de correo pendiente",
        )
    print("Cuenta creada. No se muestra ni guarda la contraseña clara.")


if __name__ == "__main__":
    main()
