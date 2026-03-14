"""
Точка входа для разработки: python run.py
В production использовать gunicorn: gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
"""
import os

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.debug)
