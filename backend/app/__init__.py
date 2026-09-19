from flask import Flask
from flask_cors import CORS

from app.application.errors import ApplicationError
from app.interfaces.http.errors import error_response
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

    app.url_map.strict_slashes = False

    allowed_origins = [Config.FRONTEND_URL]
    if "localhost" in Config.FRONTEND_URL:
        allowed_origins.append(Config.FRONTEND_URL.replace("localhost", "127.0.0.1"))
    elif "127.0.0.1" in Config.FRONTEND_URL:
        allowed_origins.append(Config.FRONTEND_URL.replace("127.0.0.1", "localhost"))

    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(positions_bp)
    app.register_blueprint(recap_bp)

    @app.errorhandler(ApplicationError)
    def handle_application_error(error: ApplicationError):
        return error_response(error)

    return app
