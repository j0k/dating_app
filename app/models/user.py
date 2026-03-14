from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from bson import ObjectId

from app.db import get_db, oid
from app.models.profile import get_profile_by_user_id


class User(UserMixin):
    """Пользователь из коллекции users + опционально профиль для current_user.profile."""

    def __init__(self, doc: dict, profile_doc: dict | None = None):
        self._doc = doc
        self._profile_doc = profile_doc

    @property
    def id(self):
        return str(self._doc["_id"])

    def get_id(self) -> str:
        return self.id

    @property
    def email(self) -> str:
        return self._doc.get("email", "")

    def set_password(self, password: str) -> None:
        self._doc["password_hash"] = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self._doc.get("password_hash", ""), password)

    @property
    def profile(self):
        """Объект-профиль с to_dict(), как у старой модели."""
        if self._profile_doc is None:
            from flask import current_app
            db = get_db(current_app.config)
            self._profile_doc = get_profile_by_user_id(db, self._doc["_id"])
        if self._profile_doc is None:
            return None
        return _ProfileWrap(self._profile_doc)

    def __repr__(self):
        return f"<User {self.email}>"


class _ProfileWrap:
    """Обёртка над документом профиля с to_dict() и полями для совместимости."""

    def __init__(self, doc: dict):
        self._doc = doc

    @property
    def id(self): return str(self._doc.get("_id", ""))
    @property
    def user_id(self): return str(self._doc.get("user_id", ""))
    @property
    def name(self): return self._doc.get("name", "")
    @property
    def birth_date(self): return self._doc.get("birth_date")
    @property
    def gender(self): return self._doc.get("gender")
    @property
    def about(self): return self._doc.get("about")
    @property
    def interests(self): return self._doc.get("interests") or ""
    @property
    def city(self): return self._doc.get("city")
    @property
    def avatar_url(self): return self._doc.get("avatar_url")
    @property
    def is_visible(self): return self._doc.get("is_visible", True)

    def interests_list(self):
        raw = self._doc.get("interests")
        if isinstance(raw, list):
            return [str(x) for x in raw]
        if not raw:
            return []
        return [s.strip() for s in str(raw).split(",") if s.strip()]

    def to_dict(self):
        return profile_to_dict(self._doc)


def get_user_by_id(db, user_id) -> dict | None:
    try:
        uid = oid(user_id)
    except Exception:
        return None
    return db.users.find_one({"_id": uid})


def get_user_by_email(db, email: str) -> dict | None:
    return db.users.find_one({"email": email})


def _generate_invite_code():
    import secrets
    return secrets.token_urlsafe(12)


def create_user(db, email: str, password_hash: str, referred_by: ObjectId | None = None) -> ObjectId:
    now = datetime.utcnow()
    for _ in range(5):
        invite_code = _generate_invite_code()
        doc = {
            "email": email,
            "password_hash": password_hash,
            "created_at": now,
            "invite_code": invite_code,
        }
        if referred_by is not None:
            doc["referred_by"] = referred_by
        try:
            r = db.users.insert_one(doc)
            return r.inserted_id
        except Exception:
            continue
    invite_code = _generate_invite_code()
    doc = {
        "email": email,
        "password_hash": password_hash,
        "created_at": now,
        "invite_code": invite_code,
    }
    if referred_by is not None:
        doc["referred_by"] = referred_by
    r = db.users.insert_one(doc)
    return r.inserted_id


def get_profile_by_user_id(db, user_id) -> dict | None:
    uid = user_id if isinstance(user_id, ObjectId) else oid(user_id)
    return db.profiles.find_one({"user_id": uid})
