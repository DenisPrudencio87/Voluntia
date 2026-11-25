from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.db import transaction, one, rows, execute
from backend.app.security.session import admin_user
from backend.app.schemas.domain import (
    Review,
    OrganizationState,
    UserState,
    Roles,
    Catalog,
    Reason,
)
from backend.app.services.domain import require, audit, notify, change_activity_state
from backend.app.services.storage import download

router = APIRouter(
    prefix="/admin",
    tags=["Administración"],
    dependencies=[Depends(admin_user, scope="function")],
)


@router.get("/statistics")
def statistics(c=Depends(transaction, scope="function")):
    return one(
        c,
        """SELECT (SELECT count(*) FROM usuario) usuarios,(SELECT count(*) FROM organizacion WHERE estado_verificacion='pendiente') organizaciones_pendientes,
    (SELECT count(*) FROM actividad) actividades,(SELECT count(*) FROM inscripcion) inscripciones""",
    )


@router.get("/organizations")
def organizations(page: int = Query(1, ge=1), c=Depends(transaction, scope="function")):
    return rows(
        c,
        "SELECT * FROM organizacion ORDER BY id_organizacion DESC LIMIT 20 OFFSET :o",
        o=(page - 1) * 20,
    )


@router.get("/organizations/{org_id}/documents")
def documents(org_id: int, c=Depends(transaction, scope="function")):
    return rows(
        c,
        "SELECT id_documento,id_organizacion,tipo_documento,numero_documento,estado_revision,fecha_subida FROM documento_organizacion WHERE id_organizacion=:o ORDER BY id_documento DESC",
        o=org_id,
    )


