"""Geração de materiais digitais (PNG) — composição com Pillow."""
import io

from PIL import Image, ImageDraw, ImageFont

from app.config import FONTS_DIR, TEMPLATES_DIR
from app.generators.base import SlotBox, fit_contain, slot_box

_FONT_FILE = FONTS_DIR / "LeagueSpartan.ttf"


def render_digital(template: dict, brand: dict) -> bytes:
    """Compõe um material digital. A cor escolhida (`brand['cor']`) troca
    a arte inteira pela variante; o conteúdo é a logo OU nome+contato."""
    variant = _variant(template, brand.get("cor", "white"))
    canvas = Image.open(TEMPLATES_DIR / variant["src"]).convert("RGBA")
    width, height = canvas.size
    text_color = _hex_to_rgba(variant.get("textColor", "#ffffff"))
    has_logo = brand.get("logo") is not None

    for slot in template["slots"]:
        box = slot_box(slot, width, height)
        kind = slot["kind"]
        if kind == "logo" and has_logo:
            _place_logo(canvas, brand["logo"], box, slot.get("align", "center"))
        elif kind == "name" and not has_logo and brand.get("name"):
            _place_text(canvas, brand["name"], box, slot, width, text_color)
        elif kind == "contact" and brand.get("phone"):
            _place_contact(canvas, brand["phone"], box, slot, width, text_color)

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
    font = _load_font(round(slot.get("fontScale", 0.036) * width))
    draw = ImageDraw.Draw(canvas)

    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    x = box.x + _align_offset(slot.get("align", "center"), box.w, right - left) - left
    y = box.y + (box.h - (bottom - top)) // 2 - top
    draw.text((x, y), text, font=font, fill=color)


def _place_contact(
    canvas: Image.Image,
    phone: str,
    box: SlotBox,
    slot: dict,
    width: int,
    color: tuple[int, int, int, int],
) -> None:
    """Renderiza o bloco de contato: label 'Entre em contato' + badge com telefone."""
    label_text = "Entre em contato"
    label_font = _load_font(round(slot.get("fontScaleLabel", 0.023) * width))
    badge_font = _load_font(round(slot.get("fontScaleBadge", 0.027) * width))
    gap      = round(slot.get("gapScale",  0.006) * width)
    pad_h    = round(slot.get("padHScale", 0.022) * width)
    pad_v    = round(slot.get("padVScale", 0.007) * width)

    draw = ImageDraw.Draw(canvas)

    lx0, ly0, lx1, ly1 = draw.textbbox((0, 0), label_text, font=label_font)
    label_w, label_h = lx1 - lx0, ly1 - ly0

    bx0, by0, bx1, by1 = draw.textbbox((0, 0), phone, font=badge_font)
    badge_text_w, badge_text_h = bx1 - bx0, by1 - by0
    badge_w = badge_text_w + 2 * pad_h
    badge_h = badge_text_h + 2 * pad_v

    total_h = label_h + gap + badge_h
    v_start = box.y + (box.h - total_h) // 2

    # Label centralizado horizontalmente
    draw.text(
        (box.x + (box.w - label_w) // 2 - lx0, v_start - ly0),
        label_text,
        font=label_font,
        fill=color,
    )

    # Badge (pill) centralizado horizontalmente
    badge_x = box.x + (box.w - badge_w) // 2
    badge_y = v_start + label_h + gap
    radius   = badge_h // 2
    border_w = max(1, round(0.0025 * width))
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w, badge_y + badge_h],
        radius=radius,
        outline=color,
        width=border_w,
    )
    draw.text(
        (badge_x + pad_h - bx0, badge_y + pad_v - by0),
        phone,
        font=badge_font,
        fill=color,
    )


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(_FONT_FILE), size)
    # League Spartan é fonte variável — fixa o peso em Bold.
    try:
        font.set_variation_by_axes([700])
    except OSError:
        pass
    return font
