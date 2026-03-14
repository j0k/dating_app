"""Эндпоинт /api/health: uptime и счётчик запросов."""
from datetime import datetime

from flask import current_app, jsonify

from app.api import api_bp


@api_bp.route("/health", methods=["GET"])
def health():
    """Возвращает uptime процесса и общее количество обращений к серверу."""
    start = current_app.config.get("APP_START_TIME")
    uptime_seconds = (datetime.utcnow() - start).total_seconds() if start else 0
    count_list = current_app.config.get("REQUEST_COUNT")
    request_count = count_list[0] if isinstance(count_list, list) and count_list else 0
    return jsonify({
        "uptime_seconds": round(uptime_seconds, 1),
        "uptime": _format_uptime(uptime_seconds),
        "request_count": request_count,
    })


def _format_uptime(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    if s < 86400:
        return f"{s // 3600}h {(s % 3600) // 60}m"
    return f"{s // 86400}d {(s % 86400) // 3600}h"
