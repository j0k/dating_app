from datetime import date, datetime
from bson import ObjectId

from app.db import oid


def get_profile_by_user_id(db, user_id) -> dict | None:
    uid = user_id if isinstance(user_id, ObjectId) else oid(user_id)
    return db.profiles.find_one({"user_id": uid})


def profile_age(birth_date) -> int | None:
    if not birth_date:
        return None
    if hasattr(birth_date, "date"):
        d = birth_date.date() if callable(getattr(birth_date, "date", None)) else birth_date
    else:
        d = birth_date
    if isinstance(d, datetime):
        d = d.date()
    if not isinstance(d, date):
        return None
    today = date.today()
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))


def profile_interests_list(doc: dict) -> list:
    raw = doc.get("interests")
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not raw:
        return []
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def profile_to_dict(doc: dict) -> dict:
    """Документ профиля из MongoDB в dict для API (id, user_id как строки)."""
    user_id = doc.get("user_id")
    uid = str(user_id) if user_id is not None else ""
    birth = doc.get("birth_date")
    bd_str = None
    if birth:
        if hasattr(birth, "isoformat"):
            bd_str = birth.isoformat()[:10] if hasattr(birth, "isoformat") else str(birth)[:10]
        else:
            bd_str = str(birth)[:10]
    return {
        "id": str(doc.get("_id", "")),
        "user_id": uid,
        "name": doc.get("name", ""),
        "age": profile_age(doc.get("birth_date")),
        "birth_date": bd_str,
        "gender": doc.get("gender"),
        "about": doc.get("about"),
        "interests": profile_interests_list(doc),
        "city": doc.get("city"),
        "avatar_url": doc.get("avatar_url") or "",
        "is_visible": doc.get("is_visible", True),
        "lat": doc.get("lat"),
        "lon": doc.get("lon"),
        "relationship_goal": doc.get("relationship_goal"),
        "relationship_type": doc.get("relationship_type"),
    }


def update_profile(db, user_id, **fields) -> dict | None:
    uid = oid(user_id)
    from datetime import datetime
    fields["updated_at"] = datetime.utcnow()
    db.profiles.update_one({"user_id": uid}, {"$set": fields})
    return db.profiles.find_one({"user_id": uid})
