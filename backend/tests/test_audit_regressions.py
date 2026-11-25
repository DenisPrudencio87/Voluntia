"""Casos derivados de auditoría independiente del recorrido feliz original."""

import io
import time
from datetime import datetime, timezone
from pathlib import Path
import pytest
from fastapi import HTTPException
from PIL import Image
from pypdf import PdfWriter, PdfReader
from pypdf.generic import NameObject, DictionaryObject, TextStringObject
from sqlalchemy.exc import DBAPIError
from backend.app.db import execute, one, actor_context
from backend.app.services.storage import validate_file, put_object
from backend.app.services.certificates import certificate_pdf
from backend.tests.conftest import post
from backend.tests.test_domain import accounts as accounts
from backend.tests.test_domain import organization, create_activity, upload, put


def test_document_rejection_reason_reaches_owner(accounts):
    org = organization(accounts)
    pdf = certificate_pdf(
        "Ficticio", "Constancia", "Prueba", 1, "audit", datetime.now(timezone.utc)
    )
    d = upload(
        accounts["org"],
        f"/organization/{org}/documents",
        pdf,
        data={"tipo_documento": "Constancia", "numero_documento": "AUDIT-001"},
    ).json()["id_documento"]
    reason = "Falta la segunda página de la constancia ficticia"
    assert (
        post(
            accounts["admin"],
            f"/admin/documents/{d}/review",
            {"estado": "rechazado", "motivo": reason},
        ).status_code
        == 200
    )
    result = accounts["org"].get(f"/api/v1/organization/{org}").json()
    assert any(reason in r["detalle"] for r in result["revisiones"])


def test_deactivating_member_does_not_regrant_global_role(accounts):
    org = organization(accounts)
    member = {"correo": "other@example.org", "cargo": "coordinador", "estado": "activo"}
    assert (
        put(accounts["org"], f"/organization/{org}/members", member).status_code == 200
    )
    assert (
        post(
            accounts["admin"],
            f"/admin/users/{accounts['other_id']}/roles",
            {
                "roles": ["voluntario"],
                "motivo": "Revocación explícita de permisos organizativos",
            },
        ).status_code
        == 200
    )
    assert (
        put(
            accounts["org"],
            f"/organization/{org}/members",
            {**member, "estado": "inactivo"},
        ).status_code
        == 200
    )
    post(
        accounts["other"],
        "/auth/login",
        {"correo": "other@example.org", "clave": "FicticiaSegura-2026!"},
    )
    assert accounts["other"].get("/api/v1/auth/me").json()["roles"] == ["voluntario"]


def test_new_organization_does_not_restore_revoked_old_membership(accounts):
    org = organization(accounts)
    activity = create_activity(accounts, org)
    assert (
        put(
            accounts["org"],
            f"/organization/{org}/members",
            {"correo": "other@example.org", "cargo": "coordinador", "estado": "activo"},
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["admin"],
            f"/admin/users/{accounts['other_id']}/roles",
            {
                "roles": ["voluntario"],
                "motivo": "Revocación explícita de permisos organizativos",
            },
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["other"],
            "/auth/login",
            {"correo": "other@example.org", "clave": "FicticiaSegura-2026!"},
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["other"],
            "/organization",
            {
                "nombre": "Nueva organización ficticia",
                "descripcion": "Organización distinta de auditoría",
                "correo_contacto": "other@example.org",
            },
        ).status_code
        == 201
    )
    assert accounts["other"].get(
        f"/api/v1/manage/activities/{activity}"
    ).status_code in (403, 404)


def test_expired_session_can_be_logged_out(client):
    client.cookies.set("voluntia_session", "expired-or-invalid")
    response = post(client, "/auth/logout")
    assert response.status_code == 200
    assert any(
        'voluntia_session=""' in v or "voluntia_session=;" in v
        for v in response.headers.get_list("set-cookie")
    )


def test_non_ascii_csrf_fails_closed():
    from backend.app.security.session import valid_csrf

    assert not valid_csrf("nonce.\u00f1")


def test_sql_acceptance_requires_active_organization_role(db_engine, scenario):
    with pytest.raises(DBAPIError), db_engine.begin() as c:
        execute(
            c,
            "UPDATE usuario_rol SET activo=false WHERE id_usuario=:u",
            u=scenario["actor"],
        )
        actor_context(c, scenario["actor"])
        execute(
            c,
            "SELECT fn_aceptar_inscripcion(:i,:u)",
            i=scenario["inscripciones"][0],
            u=scenario["actor"],
        )


