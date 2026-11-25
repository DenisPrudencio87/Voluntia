from pathlib import Path
import pytest
from sqlalchemy.exc import DBAPIError
from backend.app.db import one, execute, actor_context
from backend.app.config import Settings
from backend.tests.conftest import post
from backend.tests.test_domain import (
    organization,
    approve_org,
    create_activity,
    profile,
)
from backend.tests.test_domain import accounts as accounts


def test_runtime_permissions_and_acceptance(db_engine, scenario):
    with db_engine.begin() as c:
        execute(
            c,
            "DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='voluntia_test_runtime') THEN CREATE ROLE voluntia_test_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE; END IF; END $$",
        )
        sql = (
            Path("database/permissions.sql")
            .read_text(encoding="utf-8")
            .replace("voluntia_runtime", "voluntia_test_runtime")
        )
        with c.connection.driver_connection.cursor() as cursor:
            cursor.execute(sql, prepare=False)
    with db_engine.begin() as c:
        execute(c, "SET LOCAL ROLE voluntia_test_runtime")
        actor_context(c, scenario["actor"])
        execute(
            c,
            "SELECT fn_aceptar_inscripcion(:i,:u)",
            i=scenario["inscripciones"][0],
            u=scenario["actor"],
        )
        assert (
            one(c, "SELECT fn_cupos_disponibles(:a) n", a=scenario["actividad"])["n"]
            == 0
        )
    for statement in (
        "CREATE TABLE voluntia.ilegal(id int)",
        "UPDATE historial_inscripcion SET comentario='alterar'",
        "DELETE FROM usuario",
    ):
        with pytest.raises(DBAPIError), db_engine.begin() as c:
            execute(c, "SET LOCAL ROLE voluntia_test_runtime")
            execute(c, statement)


def test_production_settings_fail_closed():
    with pytest.raises(ValueError):
        Settings(_env_file=None, jwt_secret="short")
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            jwt_secret="x" * 64,
            email_mode="disabled",
            public_signup_enabled=True,
        )
    with pytest.raises(ValueError):
        Settings(_env_file=None, jwt_secret="x" * 64, app_env="production")


def test_unknown_api_never_spa_and_missing_certificate(client):
    assert client.get("/api/v1/inexistente").status_code == 404
    assert client.get("/api/v1/certificates/invalido").status_code == 404
    assert client.get("/api/ready").status_code == 200
    assert client.get("/api/v1/admin/users").status_code == 401


def test_document_resubmission_requires_new_review(accounts):
    from backend.tests.test_domain import upload
    from backend.app.services.certificates import certificate_pdf
    from datetime import datetime, timezone

    org = organization(accounts)
    approve_org(accounts, org)
    pdf = certificate_pdf(
        "Ficticio", "Nueva constancia", "Prueba", 1, "test", datetime.now(timezone.utc)
    )
    result = upload(
        accounts["org"],
        f"/organization/{org}/documents",
        pdf,
        data={"tipo_documento": "Nueva constancia", "numero_documento": "DEMO-003"},
    )
    assert result.status_code == 201
    assert (
        accounts["org"].get(f"/api/v1/organization/{org}").json()["estado_verificacion"]
        == "pendiente"
    )


def test_suspension_hides_public_activity_and_blocks_member(accounts):
    org = organization(accounts)
    approve_org(accounts, org)
    a = create_activity(accounts, org)
    assert (
        post(
            accounts["org"], f"/manage/activities/{a}/state", {"estado": "publicada"}
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["admin"],
            f"/admin/organizations/{org}/state",
            {"estado": "suspendida", "motivo": "Suspensión de prueba"},
        ).status_code
        == 200
    )
    assert accounts["vol"].get(f"/api/v1/activities/{a}").status_code == 404
    assert (
        post(
            accounts["org"], f"/manage/activities/{a}/state", {"estado": "cerrada"}
        ).status_code
        == 403
    )
    assert (
        post(
            accounts["admin"],
            f"/admin/organizations/{org}/state",
            {"estado": "verificada", "motivo": "Restauración con documento revisado"},
        ).status_code
        == 200
    )
    assert (
        accounts["vol"].get(f"/api/v1/activities/{a}").json()["estado"] == "publicada"
    )


def test_past_closed_cancelled_activity_rejects_applications(accounts, db_engine):
    org = organization(accounts)
    approve_org(accounts, org)
    a = create_activity(accounts, org)
    profile(accounts["vol"])
    assert (
        post(
            accounts["org"], f"/manage/activities/{a}/state", {"estado": "publicada"}
        ).status_code
        == 200
    )
    with db_engine.begin() as c:
        execute(
            c,
            "UPDATE actividad SET fecha_cierre_inscripcion=now()-interval '1 hour' WHERE id_actividad=:a",
            a=a,
        )
    assert (
        post(
            accounts["vol"],
            f"/activities/{a}/applications",
            {"motivacion": "Prueba de inscripción fuera de plazo"},
        ).status_code
        == 409
    )
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{a}/state",
            {"estado": "cancelada", "motivo": "Cancelación de prueba"},
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["vol"],
            f"/activities/{a}/applications",
            {"motivacion": "Prueba de inscripción cancelada"},
        ).status_code
        == 409
    )
