"""Rotas HTTP da API."""
import io
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

    # Fallback seguro para email e identificação
    if not payload.get("email"):
        payload["email"] = "materiais@straumann.com"
    if not payload.get("logo") and not payload.get("nome"):
        payload["nome"] = ""

    job_id = create_job(payload)
    return jsonify({"jobId": job_id}), 202


@bp.get("/jobs/<job_id>")
def job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        return jsonify({"error": "Job não encontrado"}), 404
    return jsonify(job)


@bp.get("/download/<path:job_id>")
def download(job_id: str):
    clean_id = job_id.removesuffix(".zip")
    zip_path = STORAGE_DIR / f"{clean_id}.zip"

    # Se o arquivo já existe no disco efêmero, entrega diretamente
    if zip_path.exists():
        return send_file(
            zip_path,
            as_attachment=True,
            download_name="materiais-studio-straumann.zip",
            mimetype="application/zip",
        )

    # Fallback resiliente: gera dinamicamente sob demanda caso o job tenha expirado ou seja pacote padrão
    try:
        from app.generation import run_generation

        payload = {
            "tipo": request.args.get("tipo", "digital"),
            "cor": request.args.get("cor", "brand"),
            "nome": request.args.get("nome", ""),
            "telefone": request.args.get("telefone", ""),
            "email": request.args.get("email", "materiais@straumann.com"),
        }
        zip_bytes = run_generation(payload)

        try:
            STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            zip_path.write_bytes(zip_bytes)
        except Exception:
            pass

        return send_file(
            io.BytesIO(zip_bytes),
            as_attachment=True,
            download_name="materiais-studio-straumann.zip",
            mimetype="application/zip",
        )
    except Exception as error:
        return jsonify({"error": "Erro ao gerar arquivo para download", "details": str(error)}), 500