def test_sql_acceptance_uses_current_clock_after_transaction_begins(
    db_engine, scenario
):
    with pytest.raises(DBAPIError), db_engine.begin() as c:
        actor_context(c, scenario["actor"])
        execute(
            c,
            "UPDATE actividad SET fecha_inicio=clock_timestamp()+interval '0.2 seconds',fecha_fin=clock_timestamp()+interval '1 hour',fecha_cierre_inscripcion=clock_timestamp()-interval '1 hour' WHERE id_actividad=:a",
            a=scenario["actividad"],
        )
        time.sleep(0.3)
        execute(
            c,
            "SELECT fn_aceptar_inscripcion(:i,:u)",
            i=scenario["inscripciones"][0],
            u=scenario["actor"],
        )


def test_image_mime_must_match_allowed_signature():
    content = io.BytesIO()
    Image.new("RGB", (10, 10), "green").save(content, format="GIF")
    with pytest.raises(HTTPException) as failure:
        validate_file(content.getvalue(), "image/jpeg")
    assert failure.value.status_code == 422


def test_pdf_escaped_active_names_rejected():
    class EncodedName(NameObject):
        def write_to_stream(self, stream, *args, **kwargs):
            stream.write(
                {
                    "/OpenAction": b"/O#70enAction",
                    "/JavaScript": b"/J#61vaScript",
                    "/JS": b"/J#53",
                }[str(self)]
            )

    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.root_object[EncodedName("/OpenAction")] = DictionaryObject(
        {
            NameObject("/S"): EncodedName("/JavaScript"),
            EncodedName("/JS"): TextStringObject('app.alert("ficticio")'),
        }
    )
    output = io.BytesIO()
    writer.write(output)
    content = output.getvalue()
    assert "/OpenAction" in PdfReader(io.BytesIO(content), strict=True).trailer["/Root"]
    with pytest.raises(HTTPException) as failure:
        validate_file(content, "application/pdf", only_pdf=True)
    assert failure.value.status_code == 422


def test_storage_disk_failure_is_controlled(monkeypatch):
    def disk_full(*args, **kwargs):
        raise OSError("falla ficticia de disco")

    monkeypatch.setattr(Path, "write_bytes", disk_full)
    with pytest.raises(HTTPException) as failure:
        put_object(b"ficticio", "documents", 1, "pdf", "application/pdf")
    assert failure.value.status_code == 503


def test_chunked_body_limit_counts_actual_bytes():
    import asyncio
    from backend.app.security.body_limit import BodyLimitMiddleware

    async def scenario():
        called = False
        messages = iter(
            [
                {"type": "http.request", "body": b"1234", "more_body": True},
                {"type": "http.request", "body": b"5678", "more_body": False},
            ]
        )
        output = []

        async def receive():
            return next(messages)

        async def send(message):
            output.append(message)

        async def inner(*args):
            nonlocal called
            called = True

        await BodyLimitMiddleware(inner, max_bytes=7)(
            {"type": "http", "method": "POST"}, receive, send
        )
        assert not called
        assert output[0]["status"] == 413

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "changes",
    [
        {"database_url": "postgresql+psycopg://u:p@remote.invalid/db"},
        {"migration_database_url": "postgresql+psycopg://u:p@remote.invalid/db"},
        {
            "database_url": "postgresql+psycopg://u:p@aws.example.pooler.supabase.com:6543/db?sslmode=require"
        },
        {"public_base_url": "https://user:password@example.org"},
        {"public_base_url": "https://example.org/unexpected-path"},
        {
            "storage_backend": "supabase",
            "supabase_url": "https://example.org/path",
            "supabase_service_role_key": "ficticia",
        },
    ],
)
def test_invalid_remote_settings_fail_before_connecting(changes):
    from backend.app.config import Settings

    with pytest.raises(ValueError):
        Settings(_env_file=None, jwt_secret="x" * 64, **changes)


def test_settings_repr_does_not_expose_credentials():
    from backend.app.config import Settings

    config = Settings(
        _env_file=None,
        jwt_secret="private-marker" * 4,
        smtp_password="smtp-private-marker",
        supabase_service_role_key="storage-private-marker",
    )
    assert "private-marker" not in repr(config)
    assert "voluntia_local" not in repr(config)


