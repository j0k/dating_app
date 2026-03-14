"""
Скрипт добавления 1000 тестовых пользователей с координатами по всему миру (только суша).
Запуск: python scripts/seed_test_users.py
"""
import os
import random
import sys
from datetime import datetime, timezone, date, time, timedelta
from pymongo import MongoClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_cities_land import WORLD_CITIES

GENDERS = ("male", "female", "other")


def random_birth_date_datetime():
    """Случайная дата рождения (18–60 лет), как datetime для MongoDB."""
    age = random.randint(18, 60)
    today = date.today()
    birth = date(today.year - age, random.randint(1, 12), random.randint(1, 28))
    return datetime.combine(birth, time.min)

def get_password_hash():
    from werkzeug.security import generate_password_hash
    return generate_password_hash("test123")

FIRST_NAMES = (
    "Anna Maria Elena Sofia Julia Laura Emma Olivia Mia Isabella Luna Leah Nora "
    "Liam Noah Oliver James Lucas Mateo Alexander Hugo Leon Max Felix David "
    "Yuki Hiroshi Mei Wei Chen Dmitri Alex Carlos Lucia Amara Zara Aaliyah "
    "Fatima Layla Jasmine Priya Ananya Sana Gabriel Rafael Bruno Pedro João "
    "Miguel Diego Santiago Sophie Hannah Lisa Lena Lara Ida Mila Finn Paul Ben Tim "
).split()

def main():
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/dating_app")
    client = MongoClient(uri)
    db = client.get_database()

    n = 1000
    existing = db.users.count_documents({"email": {"$regex": r"^test_user_\d+@test\.dating\.app$"}})
    if existing >= n:
        print(f"Уже есть {existing} тестовых пользователей. Обновляю координаты, возраст и пол...")
        test_user_ids = [u["_id"] for u in db.users.find({"email": {"$regex": r"^test_user_.*@test\.dating\.app$"}}, {"_id": 1})]
        updated = 0
        for uid in test_user_ids:
            lat, lon, city_name = random.choice(WORLD_CITIES)
            set_fields = {"lat": lat, "lon": lon, "city": city_name}
            prof = db.profiles.find_one({"user_id": uid}, {"birth_date": 1, "gender": 1})
            if prof is None:
                continue
            if not prof.get("birth_date"):
                set_fields["birth_date"] = random_birth_date_datetime()
            if not prof.get("gender"):
                set_fields["gender"] = random.choice(GENDERS)
            r = db.profiles.update_one({"user_id": uid}, {"$set": set_fields})
            if r.modified_count:
                updated += 1
        print(f"Обновлено профилей: {updated}")
        return

    to_add = n - existing
    print(f"Добавляем {to_add} тестовых пользователей с координатами...")

    used_emails = set(db.users.distinct("email"))
    pwd_hash = get_password_hash()
    now = datetime.now(timezone.utc)
    inserted_total = 0

    while inserted_total < to_add:
        batch_size = min(200, to_add - inserted_total)
        users_batch = []
        profile_data = []

        for _ in range(batch_size):
            while True:
                num = random.randint(1000, 999999)
                email = f"test_user_{num}@test.dating.app"
                if email not in used_emails:
                    used_emails.add(email)
                    break
            name = random.choice(FIRST_NAMES) + " " + random.choice(FIRST_NAMES)[:1] + "."
            lat, lon, city_name = random.choice(WORLD_CITIES)
            users_batch.append({
                "email": email,
                "password_hash": pwd_hash,
                "created_at": now,
            })
            profile_data.append({
                "name": name,
                "lat": lat,
                "lon": lon,
                "city": city_name,
                "birth_date": random_birth_date_datetime(),
                "gender": random.choice(GENDERS),
            })

        r = db.users.insert_many(users_batch)
        profiles_batch = [
            {
                "user_id": uid,
                "name": profile_data[i]["name"],
                "lat": profile_data[i]["lat"],
                "lon": profile_data[i]["lon"],
                "city": profile_data[i].get("city"),
                "birth_date": profile_data[i].get("birth_date"),
                "gender": profile_data[i].get("gender"),
                "about": "",
                "interests": [],
                "is_visible": True,
                "updated_at": now,
            }
            for i, uid in enumerate(r.inserted_ids)
        ]
        db.profiles.insert_many(profiles_batch)
        inserted_total += batch_size
        print(f"  вставлено {inserted_total} / {to_add}")

    total = db.users.count_documents({"email": {"$regex": r"^test_user_.*@test\.dating\.app$"}})
    with_coords = db.profiles.count_documents({"lat": {"$exists": True, "$ne": None}, "lon": {"$exists": True, "$ne": None}})
    print(f"Готово. Тестовых пользователей: {total}, с координатами на карте: {with_coords}")

if __name__ == "__main__":
    main()
