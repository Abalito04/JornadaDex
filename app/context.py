from flask import session
from flask_login import current_user

from app.models import Company


def is_platform_admin():
    if not current_user.is_authenticated:
        return False
    return getattr(current_user, "is_platform_admin", False) or current_user.role == "Developer"


def current_company_id():
    if not current_user.is_authenticated:
        return None
    if is_platform_admin():
        return session.get("active_company_id") or current_user.company_id
    return current_user.company_id


def current_company():
    company_id = current_company_id()
    if not company_id:
        return None
    return Company.query.get(company_id)
