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
PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:3006").rstrip("/")


class Smtp:
    """Credenciais de envio de e-mail."""

    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    from_name = os.getenv("SMTP_FROM_NAME", "Studio Neodent")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.host and cls.user and cls.password)
