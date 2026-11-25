"""Smoke HTTP de archivos Docker/local, usando únicamente demo ficticia privada."""

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import httpx
from backend.app.services.certificates import certificate_pdf

base = "http://localhost:8080"
credentials = json.loads(Path(".local/demo-credentials.json").read_text())
manifest = json.loads(Path(".local/demo-manifest.json").read_text())
org_id = manifest["organizacion_verificada"]


@contextmanager
def client_for(role):
    with httpx.Client(base_url=base, headers={"Origin": base}, timeout=15) as client:
        client.get("/api/v1/auth/csrf").raise_for_status()
        client.headers["X-CSRF-Token"] = client.cookies["voluntia_csrf"]
        client.post(
            "/api/v1/auth/login",
            json={"correo": credentials[role]["correo"],"clave": credentials[role]["clave"]},
        ).raise_for_status()
        client.headers["X-CSRF-Token"] = client.cookies["voluntia_csrf"]
        yield client


with client_for("organizacion") as org:
    docs = org.get(f"/api/v1/organization/{org_id}/documents")
    docs.raise_for_status()
    assert (
        org.get(
            f"/api/v1/organization/{org_id}/documents/{docs.json()[0]['id_documento']}/file"
        ).status_code
        == 200
    )
    pdf = certificate_pdf(
        "Archivo ficticio",
        "Smoke de contenedor",
        "Voluntia demo",
        1,
        "SMOKE-LOCAL",
        datetime.now(timezone.utc),
    )
    upload = org.post(
        f"/api/v1/organization/{org_id}/documents",
        files={"file": ("ficticio.pdf", pdf, "application/pdf")},
        data={"tipo_documento": "Smoke ficticio", "numero_documento": "DEMO-SMOKE"},
    )
    upload.raise_for_status()
    document = upload.json()["id_documento"]
    assert (
        org.get(f"/api/v1/organization/{org_id}/documents/{document}/file").status_code
        == 200
    )
with client_for("admin") as admin:
    assert admin.get(f"/api/v1/admin/documents/{document}/file").status_code == 200
    admin.post(
        f"/api/v1/admin/documents/{document}/review",
        json={"estado": "aprobado", "motivo": "Documento ficticio del smoke local"},
    ).raise_for_status()
    admin.post(
        f"/api/v1/admin/organizations/{org_id}/state",
        json={
            "estado": "verificada",
            "motivo": "Restauración de estado tras smoke local",
        },
    ).raise_for_status()
assert (
    httpx.get(
        f"{base}/api/v1/organization/{org_id}/documents/{document}/file"
    ).status_code
    == 401
)
print(
    "Smoke local aprobado: archivos existentes y nuevos descargables por titular/revisión; visitante denegado. Sin credenciales en salida."
)
