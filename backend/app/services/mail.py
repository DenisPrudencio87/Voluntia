import smtplib
from email.message import EmailMessage
from fastapi import HTTPException
from backend.app.config import settings


def send_account_mail(correo,token,purpose):
    if settings.email_mode!='smtp':
        raise HTTPException(503,'El correo está deshabilitado en esta demostración')
    message=EmailMessage()
    message['From']=settings.smtp_from
    message['To']=correo
    message['Subject']='Voluntia: verifica tu correo' if purpose=='verificar_email' else 'Voluntia: recupera tu contraseña'
    path='verificar' if purpose=='verificar_email' else 'recuperar'
    message.set_content(f'Abre el enlace para continuar:\n{settings.public_base_url}/{path}?token={token}\nEl enlace es privado, expira y solo puede usarse una vez. Si no lo solicitaste, ignora este mensaje.')
    try:
        with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as smtp:
            if settings.smtp_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user,settings.smtp_password)
            smtp.send_message(message)
    except (OSError,smtplib.SMTPException):
        raise HTTPException(503,'No se pudo enviar el correo. Intenta de nuevo más tarde.') from None
