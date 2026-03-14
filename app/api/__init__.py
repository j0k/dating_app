from flask import Blueprint

api_bp = Blueprint("api", __name__)

from app.api import (  # noqa: E402, F401
    profiles,
    recommendations,
    likes,
    matches,
    chat,
    announcements,
    map_users,
    invite,
)
