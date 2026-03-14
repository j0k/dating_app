import logging
from bson import ObjectId

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db, oid
from app.models.profile import get_profile_by_user_id, profile_to_dict

logger = logging.getLogger(__name__)


@api_bp.route("/matches", methods=["GET"])
@login_required
def matches():
    from flask import current_app
    db = get_db(current_app.config)
    my_oid = oid(current_user.id)
    cursor = db.matches.find({
        "$or": [{"user1_id": my_oid}, {"user2_id": my_oid}]
    }).sort("created_at", -1)
    result = []
    for m in cursor:
        other_id = m["user2_id"] if m["user1_id"] == my_oid else m["user1_id"]
        profile_doc = get_profile_by_user_id(db, other_id)
        result.append({
            "match_id": str(m["_id"]),
            "user_id": str(other_id),
            "profile": profile_to_dict(profile_doc) if profile_doc else None,
            "created_at": m["created_at"].isoformat() if m.get("created_at") else None,
        })
    return {"matches": result}


@api_bp.route("/matches/<match_id>", methods=["GET"])
@login_required
def match_detail(match_id):
    from flask import current_app
    db = get_db(current_app.config)
    try:
        match_oid = oid(match_id)
    except Exception:
        return {"error": "Match not found"}, 404
    match = db.matches.find_one({"_id": match_oid})
    if not match:
        return {"error": "Match not found"}, 404
    my_oid = oid(current_user.id)
    if my_oid not in (match["user1_id"], match["user2_id"]):
        return {"error": "Forbidden"}, 403
    other_id = match["user2_id"] if match["user1_id"] == my_oid else match["user1_id"]
    profile_doc = get_profile_by_user_id(db, other_id)
    return {
        "match_id": str(match["_id"]),
        "user_id": str(other_id),
        "profile": profile_to_dict(profile_doc) if profile_doc else None,
    }