@router.get("/documents/{doc_id}/file")
def document_file(
    doc_id: int,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    # Acceso documental circunscrito a una revisión pendiente.
    doc = require(
        one(
            c,
            "SELECT d.archivo_url FROM documento_organizacion d JOIN organizacion o USING(id_organizacion) WHERE d.id_documento=:d AND d.estado_revision='pendiente' AND o.estado_verificacion IN ('pendiente','rechazada')",
            d=doc_id,
        )
    )
    audit(c, user, "documento_consultado_revision", "documento_organizacion", doc_id)
    return download(doc["archivo_url"])


@router.post("/documents/{doc_id}/review")
def review(
    doc_id: int,
    data: Review,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    doc = require(
        one(
            c,
            "SELECT id_organizacion FROM documento_organizacion WHERE id_documento=:d",
            d=doc_id,
        )
    )
    org = require(
        one(
            c,
            "SELECT * FROM organizacion WHERE id_organizacion=:o FOR UPDATE",
            o=doc["id_organizacion"],
        )
    )
    if org["estado_verificacion"] not in ("pendiente", "rechazada"):
        raise HTTPException(409, "La organización no tiene una revisión pendiente")
    result = require(
        one(
            c,
            "UPDATE documento_organizacion SET estado_revision=:s,fecha_revision=now() WHERE id_documento=:d AND estado_revision='pendiente' RETURNING id_documento",
            s=data.estado,
            d=doc_id,
        )
    )
    audit(
        c,
        user,
        "revision_documento",
        "organizacion",
        doc["id_organizacion"],
        data.estado + ": " + data.motivo,
    )
    return result


@router.post("/organizations/{org_id}/state")
def organization_state(
    org_id: int,
    data: OrganizationState,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    require(
        one(
            c,
            "SELECT * FROM organizacion WHERE id_organizacion=:o FOR UPDATE",
            o=org_id,
        )
    )
    if data.estado == "verificada":
        docs = one(
            c,
            "SELECT count(*) FILTER(WHERE estado_revision='aprobado') aprobados,count(*) FILTER(WHERE estado_revision='pendiente') pendientes FROM documento_organizacion WHERE id_organizacion=:o",
            o=org_id,
        )
        if not docs["aprobados"] or docs["pendientes"]:
            raise HTTPException(
                409, "Aprueba al menos un documento y resuelve todos los pendientes"
            )
    execute(
        c,
        "UPDATE organizacion SET estado_verificacion=:s WHERE id_organizacion=:o",
        s=data.estado,
        o=org_id,
    )
    audit(
        c,
        user,
        "revision_organizacion",
        "organizacion",
        org_id,
        data.estado + ": " + data.motivo,
    )
    for m in rows(
        c,
        "SELECT id_usuario FROM organizacion_miembro WHERE id_organizacion=:o AND estado='activo'",
        o=org_id,
    ):
        notify(
            c,
            m["id_usuario"],
            "Revisión de organización",
            data.estado + ": " + data.motivo,
            "/panel/organizacion",
        )
    return {"mensaje": "Organización actualizada"}


@router.get("/users")
def users(page: int = Query(1, ge=1), c=Depends(transaction, scope="function")):
    return rows(
        c,
        "SELECT u.id_usuario,u.correo,u.estado,u.email_verificado,coalesce(array_agg(r.nombre) FILTER(WHERE ur.activo),'{}') roles FROM usuario u LEFT JOIN usuario_rol ur USING(id_usuario) LEFT JOIN rol r USING(id_rol) GROUP BY u.id_usuario ORDER BY u.id_usuario LIMIT 20 OFFSET :o",
        o=(page - 1) * 20,
    )


def protect_last_admin(c, user_id):
    general = one(
        c,
        "SELECT 1 FROM usuario_rol ur JOIN rol r USING(id_rol) JOIN usuario u USING(id_usuario) WHERE ur.id_usuario=:u AND ur.activo AND r.nombre='administrador' AND u.estado='activo' AND u.email_verificado",
        u=user_id,
    )
    if (
        general
        and one(
            c,
            "SELECT count(*) n FROM usuario_rol ur JOIN rol r USING(id_rol) JOIN usuario u USING(id_usuario) WHERE r.nombre='administrador' AND ur.activo AND u.estado='activo' AND u.email_verificado",
        )["n"]
        <= 1
    ):
        raise HTTPException(
            409, "No puedes retirar al último administrador general activo"
        )


def protect_org_admins(c, user_id):
    missing = one(
        c,
        """SELECT m.id_organizacion FROM organizacion_miembro m WHERE m.id_usuario=:u AND m.cargo='administrador' AND m.estado='activo'
    AND NOT EXISTS(SELECT 1 FROM organizacion_miembro other JOIN usuario u ON u.id_usuario=other.id_usuario
    JOIN usuario_rol ur ON ur.id_usuario=u.id_usuario JOIN rol r USING(id_rol)
    WHERE other.id_organizacion=m.id_organizacion AND other.id_usuario<>:u AND other.cargo='administrador'
    AND other.estado='activo' AND u.estado='activo' AND u.email_verificado AND ur.activo AND r.nombre='organizacion') LIMIT 1""",
        u=user_id,
    )
    if missing:
        raise HTTPException(
            409, "Asigna otro administrador activo a sus organizaciones primero"
        )


@router.post("/users/{user_id}/state")
def user_state(
    user_id: int,
    data: UserState,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    execute(c, "SELECT pg_advisory_xact_lock(864021)")
    require(
        one(
            c,
            "SELECT id_usuario FROM usuario WHERE id_usuario=:u FOR UPDATE",
            u=user_id,
        )
    )
    if data.estado == "suspendido":
        protect_last_admin(c, user_id)
        protect_org_admins(c, user_id)
    execute(
        c,
        "UPDATE usuario SET estado=:s,fecha_actualizacion=clock_timestamp() WHERE id_usuario=:u",
        s=data.estado,
        u=user_id,
    )
    audit(
        c, user, "estado_usuario", "usuario", user_id, data.estado + ": " + data.motivo
    )
    return {"mensaje": "Estado actualizado"}


@router.post("/users/{user_id}/roles")
def user_roles(
    user_id: int,
    data: Roles,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    execute(c, "SELECT pg_advisory_xact_lock(864021)")
    require(
        one(
            c,
            "SELECT id_usuario FROM usuario WHERE id_usuario=:u FOR UPDATE",
            u=user_id,
        )
    )
    if "administrador" not in data.roles:
        protect_last_admin(c, user_id)
    if "organizacion" not in data.roles:
        protect_org_admins(c, user_id)
        # Revocar el rol también retira las membresías anteriores: crear otra
        # organización no debe recuperar permisos que administración retiró.
        execute(
            c,
            "UPDATE organizacion_miembro SET estado='inactivo' WHERE id_usuario=:u AND estado='activo'",
            u=user_id,
        )
    execute(c, "UPDATE usuario_rol SET activo=false WHERE id_usuario=:u", u=user_id)
    for role in set(data.roles):
        execute(
            c,
            "INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre=:r ON CONFLICT(id_usuario,id_rol) DO UPDATE SET activo=true",
            u=user_id,
            r=role,
        )
    execute(
        c,
        "UPDATE usuario SET fecha_actualizacion=clock_timestamp() WHERE id_usuario=:u",
        u=user_id,
    )
    audit(c, user, "roles_usuario", "usuario", user_id, data.motivo)
    return {"mensaje": "Roles actualizados. Sesiones revocadas."}


def catalog_table(kind):
    if kind not in ("categoria", "habilidad"):
        raise HTTPException(404, "Catálogo no encontrado")
    return kind


@router.get("/catalogs/{kind}")
def catalogs(kind: str, c=Depends(transaction, scope="function")):
    table = catalog_table(kind)
    return rows(c, f"SELECT * FROM {table} ORDER BY nombre")


@router.post("/catalogs/{kind}", status_code=201)
def create_catalog(
    kind: str,
    data: Catalog,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    table = catalog_table(kind)
    row = one(
        c,
        f"INSERT INTO {table}(nombre,descripcion,activo) VALUES(:nombre,:descripcion,:activo) RETURNING *",
        **data.model_dump(),
    )
    audit(c, user, "catalogo_creado", kind, row["id_" + kind])
    return row


@router.put("/catalogs/{kind}/{item_id}")
def update_catalog(
    kind: str,
    item_id: int,
    data: Catalog,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    table = catalog_table(kind)
    row = require(
        one(
            c,
            f"UPDATE {table} SET nombre=:nombre,descripcion=:descripcion,activo=:activo WHERE id_{table}=:i RETURNING *",
            i=item_id,
            **data.model_dump(),
        )
    )
    audit(c, user, "catalogo_actualizado", kind, item_id)
    return row


@router.get("/activities")
def activities(page: int = Query(1, ge=1), c=Depends(transaction, scope="function")):
    return rows(
        c,
        "SELECT id_actividad,id_organizacion,titulo,estado,fecha_inicio FROM actividad ORDER BY id_actividad DESC LIMIT 20 OFFSET :o",
        o=(page - 1) * 20,
    )


@router.post("/activities/{activity_id}/cancel")
def cancel_activity(
    activity_id: int,
    data: Reason,
    c=Depends(transaction, scope="function"),
    user=Depends(admin_user, scope="function"),
):
    a = require(
        one(
            c, "SELECT * FROM actividad WHERE id_actividad=:a FOR UPDATE", a=activity_id
        )
    )
    return change_activity_state(c, user, a, "cancelada", data.motivo)


@router.get("/audit")
def audit_log(page: int = Query(1, ge=1), c=Depends(transaction, scope="function")):
    return rows(
        c,
        "SELECT * FROM bitacora_evento ORDER BY id_evento DESC LIMIT 30 OFFSET :o",
        o=(page - 1) * 30,
    )
