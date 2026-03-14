"""
Рекомендации: фильтрация по параметрам и исключение уже просмотренных (MongoDB).
"""
import logging
import math
from datetime import date, datetime, time
from bson import ObjectId

from app.db import get_db, oid

logger = logging.getLogger(__name__)

# Радиус Земли в км
EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние между двумя точками на Земле в км (формула Haversine)."""
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(min(1, a)))
    return EARTH_RADIUS_KM * c


def get_recommendations(
    user_id: str,
    limit: int = 20,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
    city: str | None = None,
    interests: list[str] | None = None,
    only_real: bool = False,
    map_lat: float | None = None,
    map_lon: float | None = None,
    map_radius_km: float | None = None,
):
    """
    Рекомендации для user_id. only_real — исключить тестовых (email test_user_*@test.dating.app).
    map_lat, map_lon, map_radius_km — фильтр по расстоянию от точки на карте.
    """
    from flask import current_app
    db = get_db(current_app.config)
    uid = oid(user_id)
    viewed = {r["to_user_id"] for r in db.likes.find({"from_user_id": uid}, {"to_user_id": 1})}
    viewed.add(uid)
    match = {"user_id": {"$nin": list(viewed)}, "is_visible": True}

    if only_real:
        test_user_ids = list(
            db.users.find(
                {"email": {"$regex": r"^test_user_.*@test\.dating\.app$"}},
                {"_id": 1}
            )
        )
        test_ids = [u["_id"] for u in test_user_ids]
        if test_ids:
            match["user_id"]["$nin"] = list(viewed | set(test_ids))

    if age_min is not None or age_max is not None:
        today = date.today()
        if age_max is not None and age_max < 199:
            birth_min_date = date(today.year - age_max - 1, today.month, today.day)
            birth_min = datetime.combine(birth_min_date, time.min)
            match.setdefault("birth_date", {})["$gte"] = birth_min
        if age_min is not None:
            birth_max_date = date(today.year - age_min, today.month, today.day)
            birth_max = datetime.combine(birth_max_date, time.max)
            match.setdefault("birth_date", {})["$lte"] = birth_max
    if gender:
        match["gender"] = gender
    if city:
        match["city"] = {"$regex": city, "$options": "i"}

    if map_lat is not None and map_lon is not None and map_radius_km is not None and map_radius_km > 0:
        match["lat"] = {"$exists": True, "$ne": None}
        match["lon"] = {"$exists": True, "$ne": None}

    fetch_limit = limit * 5
    if map_lat is not None and map_lon is not None and map_radius_km is not None and map_radius_km > 0:
        fetch_limit = min(5000, max(2000, limit * 100))
    cursor = db.profiles.find(match).sort("updated_at", -1).limit(fetch_limit)
    candidates = list(cursor)

    if map_lat is not None and map_lon is not None and map_radius_km is not None and map_radius_km > 0:
        center_lat = float(map_lat)
        center_lon = float(map_lon)
        radius_km = float(map_radius_km)
        candidates = [
            p for p in candidates
            if p.get("lat") is not None and p.get("lon") is not None
            and _haversine_km(center_lat, center_lon, p["lat"], p["lon"]) <= radius_km
        ]

    if interests:
        iset = set(s.strip().lower() for s in interests if s)
        def score(p):
            raw = p.get("interests") or []
            pi = set((str(x).strip().lower() for x in raw)) if isinstance(raw, list) else set()
            return len(pi & iset)
        # Показывать только тех, у кого есть хотя бы один из выбранных интересов
        candidates = [p for p in candidates if score(p) > 0]
        candidates.sort(key=score, reverse=True)
    result = candidates[:limit]
    logger.debug("Recommendations for user %s: %d profiles", user_id, len(result))
    return result


def get_recommendations_count(
    user_id: str,
    age_min: int | None = None,
    age_max: int | None = None,
    gender: str | None = None,
    city: str | None = None,
    interests: list[str] | None = None,
    only_real: bool = False,
    map_lat: float | None = None,
    map_lon: float | None = None,
    map_radius_km: float | None = None,
) -> int:
    """Количество пользователей по тем же фильтрам (для отображения на карте)."""
    return len(
        get_recommendations(
            user_id=user_id,
            limit=5000,
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
    )
