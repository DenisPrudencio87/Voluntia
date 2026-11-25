from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.db import transaction, one, rows, execute
from backend.app.security.session import verified_user, current_user
from backend.app.schemas.domain import Profile
from backend.app.services.domain import require, active_skills, location, audit

router = APIRouter(prefix="/volunteer", tags=["Voluntario"])


@router.get("/profile")
def profile(
    c=Depends(transaction, scope="function"),
    user=Depends(current_user, scope="function"),
):
    row = one(c, "SELECT * FROM voluntario WHERE id_usuario=:u", u=user["id_usuario"])
    if not row:
        return None
    result = dict(row)
    result["habilidades"] = rows(
        c,
        "SELECT vh.*,h.nombre FROM voluntario_habilidad vh JOIN habilidad h USING(id_habilidad) WHERE vh.id_voluntario=:v",
        v=row["id_voluntario"],
    )
    result["ubicacion"] = (
        one(c, "SELECT * FROM ubicacion WHERE id_ubicacion=:l", l=row["id_ubicacion"])
        if row["id_ubicacion"]
        else None
    )
    result["horas"] = one(
        c, "SELECT fn_horas_voluntariado(:v) n", v=row["id_voluntario"]
    )["n"]
    return result


@router.put("/profile")
def save_profile(
    data: Profile,
    c=Depends(transaction, scope="function"),
    user=Depends(verified_user, scope="function"),
):
    if "voluntario" not in user["roles"]:
        raise HTTPException(403, "Se requiere rol Voluntario")
    active_skills(c, data.habilidades)
    values = data.model_dump(exclude={"habilidades", "ubicacion"})
    values["id_ubicacion"] = location(c, data.ubicacion)
    row = one(
        c,
        """INSERT INTO voluntario(id_usuario,nombres,apellidos,telefono,fecha_nacimiento,biografia,foto_url,id_ubicacion)
    VALUES(:u,:nombres,:apellidos,:telefono,:fecha_nacimiento,:biografia,:foto_url,:id_ubicacion)
    ON CONFLICT(id_usuario) DO UPDATE SET nombres=excluded.nombres,apellidos=excluded.apellidos,telefono=excluded.telefono,
    fecha_nacimiento=excluded.fecha_nacimiento,biografia=excluded.biografia,foto_url=excluded.foto_url,id_ubicacion=excluded.id_ubicacion,fecha_actualizacion=now() RETURNING *""",
        u=user["id_usuario"],
        **values,
    )
    execute(
        c,
        "DELETE FROM voluntario_habilidad WHERE id_voluntario=:v",
        v=row["id_voluntario"],
    )
    for skill in data.habilidades:
        execute(
            c,
            "INSERT INTO voluntario_habilidad(id_voluntario,id_habilidad,nivel) VALUES(:v,:h,:n)",
            v=row["id_voluntario"],
            h=skill.id_habilidad,
            n=skill.nivel,
        )
    audit(c, user, "perfil_actualizado", "voluntario", row["id_voluntario"])
    return row


@router.get("/applications")
def applications(
    page: int = Query(1, ge=1),
    c=Depends(transaction, scope="function"),
    user=Depends(current_user, scope="function"),
):
    return rows(
        c,
        """SELECT i.*,e.nombre estado,a.titulo,a.fecha_inicio,a.fecha_fin,a.estado estado_actividad,
    ce.id_certificado,ce.codigo_verificacion,ce.horas_certificadas FROM inscripcion i JOIN voluntario v USING(id_voluntario)
    JOIN estado_inscripcion e USING(id_estado) JOIN actividad a USING(id_actividad) LEFT JOIN certificado ce USING(id_inscripcion)
    WHERE v.id_usuario=:u ORDER BY i.fecha_inscripcion DESC LIMIT 20 OFFSET :offset""",
        u=user["id_usuario"],
        offset=(page - 1) * 20,
    )


@router.get("/applications/{ins_id}/history")
def history(
    ins_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(current_user, scope="function"),
):
    require(
        one(
            c,
            "SELECT i.id_inscripcion FROM inscripcion i JOIN voluntario v USING(id_voluntario) WHERE i.id_inscripcion=:i AND v.id_usuario=:u",
            i=ins_id,
            u=user["id_usuario"],
        )
    )
    return rows(
        c,
        "SELECT h.fecha_cambio,h.comentario,e.nombre estado FROM historial_inscripcion h JOIN estado_inscripcion e USING(id_estado) WHERE h.id_inscripcion=:i ORDER BY h.id_historial",
        i=ins_id,
    )


@router.get("/notifications")
def notifications(
    page: int = Query(1, ge=1),
    c=Depends(transaction, scope="function"),
    user=Depends(current_user, scope="function"),
):
    return rows(
        c,
        "SELECT * FROM notificacion WHERE id_usuario=:u ORDER BY id_notificacion DESC LIMIT 20 OFFSET :o",
        u=user["id_usuario"],
        o=(page - 1) * 20,
    )


@router.post("/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(current_user, scope="function"),
):
    return require(
        one(
            c,
            "UPDATE notificacion SET leida=true,fecha_lectura=coalesce(fecha_lectura,now()) WHERE id_notificacion=:n AND id_usuario=:u RETURNING *",
            n=notification_id,
            u=user["id_usuario"],
        )
    )
