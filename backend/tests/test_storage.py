import io
from datetime import datetime, timezone
import httpx
import pytest
from fastapi import HTTPException
from PIL import Image
from backend.app.services.storage import validate_file, put_object, download
from backend.app.services.certificates import certificate_pdf


def test_file_signatures_size_and_reencoding():
    for data, mime in [
        (b"fake", "application/pdf"),
        (b"fake", "image/jpeg"),
        (b"x" * (10 * 1024 * 1024 + 1), "application/pdf"),
    ]:
        with pytest.raises(HTTPException):
            validate_file(data, mime)
    image = Image.new("RGB", (10, 10), "green")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    content, ext, mime = validate_file(buffer.getvalue(), "image/png")
    assert content.startswith(b"\xff\xd8") and ext == "jpg" and mime == "image/jpeg"


def test_supabase_adapter_contract_and_failure(monkeypatch):
    from backend.app.config import settings

    monkeypatch.setattr(settings, "storage_backend", "supabase")
    monkeypatch.setattr(settings, "supabase_url", "https://storage.invalid")
    monkeypatch.setattr(
        settings, "supabase_service_role_key", "unit-test-key-not-a-real-secret"
    )
    requests = []

    def handler(request):
        requests.append(request)
        assert (
            request.headers["authorization"] == "Bearer unit-test-key-not-a-real-secret"
        )
        if "/object/sign/" in str(request.url):
            return httpx.Response(
                200,
                json={
                    "signedURL": "/object/sign/voluntia-demo-private/certificates/1/test.pdf?token=ficticio"
                },
            )
        return httpx.Response(200, json={"Key": "ficticio"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        monkeypatch.setattr(httpx, "post", client.post)
        key = put_object(b"pdf ficticio", "certificates", 1, "pdf", "application/pdf")
        response = download(key)
        assert (
            response.status_code == 303
            and "token=ficticio" in response.headers["location"]
        )
        assert requests[0].headers["x-upsert"] == "false"

    def failure(*args, **kwargs):
        raise httpx.ConnectError("fallo de prueba")

    monkeypatch.setattr(httpx, "post", failure)
    with pytest.raises(HTTPException) as error:
        put_object(b"pdf ficticio", "certificates", 1, "pdf", "application/pdf")
    assert error.value.status_code == 503


def test_certificate_long_values_fit_one_page():
    from pypdf import PdfReader

    content = certificate_pdf(
        "Nombre " * 30,
        "Actividad " * 18,
        "Organización " * 12,
        2,
        "a" * 40,
        datetime.now(timezone.utc),
    )
    assert len(PdfReader(io.BytesIO(content)).pages) == 1
