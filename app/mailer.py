"""Envio de e-mail (SMTP) com o ZIP dos materiais."""
import smtplib
from email.message import EmailMessage

from app.config import Smtp

_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20 MB — limite seguro de anexo


def send_materials_email(to_address: str, zip_bytes: bytes, download_url: str) -> None:
    """Envia o e-mail com o link de download e o ZIP anexo (se couber).

    Lança exceção em caso de falha — quem chama decide o que fazer
    (a geração não é bloqueada por falha de e-mail).
    """
    if not Smtp.is_configured():
        raise RuntimeError("SMTP não configurado")

    message = EmailMessage()
    message["Subject"] = "Seus materiais — Studio Neodent"
    message["From"] = f"{Smtp.from_name} <{Smtp.user}>"
    message["To"] = to_address
    message.set_content(
        "Olá!\n\n"
        "Seus materiais personalizados estão prontos.\n"
        f"Baixe aqui: {download_url}\n\n"
        "Studio Neodent"
    )

    # ZIP grande não vai como anexo — o link de download cobre o caso.
    if len(zip_bytes) <= _MAX_ATTACHMENT_BYTES:
        message.add_attachment(
            zip_bytes,
            maintype="application",
            subtype="zip",
            filename="materiais-studio-neodent.zip",
        )

    with smtplib.SMTP(Smtp.host, Smtp.port, timeout=30) as server:
        if Smtp.use_tls:
            server.starttls()
        server.login(Smtp.user, Smtp.password)
        server.send_message(message)
