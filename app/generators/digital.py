"""Geração de materiais digitais (PNG) — composição com Pillow."""
import io

from PIL import Image, ImageDraw, ImageFont

from app.config import FONTS_DIR, TEMPLATES_DIR
from app.generators.base import SlotBox, fit_contain, slot_box

_FONT_FILE = FONTS_DIR / "LeagueSpartan.ttf"


def render_digital(template: dict, brand: dict) -> bytes:
    """Compõe um material digital. A cor escolhida (`brand['cor']`) troca
    a arte inteira pela variante; o conteúdo é a logo OU nome+telefone."""
    variant = _variant(template, brand.get("cor", "white"))
    canvas = Image.open(TEMPLATES_DIR / variant["src"]).convert("RGBA")
    width, height = canvas.size
    text_color = _hex_to_rgba(variant.get("textColor", "#ffffff"))
    has_logo = brand.get("logo") is not None

    for slot in template["slots"]:
        box = slot_box(slot, width, height)
        kind = slot["kind"]
        if kind == "logo" and has_logo:
            _place_logo(canvas, brand["logo"], box, slot.get("align", "start"))
        elif kind in ("name", "phone") and not has_logo and brand.get(kind):
            _place_text(canvas, brand[kind], box, slot, width, text_color)

    out = io.BytesIO()
    canvas.convert("RGB").save(out, format="PNG")
    return out.getvalue()


def _variant(template: dict, cor: str) -> dict:
    """Seleciona a variante de cor; cai na branca se a cor for inválida."""
    variants = template["variants"]
    return variants.get(cor) or variants.get("white") or next(iter(variants.values()))


def _hex_to_rgba(value: str) -> tuple[int, int, int, int]:
    hex_value = value.lstrip("#")
    red, green, blue = (int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
    return (red, green, blue, 255)


def _align_offset(align: str, outer: int, inner: int) -> int:
    """Deslocamento horizontal do conteúdo dentro da largura do slot."""
    if align == "center":
        return (outer - inner) // 2
    if align == "end":
        return outer - inner
    return 0


def _place_logo(canvas: Image.Image, logo: Image.Image, box: SlotBox, align: str) -> None:
    fitted = fit_contain(logo, box.w, box.h)
    x = box.x + _align_offset(align, box.w, fitted.width)
    y = box.y + (box.h - fitted.height) // 2
    canvas.alpha_composite(fitted, (x, y))


def _place_text(
    canvas: Image.Image,
    text: str,
    box: SlotBox,
    slot: dict,
    width: int,
    color: tuple[int, int, int, int],
) -> None:
    font = _load_font(round(slot.get("fontScale", 0.03) * width))
    draw = ImageDraw.Draw(canvas)

    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = box.x + _align_offset(slot.get("align", "start"), box.w, right - left) - left
    y = box.y + (box.h - (bottom - top)) // 2 - top
    draw.text((x, y), text, font=font, fill=color)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(_FONT_FILE), size)
    # League Spartan é fonte variável — fixa o peso em Bold.
    try:
        font.set_variation_by_axes([700])
    except OSError:
        pass
    return font
