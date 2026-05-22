"""Empacota os materiais gerados num arquivo ZIP."""
import io
import zipfile


def build_zip(files: dict[str, bytes]) -> bytes:
    """Monta um ZIP. `files` mapeia nome do arquivo -> conteúdo."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()
