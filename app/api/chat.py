import logging
from datetime import datetime, timezone
from bson import ObjectId

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db, oid

logger = logging.getLogger(__name__)

TYPING_TTL_SECONDS = 8


def _user_in_match(match: dict, user_oid: ObjectId) -> bool:
    return user_oid in (match["user1_id"], match["user2_id"])


def _other_user_id(match: dict, my_oid: ObjectId) -> ObjectId:
    return match["user2_id"] if match["user1_id"] == my_oid else match["user1_id"]


@api_bp.route("/matches/<match_id>/messages", methods=["GET"])
@login_required
def get_messages(match_id):
    from flask import current_app
    db = get_db(current_app.config)
    try:
        match_oid = oid(match_id)
    except Exception:
        return {"error": "Match not found"}, 404
    match = db.matches.find_one({"_id": match_oid})
    if not match or not _user_in_match(match, oid(current_user.id)):
        return {"error": "Match not found"}, 404
    my_oid = oid(current_user.id)
    since = request.args.get("since_id")
    q = {"match_id": match_oid}
    if since:
        try:
            q["_id"] = {"$gt": oid(since)}
        except Exception:
            pass
    messages = list(db.messages.find(q).sort("_id", 1))
    now = datetime.now(timezone.utc)
    for m in messages:
        if m["sender_id"] != my_oid and not m.get("read_at"):
            db.messages.update_one({"_id": m["_id"]}, {"$set": {"read_at": now}})
            m["read_at"] = now
    other_oid = _other_user_id(match, my_oid)
    typing_doc = db.typing.find_one({"match_id": match_oid, "user_id": other_oid})
    other_typing = False
    if typing_doc and typing_doc.get("updated_at"):
        from datetime import timedelta
        t = typing_doc["updated_at"]
        t_utc = t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t
        if (now - t_utc) <= timedelta(seconds=TYPING_TTL_SECONDS):
            other_typing = True
    return {
        "messages": [
            {
                "id": str(m["_id"]),
                "sender_id": str(m["sender_id"]),
                "body": m["body"],
                "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
                "is_mine": m["sender_id"] == my_oid,
                "read_at": m["read_at"].isoformat() if m.get("read_at") else None,
            }
            for m in messages
        ],
        "other_typing": other_typing,
    }


@api_bp.route("/matches/<match_id>/messages", methods=["POST"])
@login_required
def send_message(match_id):
    from flask import current_app
    db = get_db(current_app.config)
    try:
        match_oid = oid(match_id)
    except Exception:
        return {"error": "Match not found"}, 404
    match = db.matches.find_one({"_id": match_oid})
    if not match or not _user_in_match(match, oid(current_user.id)):
        return {"error": "Match not found"}, 404
    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    if not body or len(body) > 2000:
        return {"error": "body required, max 2000 chars"}, 400
    now = datetime.utcnow()
    r = db.messages.insert_one({
        "match_id": match_oid,
        "sender_id": oid(current_user.id),
        "body": body,
        "created_at": now,
        "read_at": None,
    })
    logger.info("Message sent: match_id=%s from=%s", match_id, current_user.id)
    return {
        "id": str(r.inserted_id),
        "sender_id": current_user.id,
        "body": body,
        "created_at": now.isoformat(),
        "is_mine": True,
        "read_at": None,
    }


@api_bp.route("/matches/<match_id>/typing", methods=["POST"])
@login_required
def set_typing(match_id):
    """Сообщить, что пользователь печатает (для индикатора «печатает…»)."""
    from flask import current_app
    db = get_db(current_app.config)
    try:
        match_oid = oid(match_id)
    except Exception:
        return {"error": "Match not found"}, 404
    match = db.matches.find_one({"_id": match_oid})
    if not match or not _user_in_match(match, oid(current_user.id)):
        return {"error": "Match not found"}, 404
    now = datetime.now(timezone.utc)
    db.typing.update_one(
        {"match_id": match_oid, "user_id": oid(current_user.id)},
        {"$set": {"match_id": match_oid, "user_id": oid(current_user.id), "updated_at": now}},
        upsert=True,
    )
    return {"ok": True}
