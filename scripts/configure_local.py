"""Crea .env local una sola vez. Nunca imprime ni sobreescribe secretos."""

import argparse
import secrets
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--closed-demo", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
env = root / ".env"
if not env.exists():
    value = (
        (root / ".env.example")
        .read_text(encoding="utf-8")
        .replace("JWT_SECRET=", "JWT_SECRET=" + secrets.token_urlsafe(48))
    )
    if args.closed_demo:
        value = value.replace("EMAIL_MODE=smtp", "EMAIL_MODE=disabled").replace(
            "PUBLIC_SIGNUP_ENABLED=true", "PUBLIC_SIGNUP_ENABLED=false"
        )
    env.write_text(value, encoding="utf-8")
    print("Configuración local generada en .env ignorado. No compartir su contenido.")
else:
    print("Se conserva .env existente; no se muestran sus valores.")
