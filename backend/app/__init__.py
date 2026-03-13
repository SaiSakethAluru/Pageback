import os

from flask import Flask
from flask_cors import CORS

from app.routes.books import books_bp
from app.routes.positions import positions_bp
from app.routes.recap import recap_bp
from config import Config


def create_app() -> Flask:
    Config.validate()

    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.FLASK_SECRET_KEY

    allowed_origins = ["http://localhost:5173"]
    production_frontend_url = os.getenv("FRONTEND_URL")
    if production_frontend_url:
        allowed_origins.append(production_frontend_url)

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    app.register_blueprint(books_bp)
    app.register_blueprint(positions_bp)
    app.register_blueprint(recap_bp)

    return app
