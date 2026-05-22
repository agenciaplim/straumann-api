"""Registro e execução assíncrona dos jobs de geração.

Estado mantido em memória — suficiente para o protótipo. Para produção
com múltiplos processos, trocar por um store persistente (Redis/DB).
"""
import threading
import traceback
import uuid

from app.config import PUBLIC_URL, STORAGE_DIR
from app.generation import run_generation
from app.mailer import send_materials_email

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


def create_job(payload: dict) -> str:
    """Registra um job e dispara a geração em background."""
    job_id = uuid.uuid4().hex
    with _lock:
        _jobs[job_id] = {
            "status": "pendente",
            "downloadUrl": None,
            "emailSent": False,
            "message": "",
        }
    threading.Thread(target=_process, args=(job_id, payload), daemon=True).start()
    return job_id


def get_job(job_id: str) -> dict | None:
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job is not None else None


def _update(job_id: str, **fields) -> None:
    with _lock:
        if job_id in _jobs:
            _jobs[job_id].update(fields)


def _process(job_id: str, payload: dict) -> None:
    _update(job_id, status="processando")
    try:
        zip_bytes = run_generation(payload)
        (STORAGE_DIR / f"{job_id}.zip").write_bytes(zip_bytes)
        download_url = f"{PUBLIC_URL}/download/{job_id}"

        # E-mail é best-effort: uma falha aqui NÃO impede o download.
        email_sent = _try_send_email(payload.get("email", ""), zip_bytes, download_url)

        _update(job_id, status="concluido", downloadUrl=download_url, emailSent=email_sent)
    except Exception as error:
        # Qualquer falha na geração marca o job como erro.
        traceback.print_exc()
        _update(job_id, status="erro", message=str(error))


def _try_send_email(email: str, zip_bytes: bytes, download_url: str) -> bool:
    if not email:
        return False
    try:
        send_materials_email(email, zip_bytes, download_url)
        return True
    except Exception:
        # Best-effort: registra e segue — o download continua disponível.
        traceback.print_exc()
        return False
