"""
Модели: обёртки над документами MongoDB. User совместим с Flask-Login.
"""
from app.models.user import User
from app.models.profile import profile_to_dict, get_profile_by_user_id

__all__ = ["User", "profile_to_dict", "get_profile_by_user_id"]
