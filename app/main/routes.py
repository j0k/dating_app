from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.main import main_bp
from app.db import get_db
from app.models.profile import get_profile_by_user_id, profile_to_dict


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/stats")
def stats_redirect():
    """Редирект на /api/stats для удобства."""
    return redirect(url_for("api.stats"), code=302)


@main_bp.route("/register")
def register_redirect():
    """Редирект на /auth/register (сохраняем ref из ссылки-приглашения)."""
    return redirect(url_for("auth.register", **request.args), code=302)


@main_bp.route("/share/<user_id>")
def share_profile(user_id):
    """Публичная страница профиля по ссылке (для шаринга в соцсети/ТГ)."""
    from flask import current_app
    db = get_db(current_app.config)
    profile = get_profile_by_user_id(db, user_id)
    if not profile:
        return render_template("share_profile.html", profile=None), 404
    return render_template("share_profile.html", profile=profile_to_dict(profile))


@main_bp.route("/feed")
@login_required
def feed():
    return render_template("feed.html")


@main_bp.route("/cabinet")
@login_required
def cabinet():
    return render_template("cabinet.html")


@main_bp.route("/map")
def map_page():
    return render_template("map.html")


@main_bp.route("/matches")
@login_required
def matches():
    return render_template("matches.html")


@main_bp.route("/chat/<match_id>")
@login_required
def chat(match_id):
    return render_template("chat.html", match_id=match_id)
