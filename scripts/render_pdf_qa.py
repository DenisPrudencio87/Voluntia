"""QA local de rúbrica y certificado, sin cambiar el PDF original."""

from pathlib import Path
from datetime import datetime, timezone
import pymupdf
from backend.app.services.certificates import certificate_pdf

root = Path(".local/pdf-qa")
root.mkdir(parents=True, exist_ok=True)
for idx, page in enumerate(pymupdf.open("docs/RUBRICA.pdf")):
    page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3)).save(
        root / f"rubrica-{idx + 1}.png"
    )
content = certificate_pdf(
    "María Alejandra Ejemplo Ficticio",
    "Jornada comunitaria de educación y cuidado del ambiente",
    "Organización Manos que Transforman (ficticia)",
    2,
    "a" * 40,
    datetime.now(timezone.utc),
)
(root / "certificado.pdf").write_bytes(content)
document = pymupdf.open(stream=content, filetype="pdf")
assert len(document) == 1
document[0].get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(root / "certificado.png")
print(
    "Renderizadas 3 páginas de rúbrica y 1 certificado ficticio para QA visual local."
)
