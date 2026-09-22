from .db_helper import get_db_config
from django.db import connection


def db_status_processor(request):
    """Injects db_status into every template context for the sidebar."""
    try:
        engine_name = connection.vendor
        is_mysql = (engine_name == "mysql")
        db_name = connection.settings_dict.get("NAME", "db.sqlite3")
        host = connection.settings_dict.get("HOST", "local")
        return {
            "db_status": {
                "engine": engine_name,
                "is_mysql": is_mysql,
                "db_name": db_name,
                "host": host or "localhost",
            }
        }
    except Exception:
        return {"db_status": {"engine": "sqlite3", "is_mysql": False, "db_name": "db.sqlite3", "host": "local"}}
