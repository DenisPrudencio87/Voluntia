from datetime import datetime, timezone
from fastapi import HTTPException
from backend.app.db import one, rows, execute


def require(row, message="Registro no encontrado"):
    if not row:
        raise HTTPException(404, message)
    return row


def audit(c, user, action, entity, record, detail=""):
    execute(
        c,
        "INSERT INTO bitacora_evento(id_usuario,accion,entidad,id_registro,detalle) VALUES(:u,:a,:e,:r,:d)",
        u=user["id_usuario"],
        a=action,
        e=entity,
        r=record,
        d=detail,
    )


def notify(c, user_id, title, message, path="/panel/voluntario"):
    execute(
        c,
        "INSERT INTO notificacion(id_usuario,titulo,mensaje,tipo,url_destino) VALUES(:u,:t,:m,'sistema',:p)",
        u=user_id,
        t=title,
        m=message,
        p=path,
    )


def member(c, user, org, admin=False, allow_suspended=False):
    # La membresía y rol se consultan en cada operación, nunca se confía en un id del cliente.
    row = require(
        one(
            c,
            "SELECT m.*,o.estado_verificacion FROM organizacion_miembro m JOIN organizacion o USING(id_organizacion) WHERE m.id_organizacion=:o AND m.id_usuario=:u AND m.estado='activo'",
            o=org,
            u=user["id_usuario"],
        )
    )
    if "organizacion" not in user["roles"] or (
        admin and row["cargo"] != "administrador"
    ):
        raise HTTPException(403, "Tu cargo no permite esta operación")
    if row["estado_verificacion"] == "suspendida" and not allow_suspended:
        raise HTTPException(403, "Organización suspendida")
    return row


def owned_activity(c, user, activity_id, lock=True):
    a = require(
        one(
            c,
            "SELECT * FROM actividad WHERE id_actividad=:a"
            + (" FOR UPDATE" if lock else ""),
            a=activity_id,
        )
    )
    member(c, user, a["id_organizacion"])
    return a


def location(c, data):
    if not data:
        return None
    return one(
        c,
        "INSERT INTO ubicacion(nombre_lugar,direccion,latitud,longitud) VALUES(:nombre_lugar,:direccion,:latitud,:longitud) RETURNING id_ubicacion",
        **data.model_dump(),
    )["id_ubicacion"]


def active_skills(c, skills):
    ids = [s.id_habilidad for s in skills]
    if len(set(ids)) != len(ids):
        raise HTTPException(422, "No repitas habilidades")
    for skill in ids:
        if not one(
            c,
            "SELECT id_habilidad FROM habilidad WHERE id_habilidad=:h AND activo",
            h=skill,
        ):
            raise HTTPException(422, "Habilidad inexistente o inactiva")


def set_application_state(c, inscription, state, observation=""):
    return one(
        c,
        "UPDATE inscripcion SET id_estado=(SELECT id_estado FROM estado_inscripcion WHERE nombre=:s),observacion=:o,fecha_actualizacion=now() WHERE id_inscripcion=:i RETURNING *",
        s=state,
        o=observation,
        i=inscription,
    )


def change_activity_state(c, user, a, state, reason):
    now = datetime.now(timezone.utc)
    transitions = {
        "borrador": {"publicada", "cancelada"},
        "publicada": {"cerrada", "en_curso", "cancelada"},
        "cerrada": {"en_curso", "cancelada"},
        "en_curso": {"finalizada", "cancelada"},
    }
    if state not in transitions.get(a["estado"], set()):
        raise HTTPException(409, "Transición de actividad no permitida")
    if state == "cancelada" and len(reason.strip()) < 5:
        raise HTTPException(422, "Indica el motivo de cancelación")
    if state == "publicada":
        org = require(
            one(
                c,
                "SELECT * FROM organizacion WHERE id_organizacion=:o FOR UPDATE",
                o=a["id_organizacion"],
            )
        )
        if (
            org["estado_verificacion"] != "verificada"
            or a["fecha_cierre_inscripcion"] <= now
            or a["fecha_inicio"] <= now
        ):
            raise HTTPException(
                409, "Publicar requiere organización verificada y fechas futuras"
            )
        if not one(
            c,
            "SELECT id_categoria FROM categoria WHERE id_categoria=:i AND activo",
            i=a["id_categoria"],
        ):
            raise HTTPException(409, "Selecciona una categoría activa")
    if state == "en_curso" and now < a["fecha_inicio"]:
        raise HTTPException(409, "La actividad aún no comienza")
    if state == "finalizada" and now < a["fecha_fin"]:
        raise HTTPException(409, "Espera hasta la fecha de fin")
    if state in ("cancelada", "finalizada"):
        ins = rows(
            c,
            "SELECT i.id_inscripcion,e.nombre FROM inscripcion i JOIN estado_inscripcion e USING(id_estado) WHERE i.id_actividad=:a ORDER BY i.id_inscripcion FOR UPDATE OF i",
            a=a["id_actividad"],
        )
        for i in ins:
            if state == "cancelada" and i["nombre"] in (
                "pendiente",
                "espera",
                "aceptada",
            ):
                set_application_state(c, i["id_inscripcion"], "cancelada", reason)
            elif state == "finalizada" and i["nombre"] in (
                "pendiente",
                "espera",
                "aceptada",
            ):
                set_application_state(
                    c,
                    i["id_inscripcion"],
                    "finalizada" if i["nombre"] == "aceptada" else "rechazada",
                    "Cierre de actividad",
                )
    execute(
        c,
        "UPDATE actividad SET estado=:s,fecha_publicacion=CASE WHEN :publish THEN now() ELSE fecha_publicacion END,fecha_actualizacion=now() WHERE id_actividad=:a",
        s=state,
        publish=state == "publicada",
        a=a["id_actividad"],
    )
    audit(
        c,
        user,
        "estado_actividad",
        "actividad",
        a["id_actividad"],
        state + ": " + reason,
    )
    return {"mensaje": "Estado actualizado", "estado": state}
