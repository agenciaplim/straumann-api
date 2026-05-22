"""Rotas HTTP da API."""
import json

from flask import Blueprint, jsonify, request, send_file

from app.config import STORAGE_DIR
from app.jobs import create_job, get_job

bp = Blueprint("api", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@bp.post("/jobs")
def post_job():
    """Cria um job de geração — multipart: campo `data` (JSON) + `logo` (arquivo).

    Responde com o jobId e gera em background.
    """
    try:
        payload = json.loads(request.form.get("data") or "{}")
    except json.JSONDecodeError:
        return jsonify({"error": "Campo 'data' inválido"}), 400

    # A logo vem como arquivo binário — sem inflar como base64.
    logo_file = request.files.get("logo")
    if logo_file is not None and logo_file.filename:
        payload["logo"] = logo_file.read()
        payload["logoName"] = logo_file.filename

    if not payload.get("email"):
        return jsonify({"error": "Campo 'email' é obrigatório"}), 400
    if not payload.get("logo") and not payload.get("nome"):
        return jsonify({"error": "Envie uma logo ou um nome"}), 400

    job_id = create_job(payload)
    return jsonify({"jobId": job_id}), 202


@bp.get("/jobs/<job_id>")
def job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        return jsonify({"error": "Job não encontrado"}), 404
    return jsonify(job)


@bp.get("/download/<job_id>")
def download(job_id: str):
    zip_path = STORAGE_DIR / f"{job_id}.zip"
    if not zip_path.exists():
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_file(
        zip_path,
        as_attachment=True,
        download_name="materiais-studio-neodent.zip",
        mimetype="application/zip",
    )
