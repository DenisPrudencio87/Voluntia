import io
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from pypdf import PdfReader
from backend.app.db import one, execute
from backend.app.security.session import passwords
from backend.app.services.certificates import certificate_pdf
from backend.tests.conftest import post


def put(client, path, data):
    return client.put(
        "/api/v1" + path,
        json=data,
        headers={"x-csrf-token": client.cookies.get("voluntia_csrf", "")},
    )


def upload(client, path, content, mime="application/pdf", data=None):
    return client.post(
        "/api/v1" + path,
        files={"file": ("ficticio.pdf", content, mime)},
        data=data,
        headers={"x-csrf-token": client.cookies.get("voluntia_csrf", "")},
    )


@pytest.fixture
def accounts(db_engine):
    from backend.app.main import app

    result = {}
    # Provisionamiento únicamente en fixture de la base _test.
    with db_engine.begin() as c:
        for name, role in [
            ("admin", "administrador"),
            ("org", "voluntario"),
            ("vol", "voluntario"),
            ("other", "voluntario"),
        ]:
            u = one(
                c,
                "INSERT INTO usuario(correo,clave_hash,email_verificado) VALUES(:e,:h,true) RETURNING id_usuario",
                e=name + "@example.org",
                h=passwords.hash("FicticiaSegura-2026!"),
            )
            execute(
                c,
                "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre=:r",
                u=u["id_usuario"],
                r=role,
            )
            result[name + "_id"] = u["id_usuario"]
    for name in ("admin", "org", "vol", "other"):
        client = TestClient(
            app,
            base_url="http://localhost:4200",
            headers={"Origin": "http://localhost:4200"},
        )
        client.get("/api/v1/auth/csrf")
        assert (
            post(
                client,
                "/auth/login",
                {"correo": name + "@example.org", "clave": "FicticiaSegura-2026!"},
            ).status_code
            == 200
        )
        result[name] = client
    yield result
    for name in ("admin", "org", "vol", "other"):
        result[name].close()


