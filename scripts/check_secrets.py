"""Chequeo conservador de patrones en archivos versionados; nunca imprime valores."""

import re
import subprocess
from pathlib import Path

patterns = [
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{25,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"sb_secret_[A-Za-z0-9_-]{25,}"),
]
files = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
hits = []
for name in files:
    if not name or name.endswith((".pdf", ".ico", ".png", ".jpg", ".woff", ".woff2")):
        continue
    p = Path(name)
    if not p.is_file():
        continue
    for line_number, line in enumerate(p.read_bytes().splitlines(), 1):
        if any(pattern.search(line) for pattern in patterns):
            hits.append(f"{name}:{line_number}")
if hits:
    raise SystemExit("Revisar posibles secretos (valores ocultos): " + ", ".join(hits))
print(
    "Sin patrones de clave privada/GitHub/Supabase detectados en archivos versionados. No sustituye revisión manual."
)
