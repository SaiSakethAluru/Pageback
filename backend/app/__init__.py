from flask import Flask
from flask_cors import CORS

from app.routes.auth import auth_bp
from app.routes.books import books_bp
from app.routes.positions import positions_bp
from app.routes.recap import recap_bp
from config import Config


def create_app() -> Flask:
    Config.validate()

    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.FLASK_SECRET_KEY
    app.config.update(
        SESSION_COOKIE_NAME=Config.SESSION_COOKIE_NAME,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=Config.SESSION_COOKIE_SAMESITE,
        SESSION_COOKIE_SECURE=Config.SESSION_COOKIE_SECURE,
    )

    allowed_origins = [Config.FRONTEND_URL]

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(positions_bp)
    app.register_blueprint(recap_bp)

    return app
