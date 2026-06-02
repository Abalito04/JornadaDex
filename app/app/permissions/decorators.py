from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def roles_required(*roles):
    def wrapper(view):
        @wraps(view)
        @login_required
        def inner(*args, **kwargs):
            if getattr(current_user, "is_platform_admin", False):
                return view(*args, **kwargs)
            if current_user.role not in roles and not current_user.is_company_owner:
                abort(403)
            return view(*args, **kwargs)

        return inner

    return wrapper


def manager_required(view):
    return roles_required("Administrator", "Supervisor")(view)
