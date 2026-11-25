import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from backend.app.db import transaction, one, rows
from backend.app.security.session import verified_user
from backend.app.schemas.domain import Attendance, Impact, CertificateConsent
from backend.app.services.domain import owned_activity, require, audit, notify
from backend.app.services.storage import put_object, validate_file, download
from backend.app.services.certificates import certificate_pdf

router = APIRouter(tags=["Asistencia, impacto y certificados"])


def manage_inscription(c, user, ins_id):
    i = require(one(c, "SELECT * FROM inscripcion WHERE id_inscripcion=:i", i=ins_id))
    a = owned_activity(c, user, i["id_actividad"])
    require(
        one(
            c,
            "SELECT id_inscripcion FROM inscripcion WHERE id_inscripcion=:i FOR UPDATE",
            i=ins_id,
        )
    )
    return i, a


@router.put("/manage/applications/{ins_id}/attendance")
def attendance(
    ins_id: int,
    data: Attendance,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    i, a = manage_inscription(c, user, ins_id)
    row = one(
        c,
        """INSERT INTO asistencia(id_inscripcion,estado,hora_entrada,hora_salida,observacion)
    VALUES(:i,:estado,:hora_entrada,:hora_salida,:observacion) ON CONFLICT(id_inscripcion) DO UPDATE
    SET estado=excluded.estado,hora_entrada=excluded.hora_entrada,hora_salida=excluded.hora_salida,observacion=excluded.observacion RETURNING *""",
        i=ins_id,
        **data.model_dump(),
    )
    audit(c, user, "asistencia_registrada", "inscripcion", ins_id)
    return row


@router.get("/manage/activities/{activity_id}/impact")
def get_impact(
    activity_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    owned_activity(c, user, activity_id, lock=False)
    return one(
        c, "SELECT * FROM impacto_actividad WHERE id_actividad=:a", a=activity_id
    )


@router.put("/manage/activities/{activity_id}/impact")
def impact(
    activity_id: int,
    data: Impact,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    a = owned_activity(c, user, activity_id)
    if a["estado"] != "finalizada":
        raise HTTPException(409, "Finaliza la actividad antes de registrar impacto")
    hours = one(
        c,
        "SELECT coalesce(sum(extract(epoch FROM(s.hora_salida-s.hora_entrada))/3600),0) h FROM asistencia s JOIN inscripcion i USING(id_inscripcion) WHERE i.id_actividad=:a AND s.estado='asistio'",
        a=activity_id,
    )["h"]
    result = one(
        c,
        """INSERT INTO impacto_actividad(id_actividad,beneficiarios_estimados,descripcion_impacto,horas_voluntariado)
    VALUES(:a,:beneficiarios_estimados,:descripcion_impacto,:h) ON CONFLICT(id_actividad) DO UPDATE SET
    beneficiarios_estimados=excluded.beneficiarios_estimados,descripcion_impacto=excluded.descripcion_impacto,horas_voluntariado=excluded.horas_voluntariado RETURNING *""",
        a=activity_id,
        h=hours,
        **data.model_dump(),
    )
    audit(c, user, "impacto_registrado", "actividad", activity_id)
    return result


@router.post("/manage/applications/{ins_id}/certificate", status_code=201)
def issue_certificate(
    ins_id: int,
    data: CertificateConsent,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    i, a = manage_inscription(c, user, ins_id)
    existing = one(c, "SELECT * FROM certificado WHERE id_inscripcion=:i", i=ins_id)
    if existing:
        return existing
    s = one(
        c,
        "SELECT *,extract(epoch FROM(hora_salida-hora_entrada))/3600 horas FROM asistencia WHERE id_inscripcion=:i AND estado='asistio'",
        i=ins_id,
    )
    if a["estado"] != "finalizada" or not s or not s["horas"] or s["horas"] <= 0:
        raise HTTPException(
            409,
            "Requiere actividad finalizada y asistencia efectiva con horas positivas",
        )
    v = require(
        one(c, "SELECT * FROM voluntario WHERE id_voluntario=:v", v=i["id_voluntario"])
    )
    org = require(
        one(
            c,
            "SELECT nombre FROM organizacion WHERE id_organizacion=:o",
            o=a["id_organizacion"],
        )
    )
    code = secrets.token_hex(20)
    pdf = certificate_pdf(
        v["nombres"] + " " + v["apellidos"],
        a["titulo"],
        org["nombre"],
        s["horas"],
        code,
        datetime.now(timezone.utc),
    )
    key = put_object(pdf, "certificates", ins_id, "pdf", "application/pdf")
    result = one(
        c,
        "INSERT INTO certificado(id_inscripcion,codigo_verificacion,horas_certificadas,archivo_url) VALUES(:i,:code,:h,:k) RETURNING *",
        i=ins_id,
        code=code,
        h=s["horas"],
        k=key,
    )
    notify(
        c,
        v["id_usuario"],
        "Certificado disponible",
        "Tu participación ya tiene un certificado verificable.",
    )
    audit(c, user, "certificado_emitido_con_aviso_publico", "inscripcion", ins_id)
    return result


@router.get("/certificates/private/{certificate_id}/file")
def download_certificate(
    certificate_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    certificate = require(
        one(
            c,
            "SELECT ce.archivo_url FROM certificado ce JOIN inscripcion i USING(id_inscripcion) JOIN voluntario v USING(id_voluntario) WHERE ce.id_certificado=:ce AND v.id_usuario=:u",
            ce=certificate_id,
            u=user["id_usuario"],
        )
    )
    return download(certificate["archivo_url"])


@router.get("/manage/activities/{activity_id}/evidence")
def evidence(
    activity_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    owned_activity(c, user, activity_id, lock=False)
    return rows(
        c,
        "SELECT id_evidencia,tipo,descripcion,fecha_subida FROM evidencia_actividad WHERE id_actividad=:a ORDER BY id_evidencia DESC",
        a=activity_id,
    )


@router.post("/manage/activities/{activity_id}/evidence", status_code=201)
def upload_evidence(
    activity_id: int,
    descripcion: str = Form(min_length=5, max_length=1000),
    file: UploadFile = File(),
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    owned_activity(c, user, activity_id)
    content, ext, mime = validate_file(
        file.file.read(10 * 1024 * 1024 + 1), file.content_type
    )
    key = put_object(content, "evidence", activity_id, ext, mime)
    result = one(
        c,
        "INSERT INTO evidencia_actividad(id_actividad,id_usuario,tipo,archivo_url,descripcion) VALUES(:a,:u,:t,:k,:d) RETURNING id_evidencia",
        a=activity_id,
        u=user["id_usuario"],
        t="pdf" if ext == "pdf" else "imagen",
        k=key,
        d=descripcion,
    )
    audit(c, user, "evidencia_privada", "actividad", activity_id)
    return result


@router.get("/manage/activities/{activity_id}/evidence/{evidence_id}/file")
def download_evidence(
    activity_id: int,
    evidence_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    owned_activity(c, user, activity_id, lock=False)
    result = require(
        one(
            c,
            "SELECT archivo_url FROM evidencia_actividad WHERE id_evidencia=:e AND id_actividad=:a",
            e=evidence_id,
            a=activity_id,
        )
    )
    return download(result["archivo_url"])
