import logging
from datetime import datetime

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db, oid
from app.models.profile import get_profile_by_user_id

logger = logging.getLogger(__name__)


@api_bp.route("/announcements", methods=["GET"])
def list_announcements():
    """Список объявлений для доски (последние 50). Без авторизации."""
    from flask import current_app
    db = get_db(current_app.config)
    limit = min(int(request.args.get("limit", 50)), 100)
    cursor = db.announcements.find().sort("created_at", -1).limit(limit)
    items = []
    for a in cursor:
        items.append({
            "id": str(a["_id"]),
            "user_id": str(a["user_id"]),
            "author_name": a.get("author_name", ""),
            "title": a.get("title", ""),
            "body": a.get("body", ""),
            "created_at": a["created_at"].isoformat() if a.get("created_at") else None,
        })
    return {"announcements": items}


@api_bp.route("/announcements", methods=["POST"])
@login_required
def create_announcement():
    """Создать объявление. JSON: title, body."""
    from flask import current_app
    db = get_db(current_app.config)
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()[:200]
    body = (data.get("body") or "").strip()[:2000]
    if not title:
        return {"error": "title required"}, 400
    profile = get_profile_by_user_id(db, current_user.id)
    author_name = (profile.get("name") or current_user.email or "Пользователь")[:100]
    doc = {
        "user_id": oid(current_user.id),
        "author_name": author_name,
        "title": title,
        "body": body,
        "created_at": datetime.utcnow(),
    }
    r = db.announcements.insert_one(doc)
    logger.info("Announcement created: user_id=%s", current_user.id)
    return {
        "id": str(r.inserted_id),
        "author_name": author_name,
        "title": title,
        "body": body,
        "created_at": doc["created_at"].isoformat(),
    }
