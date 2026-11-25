import hashlib
import secrets
from fastapi import HTTPException
from backend.app.db import one, execute
from backend.app.services.mail import send_account_mail
from backend.app.security.session import passwords


def issue_token(c,user,purpose):
    token=secrets.token_urlsafe(48)
    execute(c,'UPDATE token_cuenta SET fecha_uso=now() WHERE id_usuario=:u AND tipo=:t AND fecha_uso IS NULL',u=user['id_usuario'],t=purpose)
    execute(c,"INSERT INTO token_cuenta(id_usuario,tipo,token_hash,fecha_expiracion) VALUES(:u,:t,:h,now()+interval '30 minutes')",u=user['id_usuario'],t=purpose,h=hashlib.sha256(token.encode()).hexdigest())
    send_account_mail(user['correo'],token,purpose)


def consume_token(c,token,purpose):
    # Bloqueo del usuario antes del token: orden consistente para reset/verificación.
    user=one(c,"SELECT u.* FROM usuario u JOIN token_cuenta t USING(id_usuario) WHERE t.token_hash=:h AND t.tipo=:t FOR UPDATE OF u",h=hashlib.sha256(token.encode()).hexdigest(),t=purpose)
    if not user:
        raise HTTPException(400,'Enlace inválido o vencido')
    row=one(c,"UPDATE token_cuenta SET fecha_uso=now() WHERE token_hash=:h AND tipo=:t AND fecha_uso IS NULL AND fecha_expiracion>now() RETURNING id_token",h=hashlib.sha256(token.encode()).hexdigest(),t=purpose)
    if not row:
        raise HTTPException(400,'Enlace inválido o vencido')
    return user


def update_password(c,user_id,password):
    execute(c,'UPDATE usuario SET clave_hash=:h,fecha_actualizacion=clock_timestamp() WHERE id_usuario=:u',h=passwords.hash(password),u=user_id)
    execute(c,'UPDATE token_cuenta SET fecha_uso=now() WHERE id_usuario=:u AND fecha_uso IS NULL',u=user_id)
