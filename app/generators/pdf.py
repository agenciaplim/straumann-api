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
    """Insere logo (ou nome como fallback) no PDF e devolve em CMYK."""
    document = fitz.open(TEMPLATES_DIR / template["src"])
    page = document[0]

    # Cor do nome = a mesma do preview no front: fundo branco → roxo da marca,
    # fundo roxo → branco. Vem do `textColor` da variante no layout.json.
    text_color = _hex_to_rgb01(template.get("textColor", "#ffffff"))

    for slot in template["slots"]:
        if slot["kind"] != "logo":
            continue
        if brand.get("logo") is not None:
            _insert_logo(page, brand["logo"], slot, page.rect.width, page.rect.height)
        elif brand.get("name"):
            _insert_name(page, brand["name"], slot, page.rect.width, page.rect.height, text_color)

    rgb_pdf = document.tobytes()
    document.close()
    return _to_cmyk(rgb_pdf)


def _hex_to_rgb01(value: str) -> tuple[float, float, float]:
    """Converte '#rrggbb' na tupla RGB 0–1 que o PyMuPDF espera."""
    hex_value = value.lstrip("#")
    return tuple(int(hex_value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _insert_logo(page, logo, slot: dict, page_w: float, page_h: float) -> None:
    # O slot é resolvido em pontos do PDF; a logo é rasterizada a 300 DPI.
    box = slot_box(slot, round(page_w), round(page_h))

    # A logo cabe no CÍRCULO do slot, não no retângulo — mesma regra do front
    # (MaterialPrintCard, --slot-h-ratio + min()): largura limitada a 80% do
    # menor lado (≈ diâmetro do círculo) e altura a 80% da altura do slot. Sem
    # isso, num slot largo a logo se estica além do círculo e transborda.
    max_w = 0.8 * min(box.w, box.h)
    max_h = 0.8 * box.h

    scale = _PRINT_DPI / _POINTS_PER_INCH
    fitted = fit_contain(logo, round(max_w * scale), round(max_h * scale))

    stream = io.BytesIO()
    fitted.save(stream, format="PNG")

    draw_w = fitted.width / scale
    draw_h = fitted.height / scale
    # Centra a logo no centro do slot (cx, cy) — igual ao posicionamento do nome.
    x = box.x + (box.w - draw_w) / 2
    y = box.y + (box.h - draw_h) / 2
    page.insert_image(fitz.Rect(x, y, x + draw_w, y + draw_h), stream=stream.getvalue())


def _insert_name(
    page, name: str, slot: dict, page_w: float, page_h: float, color: tuple
) -> None:
    """Insere o nome da clínica centralizado H+V no slot, com auto-fit de fonte."""
    box = slot_box(slot, round(page_w), round(page_h))
    font_size = max(6, round(slot.get("fontScale", 0.25) * min(box.w, box.h)))

    # Auto-fit: reduz a fonte até caber na largura do slot (margem de 8% em cada lado)
    max_text_w = box.w * 0.84
    text_w = fitz.get_text_length(name, fontname="helv", fontsize=font_size)
    if text_w > max_text_w:
        font_size = max(6, round(font_size * max_text_w / text_w))
        text_w = fitz.get_text_length(name, fontname="helv", fontsize=font_size)

    # Centralização H+V — baseline = centro da caixa + cap-height/2 (Helvetica ≈ 0.718 em)
    x = box.x + (box.w - text_w) / 2
    y = box.y + (box.h + font_size * 0.718) / 2

    page.insert_text(
        fitz.Point(x, y),
        name,
        fontname="helv",
        fontsize=font_size,
        color=color,
    )


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
