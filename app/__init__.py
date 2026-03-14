"""
Dating App MVP — рекомендательный сервис в формате dating (MongoDB).
"""
import logging
import os
from datetime import datetime, timedelta
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

    # Публичный чат под картой — без CSRF, чтобы POST с JSON работал стабильно
    from app.api.map_chat import map_chat_post
    csrf.exempt(map_chat_post)

    @app.context_processor
    def inject_version_and_stats():
        from flask_login import current_user
        version_file = os.path.join(os.path.dirname(app.root_path), "VERSION")
        try:
            with open(version_file, encoding="utf-8") as f:
                version = f.read().strip() or "0.0.0"
        except OSError:
            version = "0.0.0"
        stats_total = 0
        stats_real = 0
        stats_online = 0
        try:
            db = get_db(app.config)
            stats_total = db.users.count_documents({})
        except Exception:
            pass
        try:
            db = get_db(app.config)
            real_name = "Сальто"
            n = db.profiles.count_documents({"name": real_name})
            stats_real = n
        except Exception:
            pass
        try:
            db = get_db(app.config)
            since = datetime.utcnow() - timedelta(minutes=15)
            stats_online = db.users.count_documents({"last_seen": {"$gte": since}})
        except Exception:
            pass
        header_user_name = None
        header_user_balance = None
        header_last_match_id = None
        header_last_match_label = None
        if current_user.is_authenticated:
            profile = current_user.profile if hasattr(current_user, "profile") else None
            header_user_name = (getattr(profile, "name", None) or "").strip() or "Вы"
            try:
                from app.db import oid
                db = get_db(app.config)
                my_oid = oid(current_user.id)
                user_doc = db.users.find_one({"_id": my_oid}, {"balance": 1})
                header_user_balance = user_doc.get("balance", 100) if user_doc else 100
                match = db.matches.find_one(
                    {"$or": [{"user1_id": my_oid}, {"user2_id": my_oid}]},
                    sort=[("created_at", -1)],
                    projection={"user1_id": 1, "user2_id": 1, "_id": 1},
                )
                if match:
                    header_last_match_id = str(match["_id"])
                    other_id = match["user2_id"] if match["user1_id"] == my_oid else match["user1_id"]
                    from app.models.profile import get_profile_by_user_id
                    other = get_profile_by_user_id(db, other_id)
                    header_last_match_label = (other or {}).get("name") or "Чат"
            except Exception:
                pass
        return {
            "app_version": version,
            "release_time": release_time,
            "total_users": stats_total,
            "stats_total": stats_total,
            "stats_real": stats_real,
            "stats_online": stats_online,
            "header_user_name": header_user_name,
            "header_user_balance": header_user_balance,
            "header_last_match_id": header_last_match_id,
            "header_last_match_label": header_last_match_label,
        }

    @app.after_request
    def update_last_seen(response):
        from flask_login import current_user
        if current_user.is_authenticated:
            try:
                from app.db import oid
                get_db(app.config).users.update_one(
                    {"_id": oid(current_user.id)},
                    {"$set": {"last_seen": datetime.utcnow()}},
                )
            except Exception:
                pass
        return response

    app.logger.info("App created: %s", config_name)
    return app
