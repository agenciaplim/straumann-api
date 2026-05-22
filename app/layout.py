"""Carrega o layout dos templates (slots) — fonte única de posições.

Espelha o `src/data/materialTemplates.ts` do frontend: as coordenadas
dos slots são frações (0–1) do material. Lido a cada job (arquivo
pequeno), então editar o `layout.json` reflete sem reiniciar o serviço.
"""
import json

from app.config import LAYOUT_FILE


def load_layout() -> dict:
    with open(LAYOUT_FILE, encoding="utf-8") as file:
        return json.load(file)
