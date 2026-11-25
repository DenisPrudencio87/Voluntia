from pathlib import Path
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError
from backend.app.config import settings
from backend.app.db import one
from backend.app.routers import (
    auth,
    public,
    volunteers,
    organizations,
    activities,
    participation,
    admin,
)
from backend.app.security.session import SAFE_METHODS, valid_csrf
from backend.app.security.body_limit import BodyLimitMiddleware
from backend.app.security.logging import RedactAccessQuery
from alembic.config import Config
from alembic.script import ScriptDirectory

REQUIRED_REVISION = ScriptDirectory.from_config(
    Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
).get_current_head()
logging.getLogger("uvicorn.access").addFilter(RedactAccessQuery())

app = FastAPI(
    title="Voluntia API",
    version="1.0.0",
    description="Voluntariado y trazabilidad de participación. Autenticación por cookie HttpOnly y CSRF.",
)
for module in (
    auth,
    public,
    volunteers,
    organizations,
    activities,
    participation,
    admin,
):
    app.include_router(module.router, prefix="/api/v1")
app.add_middleware(BodyLimitMiddleware)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    length = request.headers.get("content-length", "0") or "0"
    if request.method not in SAFE_METHODS and (
        len(length) > 12
        or not length.isascii()
        or not length.isdigit()
        or int(length) > 11 * 1024 * 1024
    ):
        return JSONResponse(
            status_code=413, content={"detail": "Archivo demasiado grande"}
        )
    if request.method not in SAFE_METHODS:
        origin = request.headers.get("origin", "")
        csrf = request.cookies.get("voluntia_csrf", "")
        if (
            origin != settings.public_base_url.rstrip("/")
            or not valid_csrf(csrf)
            or request.headers.get("x-csrf-token") != csrf
        ):
            return JSONResponse(
                status_code=403,
                content={"detail": "Solicitud no autorizada (origen o CSRF)"},
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not request.url.path.startswith(("/docs", "/openapi.json", "/redoc")):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    if settings.app_env in ("demo", "production"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Cache-Control"] = (
        "no-store" if request.url.path.startswith("/api") else "no-cache"
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Revisa los campos enviados",
            "campos": [
                {"campo": ".".join(str(x) for x in e["loc"][1:]), "mensaje": e["msg"]}
                for e in exc.errors()
            ],
        },
    )


@app.exception_handler(DBAPIError)
async def database_error(request, exc):
    state = getattr(exc.orig, "sqlstate", "")
    diagnostic = getattr(exc.orig, "diag", None)
    logging.getLogger(__name__).error(
        "DB %s: %s", state, getattr(diagnostic, "message_primary", "unavailable")
    )
    status = (
        409
        if state in ("23505", "23514", "23503", "40001", "40P01")
        else 403
        if state == "42501"
        else 503
    )
    message = (
        "La operación entra en conflicto con los datos o las reglas de negocio"
        if status == 409
        else "Operación no permitida"
        if status == 403
        else "Servicio de datos temporalmente no disponible"
    )
    return JSONResponse(status_code=status, content={"detail": message})


@app.get("/api/health", tags=["Operación"])
def health():
    return {"status": "ok", "service": "voluntia"}


@app.get("/api/ready", tags=["Operación"])
def ready():
    try:
        from backend.app.db import engine

        with engine.connect() as c:
            state = one(
                c,
                "SELECT (SELECT count(*) FROM rol) roles,(SELECT version_num FROM public.alembic_version) revision,(SELECT count(*) FROM information_schema.tables WHERE table_schema='voluntia') tablas",
            )
            if (
                state["roles"] != 3
                or state["revision"] != REQUIRED_REVISION
                or state["tablas"] != 23
            ):
                raise RuntimeError()
        return {"status": "ready"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if path.split("/")[0] in ("api", "docs", "redoc", "openapi.json"):
        raise HTTPException(404, "Ruta no encontrada")
    root = (
        Path(__file__).resolve().parents[2]
        / "frontend"
        / "dist"
        / "voluntia-frontend"
        / "browser"
    )
    requested = (root / path).resolve()
    if not requested.is_relative_to(root.resolve()):
        raise HTTPException(404, "Ruta no encontrada")
    if requested.is_file():
        return FileResponse(requested)
    if "." in Path(path).name or not (root / "index.html").is_file():
        raise HTTPException(404, "Recurso no encontrado")
    return FileResponse(root / "index.html")
