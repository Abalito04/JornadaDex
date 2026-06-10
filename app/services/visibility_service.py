from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import Employee, TimeRecord, User
from app.roles import LEGACY_ADMIN, ROLE_OWNER, ROLE_SUPERVISOR


def is_owner_user(user):
    return bool(user and (user.is_company_owner or user.role in (ROLE_OWNER, LEGACY_ADMIN)))


def is_supervisor_scope(user):
    if not user or is_platform_admin():
        return False
    return user.role == ROLE_SUPERVISOR and not is_owner_user(user)


def visible_employees_query(query):
    if not is_supervisor_scope(_current_user()):
        return query
    return query.filter(Employee.id.notin_(_owner_employee_ids_subquery()))


def visible_users_query(query):
    if not is_supervisor_scope(_current_user()):
        return query
    return query.filter(
        User.is_company_owner.is_(False),
        User.role.notin_([ROLE_OWNER, LEGACY_ADMIN]),
    )


def visible_time_records_query(query):
    if not is_supervisor_scope(_current_user()):
        return query
    return query.filter(TimeRecord.employee_id.notin_(_owner_employee_ids_subquery()))


def employee_is_visible(employee):
    if not is_supervisor_scope(_current_user()):
        return True
    return not is_owner_user(employee.user if employee else None)


def user_is_visible(user):
    if not is_supervisor_scope(_current_user()):
        return True
    return not is_owner_user(user)


def _owner_employee_ids_subquery():
    return (
        db.session.query(User.employee_id)
        .filter(
            User.company_id == current_company_id(),
            User.deleted_at.is_(None),
            User.employee_id.isnot(None),
            (User.is_company_owner.is_(True)) | (User.role.in_([ROLE_OWNER, LEGACY_ADMIN])),
        )
    )


def _current_user():
    from flask_login import current_user

    return current_user
