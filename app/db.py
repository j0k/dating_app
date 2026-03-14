"""
Подключение к MongoDB и коллекции.
"""
from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from pymongo.collection import Collection

_client: MongoClient | None = None
_db: Database | None = None


def get_db(config) -> Database:
    global _client, _db
    if _db is not None:
        return _db
    _client = MongoClient(config["MONGODB_URI"])
    _db = _client.get_database()
    _ensure_indexes(_db)
    return _db


def _ensure_indexes(db: Database) -> None:
    db.users.create_index("email", unique=True)
    try:
        db.users.create_index("invite_code", unique=True, sparse=True)
    except Exception:
        pass
    db.users.create_index("referred_by")
    db.profiles.create_index("user_id", unique=True)
    db.likes.create_index([("from_user_id", ASCENDING), ("to_user_id", ASCENDING)], unique=True)
    db.matches.create_index([("user1_id", ASCENDING), ("user2_id", ASCENDING)], unique=True)
    db.messages.create_index("match_id")
    db.messages.create_index([("match_id", ASCENDING), ("_id", ASCENDING)])
    db.announcements.create_index("created_at")


def oid(s) -> ObjectId:
    """Строку или ObjectId привести к ObjectId."""
    if s is None:
        raise ValueError("id is None")
    if isinstance(s, ObjectId):
        return s
    return ObjectId(s)
