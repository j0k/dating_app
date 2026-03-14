import logging
from datetime import datetime
from bson import ObjectId

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db, oid
from app.models.profile import get_profile_by_user_id

logger = logging.getLogger(__name__)

REAL_USER_NAME = "Сальто"


def _is_test_user(db, user_id: ObjectId) -> bool:
    """Тестовый пользователь = все, кроме Сальто (по имени в профиле)."""
    profile = get_profile_by_user_id(db, user_id)
    if not profile or not profile.get("name"):
        return True
    name = (profile.get("name") or "").strip()
    return name != REAL_USER_NAME


def _ensure_match(db, user_id: ObjectId, other_id: ObjectId) -> dict | None:
    u1, u2 = (user_id, other_id) if user_id < other_id else (other_id, user_id)
    match = db.matches.find_one({"user1_id": u1, "user2_id": u2})
    if match:
        return match
    if _is_test_user(db, other_id):
        reverse = True
    else:
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


SUPER_LIKE_COST = 3
DEFAULT_BALANCE = 100


@api_bp.route("/me", methods=["GET"])
@login_required
def me():
    """Баланс текущего пользователя (для суперлайков)."""
    from flask import current_app
    db = get_db(current_app.config)
    my_oid = oid(current_user.id)
    user_doc = db.users.find_one({"_id": my_oid}, {"balance": 1})
    balance = user_doc.get("balance", DEFAULT_BALANCE) if user_doc else DEFAULT_BALANCE
    return {"balance": balance, "super_like_cost": SUPER_LIKE_COST}


@api_bp.route("/like", methods=["POST"])
@login_required
def like():
    data = request.get_json() or {}
    to_user_id = data.get("to_user_id")
    is_like = data.get("is_like", True)
    is_super = bool(data.get("is_super", False))
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
        if is_like:
            if not existing.get("is_like"):
                db.likes.update_one(
                    {"from_user_id": my_oid, "to_user_id": to_oid},
                    {"$set": {"is_like": True, "is_super": is_super}},
                )
            new_match = _ensure_match(db, my_oid, to_oid)
            ud = db.users.find_one({"_id": my_oid}, {"balance": 1})
            new_balance = ud.get("balance", DEFAULT_BALANCE) if ud else DEFAULT_BALANCE
            return {
                "ok": True,
                "is_like": True,
                "is_super": bool(existing.get("is_super") or is_super),
                "new_match": new_match is not None,
                "match_id": str(new_match["_id"]) if new_match else None,
                "balance": new_balance,
            }
        return {"error": "Already reacted", "is_like": existing.get("is_like")}, 409
    if is_like and is_super:
        user_doc = db.users.find_one({"_id": my_oid}, {"balance": 1})
        balance = user_doc.get("balance", DEFAULT_BALANCE) if user_doc else DEFAULT_BALANCE
        if balance < SUPER_LIKE_COST:
            return {"error": "Недостаточно баланса для суперлайка", "balance": balance, "required": SUPER_LIKE_COST}, 400
    db.likes.insert_one({
        "from_user_id": my_oid,
        "to_user_id": to_oid,
        "is_like": bool(is_like),
        "is_super": is_super and bool(is_like),
        "created_at": datetime.utcnow(),
    })
    if is_like and is_super:
        db.users.update_one({"_id": my_oid}, {"$inc": {"balance": -SUPER_LIKE_COST}})
    new_match = None
    if is_like:
        new_match = _ensure_match(db, my_oid, to_oid)
    logger.info("Like: from=%s to=%s is_like=%s is_super=%s", current_user.id, to_user_id, is_like, is_super)
    user_doc = db.users.find_one({"_id": my_oid}, {"balance": 1})
    new_balance = user_doc.get("balance", DEFAULT_BALANCE) if user_doc else DEFAULT_BALANCE
    return {
        "ok": True,
        "is_like": is_like,
        "is_super": is_super and is_like,
        "new_match": new_match is not None,
        "match_id": str(new_match["_id"]) if new_match else None,
        "balance": new_balance,
    }


@api_bp.route("/me/liked", methods=["GET"])
@login_required
def me_liked():
    """Список пользователей, которых я лайкнул (для вкладки «Тестовая»)."""
    from flask import current_app
    from app.models.profile import get_profile_by_user_id, profile_to_dict
    db = get_db(current_app.config)
    my_oid = oid(current_user.id)
    cursor = db.likes.find(
        {"from_user_id": my_oid, "is_like": True}
    ).sort("created_at", -1)
    result = []
    for like_doc in cursor:
        other_id = like_doc["to_user_id"]
        profile_doc = get_profile_by_user_id(db, other_id)
        u1, u2 = (my_oid, other_id) if my_oid < other_id else (other_id, my_oid)
        match_doc = db.matches.find_one({"user1_id": u1, "user2_id": u2})
        result.append({
            "user_id": str(other_id),
            "profile": profile_to_dict(profile_doc) if profile_doc else None,
            "match_id": str(match_doc["_id"]) if match_doc else None,
            "created_at": like_doc.get("created_at").isoformat() if like_doc.get("created_at") else None,
        })
    return {"liked": result}
