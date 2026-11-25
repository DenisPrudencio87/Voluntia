from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Request,Query
from backend.app.db import transaction,one,rows,execute
from backend.app.security.session import verified_user,limiter
from backend.app.schemas.domain import Activity,ActivityState,Application,ApplicationState
from backend.app.services.domain import member,require,owned_activity,active_skills,location,audit,notify,change_activity_state,set_application_state

router=APIRouter(tags=['Actividades e inscripciones'])


@router.get('/organization/{org_id}/activities')
def list_owned(org_id:int,page:int=Query(1,ge=1),c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id,allow_suspended=True)
    return rows(c,'SELECT *,fn_cupos_disponibles(id_actividad) cupos_disponibles FROM actividad WHERE id_organizacion=:o ORDER BY id_actividad DESC LIMIT 20 OFFSET :offset',o=org_id,offset=(page-1)*20)


def activity_values(c,data):
    active_skills(c,data.habilidades)
    if not one(c,'SELECT id_categoria FROM categoria WHERE id_categoria=:i AND activo',i=data.id_categoria):
        raise HTTPException(422,'Categoría inexistente o inactiva')
    return {**data.model_dump(exclude={'ubicacion','habilidades'}),'id_ubicacion':location(c,data.ubicacion)}


def save_skills(c,activity,skills):
    execute(c,'DELETE FROM actividad_habilidad WHERE id_actividad=:a',a=activity)
    for s in skills:
        execute(c,'INSERT INTO actividad_habilidad(id_actividad,id_habilidad,nivel_requerido,obligatoria) VALUES(:a,:id_habilidad,:nivel_requerido,:obligatoria)',a=activity,**s.model_dump())


@router.post('/organization/{org_id}/activities',status_code=201)
def create(org_id:int,data:Activity,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id)
    values=activity_values(c,data)
    a=one(c,"""INSERT INTO actividad(id_organizacion,id_categoria,id_ubicacion,titulo,descripcion,fecha_inicio,fecha_fin,fecha_cierre_inscripcion,cupo_maximo,modalidad,imagen_portada_url)
    VALUES(:o,:id_categoria,:id_ubicacion,:titulo,:descripcion,:fecha_inicio,:fecha_fin,:fecha_cierre_inscripcion,:cupo_maximo,:modalidad,:imagen_portada_url) RETURNING *""",o=org_id,**values)
    save_skills(c,a['id_actividad'],data.habilidades)
    audit(c,user,'actividad_creada','actividad',a['id_actividad'])
    return a


