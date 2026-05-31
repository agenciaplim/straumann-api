"""Orquestra a geração: layout → geradores → ZIP."""
import os
import re

from app.generators.base import decode_logo
from app.generators.digital import render_digital
from app.generators.pdf import render_print
from app.layout import load_layout
from app.packaging import build_zip

# Tipo do material → (renderizador, seção do layout, extensão do arquivo).
_PIPELINES = {
    "digital": (render_digital, "digital", "png"),
    "impresso": (render_print, "print", "pdf"),
}


def run_generation(payload: dict) -> bytes:
    """Gera os materiais pedidos e devolve o ZIP. Levanta exceção em erro."""
    tipo = payload.get("tipo", "digital")
    if tipo not in _PIPELINES:
        raise ValueError(f"Tipo inválido: {tipo}")

    render, layout_key, extension = _PIPELINES[tipo]
    templates = load_layout().get(layout_key, {})

    brand = {
        "logo": (
            decode_logo(payload["logo"], payload.get("logoName", ""))
            if payload.get("logo")
            else None
        ),
        "name": payload.get("nome", ""),
        "phone": payload.get("telefone", ""),
        "cor": payload.get("cor", "white"),
    }

    # Sem materiais específicos, gera todos os templates do tipo.
    # Para impressos, filtra pela cor escolhida (brand → v1, white → v3).
    requested = payload.get("materiais") or [
        tid for tid, tpl in templates.items()
        if tpl.get("cor") is None or tpl["cor"] == brand["cor"]
    ]

    files: dict[str, bytes] = {}
    for template_id in requested:
        template = templates.get(template_id)
        if template is not None:
            files[_zip_path(template_id, template, extension)] = render(template, brand)

    if not files:
        raise ValueError("Nenhum material válido para gerar")

    return build_zip(files)


def _zip_path(template_id: str, template: dict, extension: str) -> str:
    """Nome do arquivo no ZIP entregue ao cliente — limpo, sem detalhes internos.

    Impresso → `impressos/<material>.pdf` (some o v1/v3; só sai a cor escolhida).
    Digital  → post simples: `digital/<post>.png`;
               carrossel:    `digital/<post>/post-NN.png` (uma pasta por carrossel).
    """
    # Print tem `src` no topo; digital guarda o src dentro das variantes de cor.
    src = template.get("src") or next(iter(template["variants"].values()))["src"]
    folder = os.path.dirname(src)  # impressos/display | digital/post-08

    # Impresso: o nome do material é a própria pasta — vira o arquivo final.
    if "variants" not in template:
        return f"{folder}.{extension}"  # impressos/display.pdf

    # Digital: carrossel (post-NN-tela-M) separa cada tela como post-MM dentro da
    # pasta do carrossel; post de peça única vai plano em digital/.
    tela = re.search(r"tela-(\d+)", template_id)
    if tela:
        return f"{folder}/post-{int(tela.group(1)):02d}.{extension}"  # digital/post-08/post-01.png
    return f"{folder}.{extension}"  # digital/post-01.png