def organization(accounts):
    res = post(
        accounts["org"],
        "/organization",
        {
            "nombre": "Manos de prueba",
            "descripcion": "Organización ficticia para pruebas locales",
            "correo_contacto": "org@example.org",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id_organizacion"]


def approve_org(accounts, org):
    pdf = certificate_pdf(
        "Documento ficticio",
        "Prueba",
        "Voluntia",
        1,
        "ficticio",
        datetime.now(timezone.utc),
    )
    doc = upload(
        accounts["org"],
        f"/organization/{org}/documents",
        pdf,
        data={"tipo_documento": "Constancia ficticia", "numero_documento": "DEMO-001"},
    )
    assert doc.status_code == 201, doc.text
    doc_id = doc.json()["id_documento"]
    assert (
        post(
            accounts["admin"],
            f"/admin/documents/{doc_id}/review",
            {"estado": "aprobado", "motivo": "Documento ficticio revisado"},
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["admin"],
            f"/admin/organizations/{org}/state",
            {"estado": "verificada", "motivo": "Revisión académica de prueba"},
        ).status_code
        == 200
    )
    return doc_id


def activity_data():
    now = datetime.now(timezone.utc)
    return {
        "id_categoria": 1,
        "titulo": "Jornada ambiental ficticia",
        "descripcion": "Actividad de prueba para demostrar todo el ciclo de participación.",
        "fecha_inicio": (now + timedelta(days=2)).isoformat(),
        "fecha_fin": (now + timedelta(days=2, hours=2)).isoformat(),
        "fecha_cierre_inscripcion": (now + timedelta(days=1)).isoformat(),
        "cupo_maximo": 1,
        "modalidad": "virtual",
        "habilidades": [
            {"id_habilidad": 3, "nivel_requerido": "basico", "obligatoria": True}
        ],
    }


def create_activity(accounts, org):
    res = post(accounts["org"], f"/organization/{org}/activities", activity_data())
    assert res.status_code == 201, res.text
    return res.json()["id_actividad"]


def profile(client, skills=True):
    result = put(
        client,
        "/volunteer/profile",
        {
            "nombres": "Persona",
            "apellidos": "Ficticia",
            "habilidades": [{"id_habilidad": 3, "nivel": "intermedio"}]
            if skills
            else [],
        },
    )
    assert result.status_code == 200, result.text


def test_complete_cycle_and_private_certificate(accounts, db_engine):
    org = organization(accounts)
    approve_org(accounts, org)
    activity = create_activity(accounts, org)
    assert accounts["vol"].get(f"/api/v1/activities/{activity}").status_code == 404
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{activity}/state",
            {"estado": "publicada"},
        ).status_code
        == 200
    )
    cat = accounts["vol"].get(
        "/api/v1/activities",
        params={
            "q": "ambiental",
            "categoria": 1,
            "modalidad": "virtual",
            "disponible": True,
        },
    )
    assert cat.status_code == 200, cat.text
    assert cat.json()["total"] == 1
    profile(accounts["vol"])
    res = post(
        accounts["vol"],
        f"/activities/{activity}/applications",
        {"motivacion": "Quiero colaborar en esta jornada ficticia."},
    )
    assert res.status_code == 201, res.text
    ins = res.json()["id_inscripcion"]
    assert (
        post(
            accounts["vol"],
            f"/activities/{activity}/applications",
            {"motivacion": "Otra solicitud que debe rechazarse."},
        ).status_code
        == 409
    )
    assert (
        post(
            accounts["org"], f"/applications/{ins}/state", {"estado": "aceptada"}
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["org"],
            f"/manage/applications/{ins}/certificate",
            {"acepta_visibilidad_publica": True},
        ).status_code
        == 409
    )
    # Reloj de fixture: simula el paso de días solo en la base descartable, sin bypass en API.
    start = datetime.now(timezone.utc) - timedelta(hours=3)
    end = start + timedelta(hours=2)
    with db_engine.begin() as c:
        execute(
            c,
            "UPDATE actividad SET fecha_cierre_inscripcion=:c,fecha_inicio=:s,fecha_fin=:e WHERE id_actividad=:a",
            c=start - timedelta(hours=1),
            s=start,
            e=end,
            a=activity,
        )
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{activity}/state",
            {"estado": "en_curso"},
        ).status_code
        == 200
    )
    assert (
        put(
            accounts["org"],
            f"/manage/applications/{ins}/attendance",
            {
                "estado": "asistio",
                "hora_entrada": start.isoformat(),
                "hora_salida": end.isoformat(),
            },
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{activity}/state",
            {"estado": "finalizada"},
        ).status_code
        == 200
    )
    impact = put(
        accounts["org"],
        f"/manage/activities/{activity}/impact",
        {
            "beneficiarios_estimados": 12,
            "descripcion_impacto": "Resultado social ficticio documentado.",
        },
    )
    assert impact.status_code == 200, impact.text
    assert float(impact.json()["horas_voluntariado"]) == 2
    cert = post(
        accounts["org"],
        f"/manage/applications/{ins}/certificate",
        {"acepta_visibilidad_publica": True},
    )
    assert cert.status_code == 201, cert.text
    cert = cert.json()
    repeated = post(
        accounts["org"],
        f"/manage/applications/{ins}/certificate",
        {"acepta_visibilidad_publica": True},
    )
    assert repeated.json()["id_certificado"] == cert["id_certificado"]
    public = accounts["other"].get(
        "/api/v1/certificates/" + cert["codigo_verificacion"]
    )
    assert (
        public.status_code == 200
        and "correo" not in public.json()
        and "archivo_url" not in public.json()
    )
    assert (
        accounts["other"]
        .get(f"/api/v1/certificates/private/{cert['id_certificado']}/file")
        .status_code
        == 404
    )
    pdf = accounts["vol"].get(
        f"/api/v1/certificates/private/{cert['id_certificado']}/file"
    )
    assert pdf.status_code == 200
    assert (
        "Persona Ficticia" in PdfReader(io.BytesIO(pdf.content)).pages[0].extract_text()
    )
    assert (
        put(
            accounts["org"],
            f"/manage/applications/{ins}/attendance",
            {"estado": "no_asistio"},
        ).status_code
        == 409
    )
    assert float(accounts["vol"].get("/api/v1/volunteer/profile").json()["horas"]) == 2
    history = (
        accounts["vol"].get(f"/api/v1/volunteer/applications/{ins}/history").json()
    )
    assert [h["estado"] for h in history] == ["pendiente", "aceptada", "finalizada"]


