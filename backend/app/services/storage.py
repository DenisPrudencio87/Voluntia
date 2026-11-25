import io
import re
import secrets
from pathlib import Path
import httpx
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from fastapi import HTTPException
from fastapi.responses import Response, RedirectResponse
from backend.app.config import settings

KEY_PATTERN = re.compile(
    r"^(documents|evidence|certificates)/[0-9]+/[a-f0-9]{40}\.(pdf|png|jpg|webp)$"
)


def validate_file(content, content_type, only_pdf=False):
    limit = (
        10 * 1024 * 1024
        if only_pdf or content_type == "application/pdf"
        else 5 * 1024 * 1024
    )
    if len(content) > limit:
        raise HTTPException(413, "Archivo demasiado grande")
    if content_type == "application/pdf" and content.startswith(b"%PDF-"):
        try:
            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted or not 0 < len(reader.pages) <= 100:
                raise ValueError()
            if any(
                token in content
                for token in (
                    b"/JavaScript",
                    b"/JS ",
                    b"/OpenAction",
                    b"/EmbeddedFile",
                    b"/Launch",
                )
            ):
                raise ValueError()
        except Exception:
            raise HTTPException(
                422, "PDF inválido, cifrado o con contenido activo"
            ) from None
        return content, "pdf", "application/pdf"
    if not only_pdf and content_type in ("image/jpeg", "image/png", "image/webp"):
        try:
            image = Image.open(io.BytesIO(content))
            if image.width * image.height > 20000000:
                raise ValueError()
            image.verify()
            image = Image.open(io.BytesIO(content)).convert("RGB")
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=88)
            return output.getvalue(), "jpg", "image/jpeg"
        except (
            ValueError,
            OSError,
            UnidentifiedImageError,
            Image.DecompressionBombError,
        ):
            raise HTTPException(422, "Imagen inválida") from None
    raise HTTPException(422, "Tipo o firma de archivo no admitido")


def local_path(key):
    if not KEY_PATTERN.fullmatch(key):
        raise HTTPException(404, "Archivo no encontrado")
    root = Path(settings.storage_path).resolve()
    if not root.is_relative_to(Path.cwd().resolve() / ".local"):
        raise RuntimeError("Storage local debe estar dentro de .local del proyecto")
    return root / key


def headers():
    return {
        "Authorization": "Bearer " + settings.supabase_service_role_key,
        "apikey": settings.supabase_service_role_key,
    }


def put_object(content, kind, record, extension, media_type):
    key = f"{kind}/{record}/{secrets.token_hex(20)}.{extension}"
    if settings.storage_backend == "local":
        path = local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    else:
        try:
            response = httpx.post(
                f"{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{key}",
                content=content,
                headers={**headers(), "Content-Type": media_type, "x-upsert": "false"},
                timeout=20,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(
                503, "Almacenamiento externo no disponible. Reintenta más tarde."
            ) from None
    return key


def download(key):
    if not KEY_PATTERN.fullmatch(key):
        raise HTTPException(404, "Archivo no encontrado")
    if settings.storage_backend == "local":
        path = local_path(key)
        if not path.is_file():
            raise HTTPException(404, "Archivo no encontrado")
        return Response(
            path.read_bytes(),
            media_type="application/pdf" if key.endswith(".pdf") else "image/jpeg",
            headers={
                "Content-Disposition": 'attachment; filename="voluntia.'
                + key.rsplit(".", 1)[1]
                + '"'
            },
        )
    try:
        result = httpx.post(
            f"{settings.supabase_url}/storage/v1/object/sign/{settings.supabase_bucket}/{key}",
            json={"expiresIn": 60},
            headers=headers(),
            timeout=15,
        )
        result.raise_for_status()
        signed = result.json()["signedURL"]
        if not signed.startswith("/object/sign/"):
            raise ValueError()
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(503, "No se pudo obtener una descarga privada") from None
    return RedirectResponse(
        settings.supabase_url + "/storage/v1" + signed, status_code=303
    )
