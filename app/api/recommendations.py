import logging

from flask import request, current_app
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db
from app.models.profile import profile_to_dict, profile_interests_list, get_profile_by_user_id
from app.recommendation_engine import get_recommendations, get_recommendations_count

logger = logging.getLogger(__name__)


@api_bp.route("/recommendations", methods=["GET"])
@login_required
def recommendations():
    limit = min(int(request.args.get("limit", 20)), 50)
    age_min = request.args.get("age_min", type=int)
    age_max = request.args.get("age_max", type=int)
    gender = request.args.get("gender") or None
    city = request.args.get("city") or None
    interests_str = request.args.get("interests")
    interests = [s.strip() for s in interests_str.split(",")] if interests_str else None
    only_real = request.args.get("only_real", "").lower() in ("1", "true", "yes")
    map_lat = request.args.get("map_lat", type=float)
    map_lon = request.args.get("map_lon", type=float)
    map_radius_km = request.args.get("map_radius_km", type=float)
    profiles = get_recommendations(
        user_id=current_user.id,
        limit=limit,
        age_min=age_min,
        age_max=age_max,
        gender=gender,
        city=city,
        interests=interests,
        only_real=only_real,
        map_lat=map_lat,
        map_lon=map_lon,
        map_radius_km=map_radius_km,
    )
    db = get_db(current_app.config)
    my_profile = get_profile_by_user_id(db, current_user.id)
    my_interests = set(profile_interests_list(my_profile)) if my_profile else set()
    result = []
    for p in profiles:
        d = profile_to_dict(p)
        their_interests = set(profile_interests_list(p))
        union = len(my_interests | their_interests)
        common = len(my_interests & their_interests)
        d["match_score"] = round(common / union * 100) if union else 0
        result.append(d)
    return {"profiles": result}


@api_bp.route("/recommendations/count", methods=["GET"])
@login_required
def recommendations_count():
    """Количество пользователей в выбранном месте и радиусе (те же фильтры)."""
    age_min = request.args.get("age_min", type=int)
    age_max = request.args.get("age_max", type=int)
    gender = request.args.get("gender") or None
    city = request.args.get("city") or None
    only_real = request.args.get("only_real", "").lower() in ("1", "true", "yes")
    map_lat = request.args.get("map_lat", type=float)
    map_lon = request.args.get("map_lon", type=float)
    map_radius_km = request.args.get("map_radius_km", type=float)
    if map_lat is None or map_lon is None or map_radius_km is None or map_radius_km <= 0:
        return {"count": None}
    count = get_recommendations_count(
        user_id=current_user.id,
        age_min=age_min,
        age_max=age_max,
        gender=gender,
        city=city,
        only_real=only_real,
        map_lat=map_lat,
        map_lon=map_lon,
        map_radius_km=map_radius_km,
    )
    return {"count": count}
