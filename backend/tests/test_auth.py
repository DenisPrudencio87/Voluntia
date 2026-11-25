import re
import httpx
from backend.tests.conftest import post
from backend.app.db import execute, one

PASSWORD = "PruebaSegura-2026!"
EMAIL = "voluntaria@example.org"


def mail_token(correo, subject):
    # Mailpit real, solo mensajes ficticios del entorno local/CI.
    messages = httpx.get("http://127.0.0.1:8025/api/v1/messages").json()["messages"]
    message = next(
        m
        for m in messages
        if any(t["Address"] == correo for t in m["To"]) and subject in m["Subject"]
    )
    content = httpx.get("http://127.0.0.1:8025/api/v1/message/" + message["ID"]).json()[
        "Text"
    ]
    return re.search(r"token=([A-Za-z0-9_-]+)", content).group(1)


def register_verify(client):
    assert (
        post(
            client,
            "/auth/register",
            {"correo": EMAIL, "clave": PASSWORD, "confirmacion": PASSWORD},
        ).status_code
        == 201
    )
    token = mail_token(EMAIL, "verifica")
    assert post(client, "/auth/verify", {"token": token}).status_code == 200
    return token


def login(client):
    return post(client, "/auth/login", {"correo": EMAIL, "clave": PASSWORD})


def test_mailpit_register_verify_login_reset_logout(client):
    token = register_verify(client)
    assert post(client, "/auth/verify", {"token": token}).status_code == 400
    assert login(client).status_code == 200
    assert client.cookies.get("voluntia_session")
    me = client.get("/api/v1/auth/me").json()
    assert me["email_verificado"] and me["roles"] == ["voluntario"]
    assert post(client, "/auth/forgot", {"correo": EMAIL}).status_code == 200
    token = mail_token(EMAIL, "recupera")
    new = "NuevaClaveSegura-2026!"
    assert (
        post(
            client, "/auth/reset", {"token": token, "clave": new, "confirmacion": new}
        ).status_code
        == 200
    )
    assert client.get("/api/v1/auth/me").status_code == 401
    assert login(client).status_code == 401
    assert (
        post(client, "/auth/login", {"correo": EMAIL, "clave": new}).status_code == 200
    )
    assert post(client, "/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_suspend_invalidates_existing_session(client, db_engine):
    register_verify(client)
    assert login(client).status_code == 200
    with db_engine.begin() as c:
        execute(c, "UPDATE usuario SET estado='suspendido' WHERE correo=:e", e=EMAIL)
    assert client.get("/api/v1/auth/me").status_code == 403


def test_csrf_origin_and_rate_limit(client):
    assert (
        client.post(
            "/api/v1/auth/login", json={"correo": EMAIL, "clave": "x"}
        ).status_code
        == 403
    )
    for _ in range(10):
        assert (
            post(
                client, "/auth/login", {"correo": EMAIL, "clave": "Incorrecta"}
            ).status_code
            == 401
        )
    assert (
        post(
            client, "/auth/login", {"correo": EMAIL, "clave": "Incorrecta"}
        ).status_code
        == 429
    )


def test_no_privileged_registration_or_password_mismatch(client):
    assert (
        post(
            client,
            "/auth/register",
            {
                "correo": EMAIL,
                "clave": PASSWORD,
                "confirmacion": PASSWORD,
                "rol": "administrador",
            },
        ).status_code
        == 422
    )
    assert (
        post(
            client,
            "/auth/register",
            {"correo": EMAIL, "clave": PASSWORD, "confirmacion": "OtraClaveSegura"},
        ).status_code
        == 422
    )


def test_smtp_failure_rolls_back_and_retry_available(client, db_engine, monkeypatch):
    from backend.app.config import settings

    monkeypatch.setattr(settings, "smtp_port", 1)
    assert (
        post(
            client,
            "/auth/register",
            {"correo": EMAIL, "clave": PASSWORD, "confirmacion": PASSWORD},
        ).status_code
        == 503
    )
    with db_engine.connect() as c:
        assert one(c, "SELECT count(*) n FROM usuario")["n"] == 0
    monkeypatch.setattr(settings, "smtp_port", 1025)
    register_verify(client)


def test_demo_closed_without_email(client, monkeypatch):
    from backend.app.config import settings

    monkeypatch.setattr(settings, "public_signup_enabled", False)
    assert (
        post(
            client,
            "/auth/register",
            {"correo": EMAIL, "clave": PASSWORD, "confirmacion": PASSWORD},
        ).status_code
        == 403
    )
    assert post(client, "/auth/forgot", {"correo": EMAIL}).status_code == 403
