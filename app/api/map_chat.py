"""
Публичный чат под картой: любой может писать. Гости — по IP, залогиненные — имя и пол.
"""
from datetime import datetime

from flask import request
from flask_login import current_user

from app.api import api_bp
from app.db import get_db


def _gender_display(gender):
    if gender == "male":
        return "♂"
    if gender == "female":
        return "♀"
    if gender == "other":
        return "Небинарный"
    return ""


@api_bp.route("/map-chat", methods=["GET"])
def map_chat_list():
    """Список сообщений чата под картой (последние сверху)."""
    from flask import current_app
    db = get_db(current_app.config)
    limit = min(int(request.args.get("limit", 50)), 100)
    cursor = db.map_chat.find({}).sort("created_at", -1).limit(limit)
    messages = []
    for m in cursor:
        messages.append({
            "id": str(m["_id"]),
            "text": m.get("text", ""),
            "author": m.get("author_display", "Гость"),
            "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
        })
    return {"messages": messages}


@api_bp.route("/map-chat", methods=["POST"])
def map_chat_post():
    """Отправить сообщение. Без авторизации — подпись по IP, с авторизацией — имя и пол."""
    from flask import current_app
    db = get_db(current_app.config)
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    if not text or len(text) > 2000:
        return {"error": "Текст от 1 до 2000 символов"}, 400
    if current_user.is_authenticated:
        profile = current_user.profile if hasattr(current_user, "profile") else None
        name = (getattr(profile, "name", None) or "").strip() if profile else ""
        gender = getattr(profile, "gender", "") if profile else ""
        author_display = name or "Пользователь"
        if _gender_display(gender):
            author_display += " · " + _gender_display(gender)
        doc = {
            "text": text,
            "author_type": "registered",
            "user_id": current_user.id,
            "name": name,
            "gender": gender,
            "author_display": author_display,
            "created_at": datetime.utcnow(),
        }
    else:
        ip = request.remote_addr or ""
        if request.headers.get("X-Forwarded-For"):
            ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or ip
        author_display = ip or "Гость"
        doc = {
            "text": text,
            "author_type": "guest",
            "author_ip": ip,
            "author_display": author_display,
            "created_at": datetime.utcnow(),
        }
    r = db.map_chat.insert_one(doc)
    return {
        "ok": True,
        "id": str(r.inserted_id),
        "author": doc["author_display"],
        "created_at": doc["created_at"].isoformat(),
    }
