"""Primitivas comuns aos geradores: geometria de slot e decode da logo."""
import io
from dataclasses import dataclass

import cairosvg
from PIL import Image


@dataclass(frozen=True)
class SlotBox:
    """Caixa de um slot em pixels reais do material."""

    x: int
    y: int
    w: int
    h: int


def slot_box(slot: dict, width: int, height: int) -> SlotBox:
    """Converte um slot (frações 0–1) em pixels do material."""
    return SlotBox(
        x=round(slot["x"] * width),
        y=round(slot["y"] * height),
        w=round(slot["w"] * width),
        h=round(slot["h"] * height),
    )


def decode_logo(raw: bytes, filename: str = "") -> Image.Image:
    """Decodifica a logo (bytes do arquivo enviado) em imagem RGBA.
    Aceita PNG e SVG — converte SVG para raster quando necessário."""
    is_svg = filename.lower().endswith(".svg") or b"<svg" in raw[:256].lower()
    if is_svg:
        raw = cairosvg.svg2png(bytestring=raw)
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def fit_contain(image: Image.Image, max_w: int, max_h: int) -> Image.Image:
    """Redimensiona preservando a proporção para caber em max_w × max_h."""
    ratio = min(max_w / image.width, max_h / image.height)
    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    return image.resize(size, Image.Resampling.LANCZOS)
