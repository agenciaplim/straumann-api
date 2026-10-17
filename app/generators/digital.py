"""Geração de materiais digitais (PNG) — composição com Pillow."""
import io

from PIL import Image, ImageDraw, ImageFont

from app.config import FONTS_DIR, TEMPLATES_DIR
from app.generators.base import SlotBox, fit_contain, slot_box

_FONT_FILE = FONTS_DIR / "LeagueSpartan.ttf"


def render_digital(template: dict, brand: dict) -> bytes:
    """Compõe um material digital. A cor escolhida (`brand['cor']`) troca
    a arte inteira pela variante; o conteúdo é a logo OU nome+contato."""
    cor = brand.get("cor", "white")
    variant = _variant(template, cor)
    canvas = Image.open(TEMPLATES_DIR / variant["src"]).convert("RGBA")
    width, height = canvas.size
    text_color = _hex_to_rgba(variant.get("textColor", "#ffffff"))
    has_logo = brand.get("logo") is not None

    if cor == "brand":
        # Faixa inferior de background preto Straumann ampliada (18% da altura)
        band_h = int(height * 0.18)
        band_y = height - band_h
        band = Image.new("RGBA", (width, band_h), (0, 0, 0, 0))
        draw_band = ImageDraw.Draw(band)
        for y in range(band_h):
            ratio = y / band_h
            if ratio < 0.2:
                alpha = int(255 * 0.7 * (ratio / 0.2))
            elif ratio < 0.5:
                alpha = int(255 * (0.7 + 0.3 * ((ratio - 0.2) / 0.3)))
            else:
                alpha = 255
            draw_band.line([(0, y), (width, y)], fill=(20, 23, 22, alpha))
        canvas.alpha_composite(band, (0, band_y))

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
    """Renderiza o bloco de contato: label 'Entre em contato' + badge com telefone.

    Espelha o box model do front (MaterialPreview.vue):
      • label numa caixa de line-height 1.5 (herdado do body, --leading-normal)
        → dá a folga que impede o label de "colar" no badge;
      • badge com line-height 1 (= 1em) + padding vertical → pill com respiro;
      • label e dígitos centrados verticalmente nas suas caixas.
    """
    label_text = "Entre em contato"
    label_em = round(slot.get("fontScaleLabel", 0.025) * width)
    badge_em = round(slot.get("fontScaleBadge", 0.0285) * width)
    label_font = _load_font(label_em)
    badge_font = _load_font(badge_em)
    gap    = round(slot.get("gapScale",  0.007) * width)
    pad_h  = round(slot.get("padHScale", 0.036) * width)
    pad_v  = round(slot.get("padVScale", 0.0085) * width)

    draw = ImageDraw.Draw(canvas)

    # Caixas de linha, iguais ao CSS: label = 1.5em; badge = 1em + 2·pad_v.
    label_line_h = round(slot.get("labelLineHeight", 1.5) * label_em)
    badge_h = badge_em + 2 * pad_v

    lx0, ly0, lx1, ly1 = draw.textbbox((0, 0), label_text, font=label_font)
    label_w = lx1 - lx0

    # Largura do pill pelo texto real (com parênteses); a referência vertical
    # dos dígitos ("0123456789") ignora o descendente dos parênteses, senão os
    # números "sobem" no pill.
    bx0, _, bx1, _ = draw.textbbox((0, 0), phone, font=badge_font)
    badge_w = (bx1 - bx0) + 2 * pad_h
    dy0, dy1 = draw.textbbox((0, 0), "0123456789", font=badge_font)[1::2]

    total_h = label_line_h + gap + badge_h
    v_start = box.y + (box.h - total_h) // 2

    # Bloco alinhado na caixa (default end → encosta na borda direita,
    # espelhando o logo à esquerda); a label fica CENTRADA sobre o badge, não
    # sobre a caixa (senão vai pro canto). Vertical sempre centrada.
    align = slot.get("align", "end")
    badge_x = box.x + _align_offset(align, box.w, badge_w)

    # Label — centrada sobre o badge (H), centrada na linha (V).
    label_cy = v_start + label_line_h / 2
    label_x = badge_x + (badge_w - label_w) / 2
    draw.text(
        (round(label_x - lx0), round(label_cy - (ly0 + ly1) / 2)),
        label_text,
        font=label_font,
        fill=color,
    )

    # Badge (pill) — contorno com anti-aliasing (ver _draw_pill).
    badge_y = v_start + label_line_h + gap
    border_w = max(1, round(0.0025 * width))
    _draw_pill(canvas, badge_x, badge_y, badge_w, badge_h, color, border_w)
    # Dígitos centrados verticalmente no pill.
    digit_cy = badge_y + badge_h / 2
    draw.text(
        (badge_x + pad_h - bx0, round(digit_cy - (dy0 + dy1) / 2)),
        phone,
        font=badge_font,
        fill=color,
    )


def _draw_pill(
    canvas: Image.Image,
    x: int,
    y: int,
    w: int,
    h: int,
    color: tuple[int, int, int, int],
    border_w: int,
    ss: int = 4,
) -> None:
    """Desenha o contorno arredondado do badge com anti-aliasing.

    `ImageDraw.rounded_rectangle` não suaviza os cantos → serrilhado. Renderiza
    o contorno numa tile `ss`× maior e reduz com LANCZOS (supersampling)."""
    tile = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle(
        [0, 0, w * ss - 1, h * ss - 1],
        radius=h * ss // 2,
        outline=color,
        width=max(1, border_w * ss),
    )
    canvas.alpha_composite(tile.resize((w, h), Image.Resampling.LANCZOS), (x, y))


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(_FONT_FILE), size)
    # League Spartan é fonte variável — fixa o peso em Bold.
    try:
        font.set_variation_by_axes([700])
    except OSError:
        pass
    return font
