import io
import re
import secrets
from pathlib import Path
import httpx
from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader
from pypdf.generic import DictionaryObject, ArrayObject, IndirectObject, NameObject
from fastapi import HTTPException
from fastapi.responses import Response, RedirectResponse
from backend.app.config import settings

KEY_PATTERN = re.compile(
    r"^(documents|evidence|certificates)/[0-9]+/[a-f0-9]{40}\.(pdf|png|jpg|webp)$"
)


def unsafe_pdf(reader):
    """Inspecciona objetos decodificados: los nombres PDF admiten escapes #xx."""
    pending = [reader.trailer["/Root"]]
    seen = set()
    nodes = 0
    forbidden = {
        "/OpenAction",
        "/AA",
        "/JavaScript",
        "/JS",
        "/Launch",
        "/EmbeddedFiles",
        "/EmbeddedFile",
        "/RichMedia",
        "/XFA",
    }
    while pending:
        value = pending.pop()
        key = (
            ("ref", value.idnum, value.generation)
            if isinstance(value, IndirectObject)
            else ("object", id(value))
        )
        if key in seen:
            continue
        seen.add(key)
        nodes += 1
        if nodes > 50000:
            return True
        if isinstance(value, IndirectObject):
            pending.append(value.get_object())
        elif isinstance(value, DictionaryObject):
            if (
                forbidden.intersection(value.keys())
                or str(value.get("/S", ""))
                in ("/JavaScript", "/Launch", "/SubmitForm", "/ImportData", "/GoToR")
                or str(value.get("/Type", "")) == "/EmbeddedFile"
            ):
                return True
            pending.extend(value.values())
        elif isinstance(value, ArrayObject):
            pending.extend(value)
        elif isinstance(value, NameObject) and str(value) in forbidden.union(
            {"/SubmitForm", "/ImportData", "/GoToR"}
        ):
            return True
    return False


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
            if unsafe_pdf(reader):
                raise ValueError()
        except Exception:
            raise HTTPException(
                422, "PDF inválido, cifrado o con contenido activo"
            ) from None
        return content, "pdf", "application/pdf"
    if not only_pdf and content_type in ("image/jpeg", "image/png", "image/webp"):
        try:
            image = Image.open(io.BytesIO(content))
            if (
                image.format
                != {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[
                    content_type
                ]
            ):
                raise ValueError()
            if image.width * image.height > 20000000:
                raise ValueError()
            image.verify()
            image = Image.open(io.BytesIO(content)).convert("RGB")
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=88)
            if len(output.getvalue()) > limit:
                raise HTTPException(413, "Imagen procesada demasiado grande")
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
    path = (root / key).resolve()
    if not path.is_relative_to(root):
        raise HTTPException(404, "Archivo no encontrado")
    return path


def headers():
    key = settings.supabase_service_role_key
    result = {"apikey": key}
    # Las nuevas claves sb_secret_* no son JWT: Supabase rechaza su uso como Bearer.
    if not key.startswith("sb_secret_"):
        result["Authorization"] = "Bearer " + key
    return result


def put_object(content, kind, record, extension, media_type):
    key = f"{kind}/{record}/{secrets.token_hex(20)}.{extension}"
    if settings.storage_backend == "local":
        path = local_path(key)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        except OSError:
            raise HTTPException(
                503, "Almacenamiento local temporalmente no disponible"
            ) from None
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
        try:
            content = path.read_bytes()
        except OSError:
            raise HTTPException(503, "No se pudo leer el archivo privado") from None
        return Response(
            content,
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
        if (
            not isinstance(signed, str)
            or signed.split("?", 1)[0]
            != f"/object/sign/{settings.supabase_bucket}/{key}"
        ):
            raise ValueError()
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        raise HTTPException(503, "No se pudo obtener una descarga privada") from None
    return RedirectResponse(
        settings.supabase_url
        + "/storage/v1"
        + signed
        + ("&" if "?" in signed else "?")
        + "download=voluntia."
        + key.rsplit(".", 1)[1],
        status_code=303,
    )
