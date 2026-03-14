"""
Заполняет у всех профилей: дата рождения (1900–2006), пол, интересы (3–7 из списка).
Запуск: python scripts/update_all_profiles_fill.py
"""
import os
import random
import sys
from datetime import datetime, date, time, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pymongo import MongoClient

INTERESTS = [
    "музыка", "баланс", "любовь", "энергия", "путешествия", "кулинария", "походы",
    "авиация", "секс", "фотография", "инь-янь", "философия", "ницше", "политика",
    "дипломатия", "кино", "программирование", "стартапы", "книги", "спорт", "йога",
    "искусство", "театр", "наука", "природа", "кофе", "животные", "деньги",
]

GENDERS = ("male", "female", "other")


def random_birth_date(year_min=1900, year_max=2006):
    """Случайная дата рождения в диапазоне годов, как datetime для MongoDB."""
    y = random.randint(year_min, year_max)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return datetime.combine(date(y, m, d), time.min)


def main():
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/dating_app")
    client = MongoClient(uri)
    db = client.get_database()

    cursor = db.profiles.find({}, {"_id": 1, "user_id": 1})
    profiles = list(cursor)
    total = len(profiles)
    print(f"Найдено профилей: {total}")

    updated = 0
    for p in profiles:
        n_interests = random.randint(3, 7)
        interests = random.sample(INTERESTS, min(n_interests, len(INTERESTS)))
        r = db.profiles.update_one(
            {"_id": p["_id"]},
            {
                "$set": {
                    "birth_date": random_birth_date(),
                    "gender": random.choice(GENDERS),
                    "interests": interests,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if r.modified_count:
            updated += 1

    print(f"Обновлено профилей: {updated}")


if __name__ == "__main__":
    main()
