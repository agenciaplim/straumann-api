"""Envio de e-mail (SMTP) com o ZIP dos materiais — versão HTML com a marca."""
import smtplib
from email.message import EmailMessage

from app.config import ASSETS_DIR, Smtp

_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20 MB — limite seguro de anexo
_LOGO_PATH = ASSETS_DIR / "email" / "logo-neodent.png"
_BRAND = "#631961"


def send_materials_email(to_address: str, zip_bytes: bytes, download_url: str) -> None:
    """Envia o e-mail (HTML + texto) com o link de download e o ZIP anexo.

    Lança exceção em caso de falha — quem chama decide o que fazer
    (a geração não é bloqueada por falha de e-mail).
    """
    if not Smtp.is_configured():
        raise RuntimeError("SMTP não configurado")

    attached = len(zip_bytes) <= _MAX_ATTACHMENT_BYTES

    message = EmailMessage()
    message["Subject"] = "Seus materiais — Studio Neodent"
    message["From"] = f"{Smtp.from_name} <{Smtp.user}>"
    message["To"] = to_address

    # Texto puro (fallback) + HTML; o logo entra inline (cid:logo) na parte HTML.
    message.set_content(_plain_body(download_url, attached))
    message.add_alternative(_html_body(download_url, attached), subtype="html")
    _embed_logo(message)

    # ZIP grande não vai como anexo — o link de download cobre o caso.
    if attached:
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


def _embed_logo(message: EmailMessage) -> None:
    """Anexa o logo inline (cid:logo) à parte HTML, se o arquivo existir.
    Sem o arquivo, o HTML simplesmente mostra o alt text — não quebra o envio."""
    try:
        logo = _LOGO_PATH.read_bytes()
    except OSError:
        return
    html_part = message.get_payload()[1]  # [0]=texto, [1]=html
    html_part.add_related(logo, maintype="image", subtype="png", cid="<logo>")


def _plain_body(download_url: str, attached: bool) -> str:
    extra = (
        "O arquivo .zip também está anexado a este e-mail."
        if attached
        else "Seu arquivo é grande — use o link acima para baixar."
    )
    return (
        "Olá!\n\n"
        "Seus materiais personalizados do Studio Neodent estão prontos.\n\n"
        f"Baixe aqui: {download_url}\n\n"
        f"{extra}\n\n"
        "Studio Neodent — Para sorrir com a vida."
    )


def _html_body(download_url: str, attached: bool) -> str:
    attach_note = (
        "O arquivo .zip também está anexado a este e-mail."
        if attached
        else "Seu arquivo é grande — use o botão acima para baixar."
    )
    # E-mail HTML: layout em tabela + estilos inline (compatível com Gmail/Outlook).
    # Header branco com o logo, miolo roxo com o botão, rodapé branco.
    return f"""<!doctype html>
<html lang="pt-BR"><body style="margin:0;padding:0;background:#f5f4f2;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f5f4f2;font-family:Arial,Helvetica,sans-serif;">
<tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:100%;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 6px 28px rgba(99,25,97,0.12);">
<tr><td align="center" style="padding:34px 24px 30px;background:#ffffff;">
<img src="cid:logo" alt="Neodent" width="190" style="display:block;border:0;outline:none;width:190px;max-width:55%;height:auto;"/>
</td></tr>
<tr><td align="center" style="background:{_BRAND};padding:46px 36px;">
<h1 style="margin:0 0 12px;font-size:25px;line-height:1.25;color:#ffffff;font-weight:700;">Seus materiais est&atilde;o prontos! &#127881;</h1>
<p style="margin:0 0 30px;font-size:15px;line-height:1.6;color:#e7d6e6;">Ol&aacute;! Seus materiais personalizados do Studio Neodent foram gerados com sucesso e j&aacute; est&atilde;o prontos para download.</p>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr>
<td align="center" bgcolor="#ffffff" style="border-radius:10px;">
<a href="{download_url}" style="display:inline-block;padding:16px 34px;font-size:16px;font-weight:700;color:{_BRAND};text-decoration:none;border-radius:10px;font-family:Arial,Helvetica,sans-serif;">&#11015;&nbsp;&nbsp;Baixar meus materiais (.zip)</a>
</td></tr></table>
<p style="margin:24px 0 0;font-size:12px;line-height:1.5;color:#d9bdd8;">Se o bot&atilde;o n&atilde;o funcionar, copie e cole no navegador:<br><span style="color:#ffffff;word-break:break-all;">{download_url}</span></p>
</td></tr>
<tr><td align="center" style="padding:26px 36px 8px;background:#ffffff;">
<p style="margin:0;font-size:13px;line-height:1.6;color:#8a8a8a;">{attach_note}</p>
</td></tr>
<tr><td align="center" style="padding:16px 36px 32px;background:#ffffff;">
<p style="margin:0 0 4px;font-size:14px;font-weight:700;color:{_BRAND};">Studio Neodent</p>
<p style="margin:0;font-size:12px;color:#a99aa8;">Para sorrir com a vida.</p>
</td></tr>
</table>
<p style="margin:16px 0 0;font-size:11px;color:#b3aeb2;font-family:Arial,Helvetica,sans-serif;">Voc&ecirc; recebeu este e-mail porque gerou materiais no Studio Neodent.</p>
</td></tr></table></body></html>"""