def test_pending_org_permissions_documents_skills_and_dates(accounts):
    org = organization(accounts)
    activity = create_activity(accounts, org)
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{activity}/state",
            {"estado": "publicada"},
        ).status_code
        == 409
    )
    assert (
        accounts["other"].get(f"/api/v1/manage/activities/{activity}").status_code
        == 404
    )
    assert accounts["vol"].get("/api/v1/admin/users").status_code == 403
    assert (
        post(
            accounts["admin"],
            f"/admin/organizations/{org}/state",
            {"estado": "verificada", "motivo": "Sin documentos aprobados"},
        ).status_code
        == 409
    )
    assert (
        upload(
            accounts["org"],
            f"/organization/{org}/documents",
            b"archivo falso",
            data={"tipo_documento": "Prueba", "numero_documento": "DEMO-002"},
        ).status_code
        == 422
    )
    doc = approve_org(accounts, org)
    assert (
        accounts["other"]
        .get(f"/api/v1/organization/{org}/documents/{doc}/file")
        .status_code
        == 404
    )
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{activity}/state",
            {"estado": "publicada"},
        ).status_code
        == 200
    )
    profile(accounts["vol"], skills=False)
    assert (
        post(
            accounts["vol"],
            f"/activities/{activity}/applications",
            {"motivacion": "Solicitud sin habilidades obligatorias."},
        ).status_code
        == 422
    )
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{activity}/state",
            {"estado": "en_curso"},
        ).status_code
        == 409
    )
    assert (
        put(
            accounts["org"],
            f"/organization/{org}/members",
            {"correo": "org@example.org", "cargo": "coordinador"},
        ).status_code
        == 409
    )
    assert (
        post(
            accounts["admin"],
            f"/admin/users/{accounts['admin_id']}/state",
            {"estado": "suspendido", "motivo": "Prueba del último administrador"},
        ).status_code
        == 409
    )


def test_waitlist_cancellation_and_promotion(accounts):
    org = organization(accounts)
    approve_org(accounts, org)
    a = create_activity(accounts, org)
    assert (
        post(
            accounts["org"], f"/manage/activities/{a}/state", {"estado": "publicada"}
        ).status_code
        == 200
    )
    profile(accounts["vol"])
    first = post(
        accounts["vol"],
        f"/activities/{a}/applications",
        {"motivacion": "Primera solicitud ficticia con motivación."},
    ).json()["id_inscripcion"]
    assert (
        post(
            accounts["org"], f"/applications/{first}/state", {"estado": "aceptada"}
        ).status_code
        == 200
    )
    profile(accounts["other"])
    second = post(
        accounts["other"],
        f"/activities/{a}/applications",
        {"motivacion": "Segunda solicitud ficticia con motivación."},
    )
    assert second.status_code == 201 and second.json()["estado"] == "espera"
    second = second.json()["id_inscripcion"]
    assert (
        post(
            accounts["org"], f"/applications/{second}/state", {"estado": "aceptada"}
        ).status_code
        == 409
    )
    assert (
        post(
            accounts["vol"], f"/applications/{first}/state", {"estado": "cancelada"}
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["org"], f"/applications/{second}/state", {"estado": "aceptada"}
        ).status_code
        == 200
    )
    assert (
        post(
            accounts["org"],
            f"/manage/activities/{a}/state",
            {"estado": "cancelada", "motivo": "Cancelación ficticia por seguridad"},
        ).status_code
        == 200
    )
    states = accounts["other"].get("/api/v1/volunteer/applications").json()
    assert states[0]["estado"] == "cancelada"
    assert (
        len(
            accounts["other"]
            .get(f"/api/v1/volunteer/applications/{second}/history")
            .json()
        )
        == 3
    )
