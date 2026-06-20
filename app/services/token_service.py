from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from flask import current_app


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def create_security_token(purpose, payload):
    return _serializer().dumps(payload, salt=purpose)


def load_security_token(purpose, token, max_age_seconds):
    try:
        return _serializer().loads(token, salt=purpose, max_age=max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
