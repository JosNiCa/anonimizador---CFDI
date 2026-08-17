from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO


class OCRProvider(ABC):
    @abstractmethod
    def extract(self, pdf: bytes) -> list[str]: ...


def extract_pdf(pdf: bytes) -> tuple[list[str], dict[str, str]]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf), strict=True)
    if reader.is_encrypted:
        raise ValueError("ENCRYPTED_PDF")
    pages = [(page.extract_text() or "") for page in reader.pages]
    if not any(page.strip() for page in pages):
        raise ValueError("SCANNED_OR_IMAGE_PDF:OCR_REQUIRED")
    metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items()}
    for page in reader.pages:
        if "/Annots" in page or "/AA" in page:
            # Nunca se copian, pero se informa para auditoría.
            metadata["removedInteractiveObjects"] = "true"
    return pages, metadata


def render_clean_pdf(pages: list[str], label: str) -> bytes:
    """Reconstruye páginas nuevas: nunca copia streams, XMP, formularios o adjuntos originales."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen.canvas import Canvas

    output = BytesIO(); canvas = Canvas(output, pagesize=letter, pageCompression=1)
    width, height = letter
    canvas.setAuthor("CFDI Dataset Sanitizer"); canvas.setTitle("Documento sanitizado para dataset")
    for page in pages:
        y = height - 42; canvas.setFont("Helvetica", 8)
        for original_line in page.splitlines():
            for line in _wrap(original_line, width - 64, 8, stringWidth):
                if y < 42:
                    _footer(canvas, label, width); canvas.showPage(); canvas.setFont("Helvetica", 8); y = height - 42
                canvas.drawString(32, y, line); y -= 11
        _footer(canvas, label, width); canvas.showPage()
    canvas.save(); return output.getvalue()


def _wrap(line: str, max_width: float, size: int, measure) -> list[str]:
    if not line: return [""]
    words = line.split(); rows: list[str] = []; current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and measure(candidate, "Helvetica", size) > max_width:
            rows.append(current); current = word
        else: current = candidate
    rows.append(current); return rows


def _footer(canvas, label: str, width: float) -> None:
    canvas.saveState(); canvas.setFont("Helvetica-Bold", 7); canvas.drawCentredString(width / 2, 18, label); canvas.restoreState()