def test_search_path_survives_connection_rollback(db_engine):
    for _ in range(3):
        with db_engine.connect() as c:
            assert one(c, "SELECT count(*) n FROM rol")["n"] == 3
            c.rollback()
            assert one(c, "SELECT current_schema() s")["s"] == "voluntia"


def test_readiness_rejects_outdated_revision(client, db_engine):
    from backend.app.main import REQUIRED_REVISION

    with db_engine.begin() as c:
        execute(c, "UPDATE public.alembic_version SET version_num='0002'")
    try:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/ready").status_code == 503
    finally:
        with db_engine.begin() as c:
            execute(
                c,
                "UPDATE public.alembic_version SET version_num=:v",
                v=REQUIRED_REVISION,
            )
    assert client.get("/api/ready").status_code == 200


def test_acceptance_rejects_retired_volunteer_role(db_engine, scenario):
    with pytest.raises(DBAPIError), db_engine.begin() as c:
        execute(
            c,
            "UPDATE usuario_rol SET activo=false WHERE id_usuario=:u",
            u=scenario["usuarios"][1],
        )
        actor_context(c, scenario["actor"])
        execute(
            c,
            "SELECT fn_aceptar_inscripcion(:i,:u)",
            i=scenario["inscripciones"][0],
            u=scenario["actor"],
        )


def test_supabase_secret_key_is_not_sent_as_bearer(monkeypatch):
    from backend.app.config import settings
    from backend.app.services.storage import headers

    monkeypatch.setattr(settings, "supabase_service_role_key", "sb_secret_ficticia")
    assert headers() == {"apikey": "sb_secret_ficticia"}
    monkeypatch.setattr(settings, "supabase_service_role_key", "legacy-jwt-ficticio")
    assert headers()["Authorization"] == "Bearer legacy-jwt-ficticio"


def test_tiny_attendance_rejected_before_upload(db_engine, scenario, monkeypatch):
    import backend.app.routers.participation as participation
    from backend.app.schemas.domain import CertificateConsent

    def unexpected_upload(*args, **kwargs):
        pytest.fail(
            "No se debe subir un archivo que la base rechazará por horas redondeadas a cero"
        )

    monkeypatch.setattr(participation, "put_object", unexpected_upload)
    with db_engine.begin() as c:
        actor_context(c, scenario["actor"])
        execute(
            c,
            "SELECT fn_aceptar_inscripcion(:i,:u)",
            i=scenario["inscripciones"][0],
            u=scenario["actor"],
        )
        execute(
            c,
            "UPDATE actividad SET fecha_inicio=now()-interval '2 hours',fecha_fin=now()-interval '1 hour',fecha_cierre_inscripcion=now()-interval '3 hours',estado='finalizada' WHERE id_actividad=:a",
            a=scenario["actividad"],
        )
        execute(
            c,
            "INSERT INTO asistencia(id_inscripcion,estado,hora_entrada,hora_salida) VALUES(:i,'asistio',now()-interval '2 hours',now()-interval '2 hours'+interval '2 seconds')",
            i=scenario["inscripciones"][0],
        )
        with pytest.raises(HTTPException) as error:
            participation.issue_certificate(
                scenario["inscripciones"][0],
                CertificateConsent(acepta_visibilidad_publica=True),
                c,
                {"id_usuario": scenario["actor"], "roles": ["organizacion"]},
            )
        assert error.value.status_code == 409


def test_login_limit_separates_account_and_shared_ip():
    from starlette.requests import Request
    from backend.app.security.session import RateLimiter

    limiter = RateLimiter()
    request = Request({"type": "http", "client": ("127.0.0.1", 1234)})
    for account in ("cuenta1@example.org", "cuenta2@example.org"):
        for _ in range(10):
            limiter.check(request, "login", account, limit=10, window=300, ip_limit=50)
    with pytest.raises(HTTPException) as error:
        limiter.check(
            request, "login", "cuenta1@example.org", limit=10, window=300, ip_limit=50
        )
    assert error.value.status_code == 429


def test_access_log_redacts_query_tokens_without_hiding_status():
    import logging
    from backend.app.security.logging import RedactAccessQuery

    record = logging.LogRecord(
        "uvicorn.access",
        logging.INFO,
        "",
        0,
        '%s - "%s %s HTTP/%s" %d',
        ("127.0.0.1", "GET", "/verificar?token=private-fictitious-token", "1.1", 200),
        None,
    )
    assert RedactAccessQuery().filter(record)
    assert "private-fictitious-token" not in record.getMessage()
    assert "/verificar" in record.getMessage() and "200" in record.getMessage()
