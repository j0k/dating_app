"""
Пользователи с указанной позицией на карте (для OpenStreetMap).
"""
from app.api import api_bp
from app.db import get_db
from app.models.profile import profile_age, profile_interests_list


def _gender_display(gender):
    if gender == "male":
        return "♂"
    if gender == "female":
        return "♀"
    if gender == "other":
        return "Небинарный"
    return ""


@api_bp.route("/map-users", methods=["GET"])
def map_users():
    """Список профилей с координатами (lat, lon) для отображения на карте. Публичный."""
    from flask import current_app
    db = get_db(current_app.config)
    cursor = db.profiles.find(
        {"lat": {"$exists": True, "$ne": None}, "lon": {"$exists": True, "$ne": None}},
        {"user_id": 1, "name": 1, "city": 1, "lat": 1, "lon": 1, "birth_date": 1, "gender": 1, "interests": 1}
    )
    items = []
    for p in cursor:
        age = profile_age(p.get("birth_date"))
        items.append({
            "user_id": str(p["user_id"]),
            "name": p.get("name", ""),
            "city": p.get("city") or "",
            "lat": p["lat"],
            "lon": p["lon"],
            "age": age,
            "gender_display": _gender_display(p.get("gender")),
            "interests": profile_interests_list(p),
        })
    return {"users": items}
