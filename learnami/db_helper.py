import json
import os
import pymysql
from pathlib import Path
from django.conf import settings
from django.core.management import call_command

CONFIG_FILE = Path(settings.BASE_DIR) / "db_config.json"

DEFAULT_CONFIG = {
    "ENGINE": "sqlite3",
    "NAME": "db.sqlite3",
    "HOST": "",
    "PORT": "3306",
    "USER": "",
    "PASSWORD": "",
    "OPTIONS": {
        "charset": "utf8mb4"
    }
}

def get_db_config():
    """Read the saved database configuration."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_db_config(config_dict):
    """Save database configuration to db_config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=2)

def test_mysql_connection(host, port, name, user, password):
    """
    Test direct MySQL connection via PyMySQL with connection timeout.
    Returns: (success: bool, message: str, server_info: str)
    """
    try:
        port_num = int(port) if port else 3306
    except ValueError:
        return False, "Invalid port number. Default is 3306.", ""

    try:
        conn = pymysql.connect(
            host=host.strip(),
            port=port_num,
            user=user.strip(),
            password=password,
            database=name.strip() if name else None,
            connect_timeout=6,
            charset="utf8mb4"
        )
        server_info = conn.get_server_info()
        conn.close()
        return True, f"Successfully connected to MySQL database '{name}' on {host}:{port_num}!", server_info
    except pymysql.err.OperationalError as e:
        code, msg = e.args
        if code == 2003:
            detail = (
                f"Connection timed out or refused (Error 2003). "
                f"If using cPanel, please ensure:\n"
                f"1. Your current public IP is whitelisted under 'Remote MySQL' in cPanel.\n"
                f"2. Your cPanel host allows remote MySQL on port {port_num}.\n"
                f"3. The hostname/IP '{host}' is correct."
            )
        elif code == 1045:
            detail = (
                f"Access denied for user '{user}' (Error 1045). "
                f"Please verify:\n"
                f"1. The username and password match your cPanel database user.\n"
                f"2. In cPanel > MySQL Databases, the user is assigned to database '{name}' with 'ALL PRIVILEGES'."
            )
        elif code == 1049:
            detail = f"Unknown database '{name}' (Error 1049). Please verify the exact database name in cPanel."
        else:
            detail = f"MySQL Operational Error ({code}): {msg}"
        return False, detail, ""
    except Exception as e:
        return False, f"Connection error: {str(e)}", ""

def auto_migrate():
    """Run Django migrations to auto-create and sync all tables."""
    try:
        call_command("makemigrations", interactive=False)
        call_command("migrate", interactive=False)
        return True, "All tables created and migrated successfully!"
    except Exception as e:
        return False, f"Migration failed: {str(e)}"
