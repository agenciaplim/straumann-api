"""Configuração da aplicação — carregada do ambiente (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Em desenvolvimento, carrega o .env da raiz do repo. Em produção
# (Docker), as variáveis já vêm do ambiente — load_dotenv é inofensivo.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
TEMPLATES_DIR = ASSETS_DIR / "templates"
FONTS_DIR = ASSETS_DIR / "fonts"
STORAGE_DIR = BASE_DIR / "storage"
LAYOUT_FILE = ASSETS_DIR / "layout.json"

STORAGE_DIR.mkdir(exist_ok=True)

# URL pública — usada para montar o link de download no e-mail.
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://straumann-api.onrender.com").rstrip("/")


class Mail:
    """Envio de e-mail via API HTTP do Resend.

    Usamos API HTTP (porta 443) em vez de SMTP porque o Render bloqueia
    as portas de SMTP de saída (25/465/587).
    """

    resend_api_key = os.getenv("RESEND_API_KEY", "")
    # Remetente oficial Studio Straumann
    from_address = os.getenv("MAIL_FROM", "Studio Straumann <onboarding@resend.dev>")

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.resend_api_key)
