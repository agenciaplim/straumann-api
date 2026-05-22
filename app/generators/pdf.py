"""Geração de materiais impressos (PDF) — logo no template + CMYK.

Reescrita enxuta da lógica comprovada do `neodent-pdf`. Depende dos PDFs
de template em `assets/templates/print/` e das entradas correspondentes
no `layout.json` — entregues pelo cliente posteriormente.
"""
import io
import subprocess
import uuid

import fitz  # PyMuPDF

from app.config import STORAGE_DIR, TEMPLATES_DIR
from app.generators.base import fit_contain, slot_box

# A logo é rasterizada nesta resolução (qualidade de gráfica).
_PRINT_DPI = 300
_POINTS_PER_INCH = 72


def render_print(template: dict, brand: dict) -> bytes:
    """Insere a logo no PDF do template e devolve o PDF convertido em CMYK."""
    document = fitz.open(TEMPLATES_DIR / template["src"])
    page = document[0]

    if brand.get("logo") is not None:
        for slot in template["slots"]:
            if slot["kind"] == "logo":
                _insert_logo(page, brand["logo"], slot, page.rect.width, page.rect.height)

    rgb_pdf = document.tobytes()
    document.close()
    return _to_cmyk(rgb_pdf)


def _insert_logo(page, logo, slot: dict, page_w: float, page_h: float) -> None:
    # O slot é resolvido em pontos do PDF; a logo é rasterizada a 300 DPI.
    box = slot_box(slot, round(page_w), round(page_h))
    scale = _PRINT_DPI / _POINTS_PER_INCH
    fitted = fit_contain(logo, round(box.w * scale), round(box.h * scale))

    stream = io.BytesIO()
    fitted.save(stream, format="PNG")

    draw_w = fitted.width / scale
    draw_h = fitted.height / scale
    x = box.x + (box.w - draw_w) / 2
    y = box.y + (box.h - draw_h) / 2
    page.insert_image(fitz.Rect(x, y, x + draw_w, y + draw_h), stream=stream.getvalue())


def _to_cmyk(pdf_bytes: bytes) -> bytes:
    """Converte o PDF para CMYK (perfil de impressão) via Ghostscript."""
    src = STORAGE_DIR / f"gs_src_{uuid.uuid4().hex}.pdf"
    dst = STORAGE_DIR / f"gs_cmyk_{uuid.uuid4().hex}.pdf"
    src.write_bytes(pdf_bytes)
    try:
        result = subprocess.run(
            [
                "gs", "-dSAFER", "-dBATCH", "-dNOPAUSE",
                "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/prepress",
                "-dColorConversionStrategy=/CMYK",
                "-dProcessColorModel=/DeviceCMYK",
                f"-sOutputFile={dst}", str(src),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Ghostscript falhou: {result.stderr}")
        return dst.read_bytes()
    finally:
        src.unlink(missing_ok=True)
        dst.unlink(missing_ok=True)
