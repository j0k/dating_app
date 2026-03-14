import logging
from datetime import datetime
from bson import ObjectId

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db, oid
from app.models.user import get_user_by_id

logger = logging.getLogger(__name__)


def _ensure_match(db, user_id: ObjectId, other_id: ObjectId) -> dict | None:
    u1, u2 = (user_id, other_id) if user_id < other_id else (other_id, user_id)
    match = db.matches.find_one({"user1_id": u1, "user2_id": u2})
    if match:
        return match
    reverse = db.likes.find_one({
        "from_user_id": other_id,
        "to_user_id": user_id,
        "is_like": True,
    })
    if reverse:
        r = db.matches.insert_one({
            "user1_id": u1,
            "user2_id": u2,
            "created_at": datetime.utcnow(),
        })
        logger.info("New match: %s and %s", u1, u2)
        return db.matches.find_one({"_id": r.inserted_id})
    return None


@api_bp.route("/like", methods=["POST"])
@login_required
def like():
    data = request.get_json() or {}
    to_user_id = data.get("to_user_id")
    is_like = data.get("is_like", True)
    if to_user_id is None:
        return {"error": "to_user_id required"}, 400
    try:
        to_oid = oid(to_user_id)
    except Exception:
        return {"error": "to_user_id must be valid id"}, 400
    from flask import current_app
    db = get_db(current_app.config)
    my_oid = oid(current_user.id)
    if to_oid == my_oid:
        return {"error": "Cannot like yourself"}, 400
    if not db.users.find_one({"_id": to_oid}):
        return {"error": "User not found"}, 404
    existing = db.likes.find_one({"from_user_id": my_oid, "to_user_id": to_oid})
    if existing:
        return {"error": "Already reacted", "is_like": existing.get("is_like")}, 409
    db.likes.insert_one({
        "from_user_id": my_oid,
        "to_user_id": to_oid,
        "is_like": bool(is_like),
        "created_at": datetime.utcnow(),
    })
    new_match = None
    if is_like:
        new_match = _ensure_match(db, my_oid, to_oid)
    logger.info("Like: from=%s to=%s is_like=%s", current_user.id, to_user_id, is_like)
    return {
        "ok": True,
        "is_like": is_like,
        "new_match": new_match is not None,
        "match_id": str(new_match["_id"]) if new_match else None,
    }
