from datetime import datetime
from fastapi import APIRouter,Depends,Query
from backend.app.db import transaction,one,rows
from backend.app.services.domain import require

router=APIRouter(tags=['Catálogo público'])
PUBLIC="a.estado<>'borrador' AND o.estado_verificacion='verificada'"
SUMMARY="""SELECT a.id_actividad,a.id_organizacion,a.id_categoria,a.titulo,a.descripcion,a.fecha_inicio,a.fecha_fin,a.fecha_cierre_inscripcion,
a.modalidad,a.estado,a.imagen_portada_url,a.cupo_maximo,o.nombre organizacion,c.nombre categoria,l.nombre_lugar,l.direccion,
fn_cupos_disponibles(a.id_actividad) cupos_disponibles FROM actividad a JOIN organizacion o USING(id_organizacion)
JOIN categoria c USING(id_categoria) LEFT JOIN ubicacion l ON l.id_ubicacion=a.id_ubicacion"""


@router.get('/catalogs')
def catalogs(c=Depends(transaction)):
    return {'categorias':rows(c,'SELECT * FROM categoria WHERE activo ORDER BY nombre'),'habilidades':rows(c,'SELECT * FROM habilidad WHERE activo ORDER BY nombre')}


@router.get('/statistics')
def statistics(c=Depends(transaction)):
    return one(c,"""SELECT
    (SELECT count(*) FROM organizacion WHERE estado_verificacion='verificada') organizaciones,
    (SELECT count(*) FROM actividad a JOIN organizacion o USING(id_organizacion) WHERE a.estado='publicada' AND o.estado_verificacion='verificada' AND a.fecha_cierre_inscripcion>now()) actividades,
    (SELECT count(*) FROM voluntario v JOIN usuario u USING(id_usuario) WHERE u.estado='activo') voluntarios,
    (SELECT coalesce(sum(extract(epoch FROM(s.hora_salida-s.hora_entrada))/3600),0) FROM asistencia s WHERE s.estado='asistio') horas""")


@router.get('/activities')
def activities(q:str=Query('',max_length=100),categoria:int|None=None,ubicacion:str=Query('',max_length=100),modalidad:str=Query('',max_length=20),desde:datetime|None=None,disponible:bool=False,page:int=Query(1,ge=1),size:int=Query(9,ge=1,le=50),c=Depends(transaction)):
    where=PUBLIC+" AND (a.titulo ILIKE :q OR a.descripcion ILIKE :q) AND (CAST(:categoria AS bigint) IS NULL OR a.id_categoria=:categoria) AND coalesce(l.nombre_lugar,'Virtual') ILIKE :l AND (:m='' OR a.modalidad=:m) AND (CAST(:d AS timestamptz) IS NULL OR a.fecha_inicio>=:d) AND (NOT :disponible OR (a.estado='publicada' AND a.fecha_cierre_inscripcion>now() AND fn_cupos_disponibles(a.id_actividad)>0))"
    params=dict(q='%'+q+'%',categoria=categoria,l='%'+ubicacion+'%',m=modalidad,d=desde,disponible=disponible)
    base=" FROM actividad a JOIN organizacion o USING(id_organizacion) JOIN categoria c USING(id_categoria) LEFT JOIN ubicacion l ON l.id_ubicacion=a.id_ubicacion WHERE "+where
    return {'items':rows(c,SUMMARY+' WHERE '+where+' ORDER BY a.fecha_inicio,a.id_actividad LIMIT :limit OFFSET :offset',**params,limit=size,offset=(page-1)*size),'total':one(c,'SELECT count(*) n'+base,**params)['n'],'page':page,'size':size}


@router.get('/activities/{activity_id}')
def detail(activity_id:int,c=Depends(transaction)):
    a=dict(require(one(c,SUMMARY+' WHERE '+PUBLIC+' AND a.id_actividad=:a',a=activity_id)))
    a['habilidades']=rows(c,'SELECT ah.*,h.nombre FROM actividad_habilidad ah JOIN habilidad h USING(id_habilidad) WHERE ah.id_actividad=:a',a=activity_id)
    a['impacto']=one(c,'SELECT beneficiarios_estimados,horas_voluntariado,descripcion_impacto FROM impacto_actividad WHERE id_actividad=:a',a=activity_id)
    return a


@router.get('/organizations/{org_id}')
def organization(org_id:int,c=Depends(transaction)):
    return require(one(c,"SELECT id_organizacion,nombre,descripcion,sitio_web,logo_url FROM organizacion WHERE id_organizacion=:o AND estado_verificacion='verificada'",o=org_id))


@router.get('/certificates/{code}')
def certificate(code:str,c=Depends(transaction)):
    return require(one(c,"""SELECT v.nombres,v.apellidos,a.titulo actividad,o.nombre organizacion,ce.fecha_emision,ce.horas_certificadas,ce.codigo_verificacion
    FROM certificado ce JOIN inscripcion i USING(id_inscripcion) JOIN voluntario v USING(id_voluntario)
    JOIN actividad a USING(id_actividad) JOIN organizacion o USING(id_organizacion) WHERE ce.codigo_verificacion=:code""",code=code),'Certificado no encontrado')
