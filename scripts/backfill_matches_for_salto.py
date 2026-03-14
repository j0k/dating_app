"""
Обратное заполнение матчей для Сальто: по всем его лайкам (is_like=True)
создать матч, если лайкнут тестовый пользователь и матча ещё нет.
Запуск: python scripts/backfill_matches_for_salto.py
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pymongo import MongoClient

from app.config import config

REAL_USER_NAME = "Сальто"


def get_db():
    cfg = config.get(os.environ.get("FLASK_ENV", "development"))
    return MongoClient(cfg.MONGODB_URI).get_database()


def is_test_user(db, user_id):
    profile = db.profiles.find_one({"user_id": user_id})
    if not profile or not profile.get("name"):
        return True
    return (profile.get("name") or "").strip() != REAL_USER_NAME


def main():
    db = get_db()
    prof = db.profiles.find_one({"name": REAL_USER_NAME})
    if not prof:
        print("Профиль Сальто не найден")
        return 1
    salto_uid = prof["user_id"]
    print("Сальто user_id:", salto_uid)

    created = 0
    for like_doc in db.likes.find({"from_user_id": salto_uid, "is_like": True}):
        other_id = like_doc["to_user_id"]
        if not is_test_user(db, other_id):
            continue
        u1, u2 = (salto_uid, other_id) if salto_uid < other_id else (other_id, salto_uid)
        if db.matches.find_one({"user1_id": u1, "user2_id": u2}):
            continue
        db.matches.insert_one({
            "user1_id": u1,
            "user2_id": u2,
            "created_at": datetime.utcnow(),
        })
        created += 1
    print("Создано матчей:", created)
    return 0


if __name__ == "__main__":
    sys.exit(main())
