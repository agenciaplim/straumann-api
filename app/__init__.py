"""Studio Neodent — API de geração de materiais."""
from flask import Flask
from flask_cors import CORS

from app.routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(bp)
    return app
