"""Публичная статистика для шапки (зарегистрировано, реальных, онлайн)."""
from datetime import datetime, timedelta

from flask import current_app

from app.api import api_bp
from app.db import get_db


@api_bp.route("/stats", methods=["GET"])
def stats():
    """Без авторизации. Для подстановки в шапку через JS."""
    db = get_db(current_app.config)
    total = 0
    real = 0
    online = 0
    try:
        total = db.users.count_documents({})
    except Exception:
        pass
    try:
        real = db.profiles.count_documents({"name": "Сальто"})
    except Exception:
        pass
    try:
        since = datetime.utcnow() - timedelta(minutes=15)
        online = db.users.count_documents({"last_seen": {"$gte": since}})
    except Exception:
        pass
    return {"total": total, "real": real, "online": online}
