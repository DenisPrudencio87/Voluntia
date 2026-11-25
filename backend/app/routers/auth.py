from fastapi import APIRouter, Depends, HTTPException, Request, Response
from backend.app.config import settings
from backend.app.db import transaction, one, execute
from backend.app.schemas.auth import (
    Login,
    Register,
    EmailInput,
    TokenInput,
    ResetPassword,
    ChangePassword,
)
from backend.app.security.session import (
    current_user,
    limiter,
    set_csrf,
    set_session,
    passwords,
    verify_password,
    dummy_hash,
)
from backend.app.services.accounts import issue_token, consume_token, update_password

router = APIRouter(prefix="/auth", tags=["Cuenta"])


def signup_allowed():
    if not settings.public_signup_enabled:
        raise HTTPException(
            403, "Registro y recuperación por correo cerrados en esta demostración"
        )


@router.get("/csrf")
def csrf(response: Response):
    set_csrf(response)
    return {
        "public_signup_enabled": settings.public_signup_enabled,
        "email_enabled": settings.email_mode == "smtp",
        "app_env": settings.app_env,
    }


@router.post("/register", status_code=201)
def register(
    data: Register, request: Request, c=Depends(transaction, scope="function")
):
    signup_allowed()
    limiter.check(request, "register", str(data.correo), limit=5, window=300)
    # Respuesta uniforme también para correos ya existentes.
    existing = one(
        c, "SELECT id_usuario FROM usuario WHERE correo=:e", e=str(data.correo).lower()
    )
    if not existing:
        user = one(
            c,
            "INSERT INTO usuario(correo,clave_hash) VALUES(:e,:h) RETURNING *",
            e=str(data.correo).lower(),
            h=passwords.hash(data.clave),
        )
        execute(
            c,
            "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre='voluntario'",
            u=user["id_usuario"],
        )
        issue_token(c, user, "verificar_email")
    return {
        "mensaje": "Si el correo puede registrarse, recibirás un enlace de verificación."
    }


@router.post("/login")
def login(
    data: Login,
    request: Request,
    response: Response,
    c=Depends(transaction, scope="function"),
):
    limiter.check(request, "login", str(data.correo), limit=10, window=300, ip_limit=50)
    user = one(c, "SELECT * FROM usuario WHERE correo=:e", e=str(data.correo).lower())
    valid = verify_password(user["clave_hash"] if user else dummy_hash, data.clave)
    if not user or not valid or user["estado"] != "activo":
        raise HTTPException(401, "Correo o contraseña incorrectos")
    execute(
        c,
        "UPDATE usuario SET ultimo_acceso=now() WHERE id_usuario=:u",
        u=user["id_usuario"],
    )
    set_session(response, user)
    return {"mensaje": "Sesión iniciada"}


@router.get("/me")
def me(user=Depends(current_user, scope="function")):
    return user


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    c=Depends(transaction, scope="function"),
):
    # Limpiar cookies también si la sesión ya venció; una sesión válida se revoca.
    try:
        user = current_user(request, c)
    except HTTPException as error:
        if error.status_code not in (401, 403):
            raise
    else:
        execute(
            c,
            "UPDATE usuario SET fecha_actualizacion=clock_timestamp() WHERE id_usuario=:u",
            u=user["id_usuario"],
        )
    response.delete_cookie("voluntia_session", path="/")
    response.delete_cookie("voluntia_csrf", path="/")
    return {"mensaje": "Sesión cerrada"}


@router.post("/verify")
def verify(
    data: TokenInput, request: Request, c=Depends(transaction, scope="function")
):
    limiter.check(request, "verify", limit=10)
    user = consume_token(c, data.token, "verificar_email")
    execute(
        c,
        "UPDATE usuario SET email_verificado=true WHERE id_usuario=:u",
        u=user["id_usuario"],
    )
    return {"mensaje": "Correo verificado. Ya puedes iniciar sesión."}


@router.post("/resend")
def resend(
    data: EmailInput, request: Request, c=Depends(transaction, scope="function")
):
    signup_allowed()
    limiter.check(request, "resend", str(data.correo), limit=3, window=300)
    user = one(
        c,
        "SELECT * FROM usuario WHERE correo=:e AND NOT email_verificado AND estado='activo' FOR UPDATE",
        e=str(data.correo).lower(),
    )
    if user:
        issue_token(c, user, "verificar_email")
    return {"mensaje": "Si corresponde, recibirás un nuevo enlace."}


@router.post("/forgot")
def forgot(
    data: EmailInput, request: Request, c=Depends(transaction, scope="function")
):
    signup_allowed()
    limiter.check(request, "forgot", str(data.correo), limit=3, window=300)
    user = one(
        c,
        "SELECT * FROM usuario WHERE correo=:e AND email_verificado AND estado='activo' FOR UPDATE",
        e=str(data.correo).lower(),
    )
    if user:
        issue_token(c, user, "recuperar_password")
    return {"mensaje": "Si corresponde, recibirás un enlace de recuperación."}


@router.post("/reset")
def reset(
    data: ResetPassword, request: Request, c=Depends(transaction, scope="function")
):
    signup_allowed()
    limiter.check(request, "reset", limit=10)
    user = consume_token(c, data.token, "recuperar_password")
    update_password(c, user["id_usuario"], data.clave)
    return {"mensaje": "Contraseña actualizada. Las sesiones anteriores caducaron."}


@router.post("/password")
def change_password(
    data: ChangePassword,
    c=Depends(transaction, scope="function"),
    user=Depends(current_user, scope="function"),
):
    stored = one(
        c,
        "SELECT clave_hash FROM usuario WHERE id_usuario=:u FOR UPDATE",
        u=user["id_usuario"],
    )
    if not verify_password(stored["clave_hash"], data.clave_actual):
        raise HTTPException(400, "La contraseña actual no es correcta")
    update_password(c, user["id_usuario"], data.clave)
    return {"mensaje": "Contraseña actualizada. Inicia sesión de nuevo."}
