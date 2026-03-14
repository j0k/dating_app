"""
Конфигурация приложения по окружениям.
"""
import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-change-in-production"
    WTF_CSRF_ENABLED = True
    PER_PAGE = 20
    RECOMMENDATIONS_LIMIT = 50
    MONGODB_URI = os.environ.get("MONGODB_URI") or "mongodb://localhost:27017/dating_app"

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    MONGODB_URI = os.environ.get("MONGODB_URI") or "mongodb://localhost:27017/dating_app"


class ProductionConfig(Config):
    DEBUG = False
    MONGODB_URI = os.environ.get("MONGODB_URI") or "mongodb://localhost:27017/dating_app"
    SECRET_KEY = os.environ.get("SECRET_KEY") or None

    @staticmethod
    def init_app(app):
        if not ProductionConfig.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")


class TestingConfig(Config):
    TESTING = True
    MONGODB_URI = "mongodb://localhost:27017/dating_app_test"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
