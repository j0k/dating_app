import logging
from datetime import datetime, time

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db
from app.models.profile import profile_to_dict, update_profile, get_profile_by_user_id

logger = logging.getLogger(__name__)


def _parse_date(s):
    if not s:
        return None
    if isinstance(s, datetime):
        return s.date() if hasattr(s, "date") else s
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


@api_bp.route("/me/profile", methods=["GET", "POST"])
@login_required
def my_profile():
    from flask import current_app
    db = get_db(current_app.config)
    profile_doc = get_profile_by_user_id(db, current_user.id)
    if not profile_doc:
        return {"error": "Profile not found"}, 404
    if request.method == "GET":
        return profile_to_dict(profile_doc)
    data = request.get_json() or {}
    if isinstance(data, list):
        data = {}
    updates = {}
    if "name" in data and data["name"] is not None:
        updates["name"] = str(data["name"])[:100]
    if "birth_date" in data:
        d = _parse_date(data["birth_date"])
        # MongoDB/BSON принимает только datetime, не date
        updates["birth_date"] = datetime.combine(d, time.min) if d else None
    if "gender" in data:
        v = data["gender"]
        updates["gender"] = str(v) if v in ("male", "female", "other") else None
    if "about" in data:
        updates["about"] = str(data["about"])[:2000] if data["about"] else None
    if "interests" in data:
        raw = data["interests"]
        updates["interests"] = [s.strip() for s in str(raw).split(",") if s.strip()] if raw else []
    if "city" in data:
        updates["city"] = str(data["city"])[:100] if data["city"] else None
    if "is_visible" in data:
        updates["is_visible"] = bool(data["is_visible"])
    if "lat" in data:
        try:
            v = data["lat"]
            updates["lat"] = float(v) if v is not None else None
        except (TypeError, ValueError):
            updates["lat"] = None
    if "lon" in data:
        try:
            v = data["lon"]
            updates["lon"] = float(v) if v is not None else None
        except (TypeError, ValueError):
            updates["lon"] = None
    _GOALS = ("serious", "dating", "friendship", "open", "unsure")
    if "relationship_goal" in data:
        v = data["relationship_goal"]
        updates["relationship_goal"] = v if v in _GOALS else None
    _TYPES = ("monogamous", "polyamorous", "any")
    if "relationship_type" in data:
        v = data["relationship_type"]
        updates["relationship_type"] = v if v in _TYPES else None
    if not updates:
        return profile_to_dict(profile_doc)
    updated = update_profile(db, current_user.id, **updates)
    logger.info("Profile updated: user_id=%s", current_user.id)
    return profile_to_dict(updated) if updated else profile_to_dict(profile_doc)
