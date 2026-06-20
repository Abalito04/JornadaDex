import os


def clean_env_value(value):
    if value is None:
        return value
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def normalize_database_url(url):
    url = clean_env_value(url)
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def require_secret_key():
    secret_key = clean_env_value(os.getenv("SECRET_KEY"))
    if not secret_key:
        raise RuntimeError("SECRET_KEY must be set before starting JornadaDex.")
    return secret_key


class Config:
    SECRET_KEY = require_secret_key()
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///time_control.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = clean_env_value(os.getenv("SESSION_COOKIE_SECURE", "false")).lower() == "true"
