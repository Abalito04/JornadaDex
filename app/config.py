import os
from datetime import timedelta


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
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(clean_env_value(os.getenv("SESSION_LIFETIME_HOURS", "12"))))
    PUBLIC_SIGNUP_ENABLED = clean_env_value(os.getenv("PUBLIC_SIGNUP_ENABLED", "false")).lower() == "true"
    ENABLE_DEVELOPER_BOOTSTRAP = clean_env_value(os.getenv("ENABLE_DEVELOPER_BOOTSTRAP", "false")).lower() == "true"
    LOGIN_RATE_LIMIT_ATTEMPTS = int(clean_env_value(os.getenv("LOGIN_RATE_LIMIT_ATTEMPTS", "5")))
    LOGIN_RATE_LIMIT_WINDOW = timedelta(minutes=int(clean_env_value(os.getenv("LOGIN_RATE_LIMIT_WINDOW_MINUTES", "15"))))
    SIGNUP_RATE_LIMIT_ATTEMPTS = int(clean_env_value(os.getenv("SIGNUP_RATE_LIMIT_ATTEMPTS", "5")))
    SIGNUP_RATE_LIMIT_WINDOW = timedelta(minutes=int(clean_env_value(os.getenv("SIGNUP_RATE_LIMIT_WINDOW_MINUTES", "60"))))
    MAX_CONTENT_LENGTH = int(clean_env_value(os.getenv("MAX_CONTENT_LENGTH", str(4 * 1024 * 1024))))
    CLIENT_IMPORT_MAX_ROWS = int(clean_env_value(os.getenv("CLIENT_IMPORT_MAX_ROWS", "2000")))
    TURNSTILE_SITE_KEY = clean_env_value(os.getenv("TURNSTILE_SITE_KEY", ""))
    TURNSTILE_SECRET_KEY = clean_env_value(os.getenv("TURNSTILE_SECRET_KEY", ""))
    EMAIL_VERIFICATION_REQUIRED = clean_env_value(os.getenv("EMAIL_VERIFICATION_REQUIRED", "false")).lower() == "true"
    EMAIL_VERIFICATION_MAX_AGE_HOURS = int(clean_env_value(os.getenv("EMAIL_VERIFICATION_MAX_AGE_HOURS", "24")))
    PASSWORD_RESET_MAX_AGE_MINUTES = int(clean_env_value(os.getenv("PASSWORD_RESET_MAX_AGE_MINUTES", "60")))
    SMTP_HOST = clean_env_value(os.getenv("SMTP_HOST", ""))
    SMTP_PORT = int(clean_env_value(os.getenv("SMTP_PORT", "587")))
    SMTP_USERNAME = clean_env_value(os.getenv("SMTP_USERNAME", ""))
    SMTP_PASSWORD = clean_env_value(os.getenv("SMTP_PASSWORD", ""))
    SMTP_FROM_EMAIL = clean_env_value(os.getenv("SMTP_FROM_EMAIL", ""))
    SMTP_USE_TLS = clean_env_value(os.getenv("SMTP_USE_TLS", "true")).lower() == "true"
    RESEND_API_KEY = clean_env_value(os.getenv("RESEND_API_KEY", ""))





