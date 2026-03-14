"""
Проверка профиля в БД по имени. Запуск: python scripts/check_profile.py [имя]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    name = (sys.argv[1] if len(sys.argv) > 1 else "Сальто").strip()
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/dating_app")
    from pymongo import MongoClient
    client = MongoClient(uri)
    db = client.get_database()
    # Поиск по точному имени или по вхождению
    profile = db.profiles.find_one({"name": name})
    if not profile:
        profile = db.profiles.find_one({"name": {"$regex": name, "$options": "i"}})
    if not profile:
        print(f"Профиль с именем «{name}» не найден.")
        return
    user_id = profile.get("user_id")
    user = db.users.find_one({"_id": user_id}) if user_id else None
    print("--- Профиль ---")
    print("user_id:", user_id)
    print("name:", profile.get("name"))
    print("email (user):", user.get("email") if user else "—")
    print("lat:", profile.get("lat"))
    print("lon:", profile.get("lon"))
    print("city:", profile.get("city"))
    print("updated_at:", profile.get("updated_at"))
    if profile.get("lat") is None or profile.get("lon") is None:
        print("\n⚠ Координаты не заданы — укажите место в кабинете и сохраните профиль.")

if __name__ == "__main__":
    main()
