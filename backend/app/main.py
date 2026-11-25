from pathlib import Path
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError
from backend.app.config import settings
from backend.app.db import transaction, one
from backend.app.routers import auth
from backend.app.security.session import SAFE_METHODS, valid_csrf

app=FastAPI(title='Voluntia API',version='1.0.0',description='Voluntariado y trazabilidad de participación. Autenticación por cookie HttpOnly y CSRF.')
app.include_router(auth.router,prefix='/api/v1')


@app.middleware('http')
async def security_headers(request:Request,call_next):
    if request.method not in SAFE_METHODS:
        origin=request.headers.get('origin','')
        csrf=request.cookies.get('voluntia_csrf','')
        if origin!=settings.public_base_url.rstrip('/') or not valid_csrf(csrf) or request.headers.get('x-csrf-token')!=csrf:
            return JSONResponse(status_code=403,content={'detail':'Solicitud no autorizada (origen o CSRF)'})
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    if not request.url.path.startswith(('/docs','/openapi.json','/redoc')):
        response.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if settings.app_env in ('demo','production'):
        response.headers['Strict-Transport-Security']='max-age=31536000'
    response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'no-cache'
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    return JSONResponse(status_code=422,content={'detail':'Revisa los campos enviados','campos':[{'campo':'.'.join(str(x) for x in e['loc'][1:]),'mensaje':e['msg']} for e in exc.errors()]})


@app.exception_handler(DBAPIError)
async def database_error(request,exc):
    state=getattr(exc.orig,'sqlstate','')
    status=409 if state in ('23505','23514','23503','40001','40P01') else 403 if state=='42501' else 503
    message='La operación entra en conflicto con los datos o las reglas de negocio' if status==409 else 'Operación no permitida' if status==403 else 'Servicio de datos temporalmente no disponible'
    return JSONResponse(status_code=status,content={'detail':message})


@app.get('/api/health',tags=['Operación'])
def health():
    return {'status':'ok','service':'voluntia'}


@app.get('/api/ready',tags=['Operación'])
def ready():
    try:
        from backend.app.db import engine
        with engine.connect() as c:
            if one(c,'SELECT count(*) n FROM rol')['n']!=3:
                raise RuntimeError()
        return {'status':'ready'}
    except Exception:
        return JSONResponse(status_code=503,content={'status':'not_ready'})
