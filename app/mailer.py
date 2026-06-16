"""Envio de e-mail via API HTTP do Resend, com o ZIP em anexo — HTML com a marca.

Render bloqueia SMTP de saída (25/465/587), então usamos a API HTTPS do Resend.
"""
import base64
import json
import urllib.error
import urllib.request

from app.config import ASSETS_DIR, Mail

_RESEND_ENDPOINT = "https://api.resend.com/emails"
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20 MB — limite seguro de anexo
_LOGO_PATH = ASSETS_DIR / "email" / "logo-neodent.png"
_BRAND = "#631961"


def send_materials_email(to_address: str, zip_bytes: bytes) -> None:
    """Envia o e-mail (HTML + texto) com o ZIP dos materiais em anexo, via Resend.

    Sem link de download: o arquivo vai só como anexo, porque o servidor
    de produção não persiste o ZIP e o link quebraria depois do envio.
    Lança exceção em caso de falha — quem chama decide o que fazer
    (a geração não é bloqueada por falha de e-mail).
    """
    if not Mail.is_configured():
        raise RuntimeError("RESEND_API_KEY não configurada")

    attached = len(zip_bytes) <= _MAX_ATTACHMENT_BYTES

    payload = {
        "from": Mail.from_address,
        "to": [to_address],
        "subject": "Seus materiais — Studio Neodent",
        "text": _plain_body(attached),
        "html": _html_body(attached),
        "attachments": _build_attachments(zip_bytes, attached),
    }

    request = urllib.request.Request(
        _RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {Mail.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    except urllib.error.HTTPError as error:
        # Corpo da resposta traz o motivo (remetente não verificado, key inválida…).
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"Resend {error.code}: {detail}") from error


def _build_attachments(zip_bytes: bytes, attached: bool) -> list:
    """Anexos do e-mail: o logo inline (cid:logo) e, se couber, o ZIP.

    O Resend recebe o conteúdo em base64. ZIP acima do limite não vai anexado —
    sem link de fallback, o e-mail apenas avisa (caso raro)."""
    attachments = []

    # Logo inline referenciado por cid:logo no HTML. Sem o arquivo, o HTML
    # apenas mostra o alt text — não quebra o envio.
    try:
        logo = _LOGO_PATH.read_bytes()
    except OSError:
        logo = None
    if logo is not None:
        attachments.append(
            {
                "filename": "logo-neodent.png",
                "content": base64.b64encode(logo).decode("ascii"),
                "content_type": "image/png",
                "content_id": "logo",
            }
        )

    if attached:
        attachments.append(
            {
                "filename": "materiais-studio-neodent.zip",
                "content": base64.b64encode(zip_bytes).decode("ascii"),
                "content_type": "application/zip",
            }
        )

    return attachments


def _plain_body(attached: bool) -> str:
    body = (
        "Seus materiais personalizados do Studio Neodent estão prontos e estão "
        "anexados a este e-mail no arquivo materiais-studio-neodent.zip."
        if attached
        else "Seus materiais foram gerados, mas o arquivo ficou grande demais para "
        "anexar ao e-mail. Acesse o Studio Neodent para baixá-lo."
    )
    return f"Olá!\n\n{body}\n\nStudio Neodent — Para sorrir com a vida."


def _html_body(attached: bool) -> str:
    if attached:
        # Aviso + "chip" branco com o nome do anexo (apenas informativo, sem link).
        body_html = (
            '<p style="margin:0 0 28px;font-size:15px;line-height:1.6;color:#e7d6e6;">'
            "Ol&aacute;! Seus materiais personalizados do Studio Neodent foram gerados "
            'com sucesso e est&atilde;o <strong style="color:#ffffff;">anexados a este '
            "e-mail</strong> no arquivo .zip abaixo.</p>"
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center"><tr>'
            '<td align="center" bgcolor="#ffffff" '
            f'style="border-radius:10px;padding:14px 28px;font-size:15px;font-weight:700;color:{_BRAND};'
            'font-family:Arial,Helvetica,sans-serif;">&#128206;&nbsp;&nbsp;materiais-studio-neodent.zip</td>'
            "</tr></table>"
            '<p style="margin:26px 0 0;font-size:12px;line-height:1.5;color:#d9bdd8;">'
            "Procure o anexo .zip neste e-mail para baixar todos os seus materiais.</p>"
        )
    else:
        body_html = (
            '<p style="margin:0;font-size:15px;line-height:1.6;color:#e7d6e6;">'
            "Ol&aacute;! Seus materiais foram gerados, mas o arquivo ficou grande demais "
            "para anexar ao e-mail. Acesse o Studio Neodent para baix&aacute;-lo.</p>"
        )
    # E-mail HTML: layout em tabela + estilos inline (compatível com Gmail/Outlook).
    # Header branco com o logo, miolo roxo com a mensagem/anexo, rodapé branco.
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
{body_html}
</td></tr>
<tr><td align="center" style="padding:26px 36px 32px;background:#ffffff;">
<p style="margin:0 0 4px;font-size:14px;font-weight:700;color:{_BRAND};">Studio Neodent</p>
<p style="margin:0;font-size:12px;color:#a99aa8;">Para sorrir com a vida.</p>
</td></tr>
</table>
<p style="margin:16px 0 0;font-size:11px;color:#b3aeb2;font-family:Arial,Helvetica,sans-serif;">Voc&ecirc; recebeu este e-mail porque gerou materiais no Studio Neodent.</p>
</td></tr></table></body></html>"""
