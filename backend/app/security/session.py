import hashlib
import hmac
import secrets
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request
from backend.app.config import settings
from backend.app.db import transaction, one, rows, actor_context

passwords = PasswordHasher()
dummy_hash = passwords.hash(secrets.token_urlsafe(32))
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def verify_password(stored, password):
    try:
        return passwords.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False


def csrf_token():
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(
        settings.jwt_secret.encode(), nonce.encode(), hashlib.sha256
    ).hexdigest()
    return nonce + "." + signature


def valid_csrf(token):
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}\.[a-f0-9]{64}", token):
        return False
    nonce, _, signature = token.partition(".")
    expected = hmac.new(
        settings.jwt_secret.encode(), nonce.encode(), hashlib.sha256
    ).hexdigest()
    return bool(nonce) and hmac.compare_digest(signature, expected)


def set_csrf(response):
    token = csrf_token()
    response.set_cookie(
        "voluntia_csrf",
        token,
        secure=settings.app_env in ("demo", "production"),
        samesite="lax",
        max_age=1800,
        path="/",
    )
    return token


def set_session(response, user):
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user["id_usuario"]),
            "ver": user["fecha_actualizacion"].isoformat(),
            "iat": now,
            "exp": now + timedelta(minutes=30),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    response.set_cookie(
        "voluntia_session",
        token,
        httponly=True,
        secure=settings.app_env in ("demo", "production"),
        samesite="lax",
        max_age=1800,
        path="/",
    )
    set_csrf(response)


def current_user(request: Request, c=Depends(transaction, scope="function")):
    try:
        claims = jwt.decode(
            request.cookies.get("voluntia_session", ""),
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub", "ver"]},
        )
        user = one(
            c,
            "SELECT id_usuario,correo,email_verificado,estado,fecha_actualizacion FROM usuario WHERE id_usuario=:u",
            u=int(claims["sub"]),
        )
        if not user or user["fecha_actualizacion"].isoformat() != claims["ver"]:
            raise ValueError()
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(401, "Inicia sesión para continuar") from None
    if user["estado"] != "activo":
        raise HTTPException(403, "Cuenta suspendida")
    user = dict(user)
    user["roles"] = [
        r["nombre"]
        for r in rows(
            c,
            "SELECT r.nombre FROM usuario_rol ur JOIN rol r USING(id_rol) WHERE ur.id_usuario=:u AND ur.activo",
            u=user["id_usuario"],
        )
    ]
    actor_context(c, user["id_usuario"])
    return user


def verified_user(user=Depends(current_user, scope="function")):
    if not user["email_verificado"]:
        raise HTTPException(403, "Verifica tu correo antes de continuar")
    return user


def admin_user(user=Depends(verified_user, scope="function")):
    if "administrador" not in user["roles"]:
        raise HTTPException(403, "Acceso reservado a administración")
    return user


class RateLimiter:
    """Un worker. Al escalar, sustituir por almacén compartido, nunca aumentar workers sin ello."""

    def __init__(self):
        self.hits = defaultdict(deque)
        self.lock = Lock()

    def check(self, request, action, account="", limit=10, window=60, ip_limit=None):
        now = monotonic()
        ip = request.client.host if request.client else "unknown"
        with self.lock:
            for identity in (
                ("ip:" + ip, "account:" + account.lower()) if account else ("ip:" + ip,)
            ):
                key = action + ":" + hashlib.sha256(identity.encode()).hexdigest()
                q = self.hits[key]
                while q and q[0] <= now - window:
                    q.popleft()
                threshold = (
                    ip_limit if identity.startswith("ip:") and ip_limit else limit
                )
                if len(q) >= threshold:
                    raise HTTPException(
                        429,
                        "Demasiados intentos. Intenta más tarde.",
                        headers={"Retry-After": str(window)},
                    )
                q.append(now)
            if len(self.hits) > 10000:
                self.hits = {
                    k: v for k, v in self.hits.items() if v and v[-1] > now - 3600
                }
                self.hits = defaultdict(deque, self.hits)


limiter = RateLimiter()
