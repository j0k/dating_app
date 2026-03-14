"""
Реферальная система: инвайт-ссылка и счётчик приглашённых.
"""
import secrets

from flask import request
from flask_login import current_user, login_required

from app.api import api_bp
from app.db import get_db, oid


def _generate_invite_code():
    return secrets.token_urlsafe(12)


@api_bp.route("/me/invite", methods=["GET"])
@login_required
def my_invite():
    """Инвайт-ссылка текущего пользователя и число приглашённых."""
    from flask import current_app
    db = get_db(current_app.config)
    uid = oid(current_user.id)
    user = db.users.find_one({"_id": uid})
    if not user:
        return {"error": "User not found"}, 404
    invite_code = user.get("invite_code")
    if not invite_code:
        invite_code = _generate_invite_code()
        db.users.update_one({"_id": uid}, {"$set": {"invite_code": invite_code}})
    base = request.url_root.rstrip("/")
    invite_link = f"{base}/register?ref={invite_code}"
    referred_count = db.users.count_documents({"referred_by": uid})
    return {"invite_link": invite_link, "referred_count": referred_count}