@router.get('/manage/activities/{activity_id}')
def get_owned(activity_id:int,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    a=dict(owned_activity(c,user,activity_id,lock=False))
    a['habilidades']=rows(c,'SELECT * FROM actividad_habilidad WHERE id_actividad=:a',a=activity_id)
    a['ubicacion']=one(c,'SELECT * FROM ubicacion WHERE id_ubicacion=:u',u=a['id_ubicacion']) if a['id_ubicacion'] else None
    return a


@router.put('/manage/activities/{activity_id}')
def update(activity_id:int,data:Activity,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    a=owned_activity(c,user,activity_id)
    if a['estado'] not in ('borrador','publicada','cerrada') or (a['estado']!='borrador' and datetime.now(timezone.utc)>=a['fecha_inicio']):
        raise HTTPException(409,'Esta actividad ya no admite edición')
    if a['estado']!='borrador' and data.fecha_inicio<=datetime.now(timezone.utc):
        raise HTTPException(409,'Mantén el inicio en el futuro')
    values=activity_values(c,data)
    execute(c,"""UPDATE actividad SET id_categoria=:id_categoria,id_ubicacion=:id_ubicacion,titulo=:titulo,descripcion=:descripcion,
    fecha_inicio=:fecha_inicio,fecha_fin=:fecha_fin,fecha_cierre_inscripcion=:fecha_cierre_inscripcion,cupo_maximo=:cupo_maximo,
    modalidad=:modalidad,imagen_portada_url=:imagen_portada_url,fecha_actualizacion=now() WHERE id_actividad=:a""",a=activity_id,**values)
    save_skills(c,activity_id,data.habilidades)
    for row in rows(c,"SELECT v.id_usuario FROM inscripcion i JOIN voluntario v USING(id_voluntario) JOIN estado_inscripcion e USING(id_estado) WHERE i.id_actividad=:a AND e.nombre IN ('pendiente','espera','aceptada')",a=activity_id):
        notify(c,row['id_usuario'],'Actividad actualizada','Revisa fechas y ubicación de '+data.titulo)
    audit(c,user,'actividad_actualizada','actividad',activity_id)
    return {'mensaje':'Actividad actualizada'}


@router.post('/manage/activities/{activity_id}/state')
def state(activity_id:int,data:ActivityState,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    return change_activity_state(c,user,owned_activity(c,user,activity_id),data.estado,data.motivo)


@router.post('/activities/{activity_id}/applications',status_code=201)
def apply(activity_id:int,data:Application,request:Request,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    limiter.check(request,'apply',str(user['id_usuario']),limit=10)
    if 'voluntario' not in user['roles']:
        raise HTTPException(403,'Se requiere rol Voluntario')
    a=require(one(c,'SELECT * FROM actividad WHERE id_actividad=:a FOR UPDATE',a=activity_id))
    org=require(one(c,'SELECT estado_verificacion FROM organizacion WHERE id_organizacion=:o',o=a['id_organizacion']))
    if a['estado']!='publicada' or a['fecha_cierre_inscripcion']<=datetime.now(timezone.utc) or org['estado_verificacion']!='verificada':
        raise HTTPException(409,'Las inscripciones no están disponibles')
    v=require(one(c,'SELECT id_voluntario FROM voluntario WHERE id_usuario=:u',u=user['id_usuario']),'Completa primero tu perfil voluntario')
    missing=rows(c,"""SELECT h.nombre FROM actividad_habilidad ah JOIN habilidad h USING(id_habilidad)
    LEFT JOIN voluntario_habilidad vh ON vh.id_habilidad=ah.id_habilidad AND vh.id_voluntario=:v
    WHERE ah.id_actividad=:a AND ah.obligatoria AND (vh.nivel IS NULL OR
    array_position(ARRAY['basico','intermedio','avanzado'],vh.nivel::text)<array_position(ARRAY['basico','intermedio','avanzado'],ah.nivel_requerido::text))""",v=v['id_voluntario'],a=activity_id)
    if missing:
        raise HTTPException(422,'Faltan habilidades obligatorias: '+', '.join(r['nombre'] for r in missing))
    state='pendiente' if one(c,'SELECT fn_cupos_disponibles(:a) n',a=activity_id)['n']>0 else 'espera'
    ins=one(c,'INSERT INTO inscripcion(id_actividad,id_voluntario,id_estado,motivacion) VALUES(:a,:v,(SELECT id_estado FROM estado_inscripcion WHERE nombre=:s),:m) RETURNING *',a=activity_id,v=v['id_voluntario'],s=state,m=data.motivacion)
    for m in rows(c,"SELECT id_usuario FROM organizacion_miembro WHERE id_organizacion=:o AND estado='activo'",o=a['id_organizacion']):
        notify(c,m['id_usuario'],'Nueva postulación',a['titulo'],'/panel/organizacion')
    return {**ins,'estado':state}


@router.get('/manage/activities/{activity_id}/applications')
def applicants(activity_id:int,page:int=Query(1,ge=1),c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    owned_activity(c,user,activity_id,lock=False)
    return rows(c,"""SELECT i.*,v.nombres,v.apellidos,e.nombre estado,s.estado asistencia,s.hora_entrada,s.hora_salida,ce.id_certificado
    FROM inscripcion i JOIN voluntario v USING(id_voluntario) JOIN estado_inscripcion e USING(id_estado)
    LEFT JOIN asistencia s USING(id_inscripcion) LEFT JOIN certificado ce USING(id_inscripcion)
    WHERE i.id_actividad=:a ORDER BY i.id_inscripcion LIMIT 20 OFFSET :offset""",a=activity_id,offset=(page-1)*20)


@router.post('/applications/{ins_id}/state')
def application_state(ins_id:int,data:ApplicationState,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    stub=require(one(c,'SELECT id_actividad,id_voluntario FROM inscripcion WHERE id_inscripcion=:i',i=ins_id))
    a=require(one(c,'SELECT * FROM actividad WHERE id_actividad=:a FOR UPDATE',a=stub['id_actividad']))
    i=require(one(c,'SELECT i.*,e.nombre estado FROM inscripcion i JOIN estado_inscripcion e USING(id_estado) WHERE i.id_inscripcion=:i FOR UPDATE OF i',i=ins_id))
    own=one(c,'SELECT id_voluntario FROM voluntario WHERE id_voluntario=:v AND id_usuario=:u',v=i['id_voluntario'],u=user['id_usuario'])
    if own and data.estado=='cancelada':
        if datetime.now(timezone.utc)>=a['fecha_inicio']:
            raise HTTPException(409,'Solo puedes cancelar antes del inicio')
    else:
        member(c,user,a['id_organizacion'])
        if a['estado'] in ('cancelada','finalizada','borrador') or datetime.now(timezone.utc)>=a['fecha_inicio']:
            raise HTTPException(409,'No se admiten cambios de postulantes')
        if data.estado=='cancelada':
            raise HTTPException(403,'La organización debe rechazar o cancelar la actividad')
    if data.estado=='aceptada':
        execute(c,'SELECT fn_aceptar_inscripcion(:i,:u)',i=ins_id,u=user['id_usuario'])
        return {'mensaje':'Inscripción aceptada'}
    if data.estado not in {'pendiente':{'espera','rechazada','cancelada'},'espera':{'rechazada','cancelada'},'aceptada':{'cancelada'}}.get(i['estado'],set()):
        raise HTTPException(409,'Transición de inscripción no permitida')
    return set_application_state(c,ins_id,data.estado,data.observacion)
