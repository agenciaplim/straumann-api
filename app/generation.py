"""Orquestra a geração: layout → geradores → ZIP."""
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
    requested = payload.get("materiais") or list(templates.keys())

    files: dict[str, bytes] = {}
    for template_id in requested:
        template = templates.get(template_id)
        if template is not None:
            files[f"{template_id}.{extension}"] = render(template, brand)

    if not files:
        raise ValueError("Nenhum material válido para gerar")

    return build_zip(files)
