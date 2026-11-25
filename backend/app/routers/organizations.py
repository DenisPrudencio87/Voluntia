from fastapi import APIRouter,Depends,HTTPException,UploadFile,File,Form,Query
from backend.app.db import transaction,one,rows,execute
from backend.app.security.session import verified_user
from backend.app.schemas.domain import Organization,Membership
from backend.app.services.domain import member,require,location,audit
from backend.app.services.storage import validate_file,put_object,download

router=APIRouter(prefix='/organization',tags=['Organizaciones'])


@router.get('')
def mine(c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    return rows(c,"SELECT o.*,m.cargo FROM organizacion o JOIN organizacion_miembro m USING(id_organizacion) WHERE m.id_usuario=:u AND m.estado='activo' ORDER BY o.id_organizacion",u=user['id_usuario'])


@router.post('',status_code=201)
def create(data:Organization,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    values=data.model_dump(exclude={'ubicacion'})
    values['id_ubicacion']=location(c,data.ubicacion)
    org=one(c,'INSERT INTO organizacion(nombre,descripcion,correo_contacto,telefono,sitio_web,logo_url,id_ubicacion) VALUES(:nombre,:descripcion,:correo_contacto,:telefono,:sitio_web,:logo_url,:id_ubicacion) RETURNING *',**values)
    execute(c,"INSERT INTO organizacion_miembro(id_organizacion,id_usuario,cargo) VALUES(:o,:u,'administrador')",o=org['id_organizacion'],u=user['id_usuario'])
    execute(c,"INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre='organizacion' ON CONFLICT(id_usuario,id_rol) DO UPDATE SET activo=true",u=user['id_usuario'])
    audit(c,user,'organizacion_creada','organizacion',org['id_organizacion'])
    return org


@router.get('/{org_id}')
def get_org(org_id:int,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id,allow_suspended=True)
    result=dict(require(one(c,'SELECT * FROM organizacion WHERE id_organizacion=:o',o=org_id)))
    result['estadisticas']=one(c,'SELECT * FROM fn_estadisticas_organizacion(:o)',o=org_id)
    result['ubicacion']=one(c,'SELECT * FROM ubicacion WHERE id_ubicacion=:u',u=result['id_ubicacion']) if result['id_ubicacion'] else None
    result['revisiones']=rows(c,"SELECT accion,detalle,fecha_evento FROM bitacora_evento WHERE entidad='organizacion' AND id_registro=:o AND accion='revision_organizacion' ORDER BY id_evento DESC LIMIT 10",o=org_id)
    return result


@router.put('/{org_id}')
def update(org_id:int,data:Organization,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id,admin=True)
    values=data.model_dump(exclude={'ubicacion'})
    values['id_ubicacion']=location(c,data.ubicacion)
    execute(c,'UPDATE organizacion SET nombre=:nombre,descripcion=:descripcion,correo_contacto=:correo_contacto,telefono=:telefono,sitio_web=:sitio_web,logo_url=:logo_url,id_ubicacion=:id_ubicacion WHERE id_organizacion=:o',o=org_id,**values)
    audit(c,user,'perfil_organizacion','organizacion',org_id)
    return {'mensaje':'Organización actualizada'}


@router.get('/{org_id}/members')
def members(org_id:int,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id,admin=True)
    return rows(c,'SELECT m.*,u.correo FROM organizacion_miembro m JOIN usuario u USING(id_usuario) WHERE m.id_organizacion=:o ORDER BY m.id_usuario',o=org_id)


@router.put('/{org_id}/members')
def save_member(org_id:int,data:Membership,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    # Serializa cambios de miembros para proteger al último administrador.
    require(one(c,'SELECT id_organizacion FROM organizacion WHERE id_organizacion=:o FOR UPDATE',o=org_id))
    member(c,user,org_id,admin=True)
    target=require(one(c,"SELECT id_usuario FROM usuario WHERE correo=:e AND estado='activo' AND email_verificado",e=str(data.correo).lower()),'La cuenta debe existir, estar activa y verificada')
    existing=one(c,'SELECT cargo,estado FROM organizacion_miembro WHERE id_organizacion=:o AND id_usuario=:u',o=org_id,u=target['id_usuario'])
    if existing and existing['cargo']=='administrador' and existing['estado']=='activo' and (data.cargo!='administrador' or data.estado!='activo'):
        if one(c,"SELECT count(*) n FROM organizacion_miembro m JOIN usuario u USING(id_usuario) WHERE m.id_organizacion=:o AND m.cargo='administrador' AND m.estado='activo' AND u.estado='activo'",o=org_id)['n']<=1:
            raise HTTPException(409,'No puedes retirar al último administrador activo')
    execute(c,'INSERT INTO organizacion_miembro(id_organizacion,id_usuario,cargo,estado) VALUES(:o,:u,:cargo,:estado) ON CONFLICT(id_organizacion,id_usuario) DO UPDATE SET cargo=excluded.cargo,estado=excluded.estado',o=org_id,u=target['id_usuario'],cargo=data.cargo,estado=data.estado)
    execute(c,"INSERT INTO usuario_rol(id_usuario,id_rol) SELECT :u,id_rol FROM rol WHERE nombre='organizacion' ON CONFLICT(id_usuario,id_rol) DO UPDATE SET activo=true",u=target['id_usuario'])
    audit(c,user,'miembro_actualizado','organizacion',org_id)
    return {'mensaje':'Membresía actualizada'}


@router.get('/{org_id}/documents')
def documents(org_id:int,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id)
    return rows(c,'SELECT id_documento,tipo_documento,numero_documento,estado_revision,fecha_subida,fecha_revision FROM documento_organizacion WHERE id_organizacion=:o ORDER BY id_documento DESC',o=org_id)


@router.post('/{org_id}/documents',status_code=201)
def upload_document(org_id:int,tipo_documento:str=Form(min_length=2,max_length=80),numero_documento:str=Form(min_length=2,max_length=80),file:UploadFile=File(),c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    require(one(c,'SELECT id_organizacion FROM organizacion WHERE id_organizacion=:o FOR UPDATE',o=org_id))
    member(c,user,org_id,admin=True)
    content,ext,mime=validate_file(file.file.read(10*1024*1024+1),file.content_type,only_pdf=True)
    key=put_object(content,'documents',org_id,ext,mime)
    document=one(c,'INSERT INTO documento_organizacion(id_organizacion,tipo_documento,numero_documento,archivo_url) VALUES(:o,:t,:n,:k) RETURNING id_documento',o=org_id,t=tipo_documento,n=numero_documento,k=key)
    execute(c,"UPDATE organizacion SET estado_verificacion='pendiente' WHERE id_organizacion=:o AND estado_verificacion='rechazada'",o=org_id)
    audit(c,user,'documento_subido','organizacion',org_id)
    return document


@router.get('/{org_id}/documents/{doc_id}/file')
def document_file(org_id:int,doc_id:int,c=Depends(transaction, scope="function"),user=Depends(verified_user, scope="function")):
    member(c,user,org_id)
    doc=require(one(c,'SELECT archivo_url FROM documento_organizacion WHERE id_documento=:d AND id_organizacion=:o',d=doc_id,o=org_id))
    return download(doc['archivo_url'])
