"""
Dating App MVP — рекомендательный сервис в формате dating (MongoDB).
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from app.config import config
from app.db import get_db
from app.models import User
from app.models.user import get_user_by_id

login_manager = LoginManager()
csrf = CSRFProtect()


def setup_logging(app: Flask) -> None:
    """Настройка логирования: консоль + ротируемый файл."""
    if app.debug and not os.environ.get("FORCE_FILE_LOG"):
        return
    log_dir = os.path.join(os.path.dirname(app.root_path), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "dating_app.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s [%(filename)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging configured: %s", log_file)


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    get_db(app.config)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Войдите, чтобы продолжить."

    @login_manager.user_loader
    def load_user(user_id):
        db = get_db(app.config)
        doc = get_user_by_id(db, user_id)
        if not doc:
            return None
        from app.models.profile import get_profile_by_user_id
        profile_doc = get_profile_by_user_id(db, doc["_id"])
        return User(doc, profile_doc)

    setup_logging(app)

    from app.auth import auth_bp
    from app.main import main_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_version_and_stats():
        version_file = os.path.join(os.path.dirname(app.root_path), "VERSION")
        try:
            with open(version_file, encoding="utf-8") as f:
                version = f.read().strip() or "0.0.0"
        except OSError:
            version = "0.0.0"
        try:
            total_users = get_db(app.config).users.count_documents({})
        except Exception:
            total_users = 0
        return {"app_version": version, "total_users": total_users}

    app.logger.info("App created: %s", config_name)
    return app
