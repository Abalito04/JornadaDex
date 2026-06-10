from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import Company, Employee, TimeRecord, User
from app.roles import LEGACY_ADMIN, ROLE_OWNER, ROLE_SUPERVISOR


def is_owner_user(user):
    return bool(
        user
        and (
            user.is_company_owner
            or user.role in (ROLE_OWNER, LEGACY_ADMIN)
            or user.id in _owner_user_ids()
        )
    )


def is_supervisor_scope(user):
    if not user or is_platform_admin():
        return False
    return user.role == ROLE_SUPERVISOR and not is_owner_user(user)


def visible_employees_query(query):
    if not is_supervisor_scope(_current_user()):
        return query
    return _exclude_ids(query, Employee.id, _owner_employee_ids())


def visible_users_query(query):
    if not is_supervisor_scope(_current_user()):
        return query
    return _exclude_ids(query, User.id, _owner_user_ids()).filter(
        User.is_company_owner.is_(False),
        User.role.notin_([ROLE_OWNER, LEGACY_ADMIN]),
    )


def visible_time_records_query(query):
    if not is_supervisor_scope(_current_user()):
        return query
    return _exclude_ids(query, TimeRecord.employee_id, _owner_employee_ids())


def employee_is_visible(employee):
    if not is_supervisor_scope(_current_user()):
        return True
    return bool(employee and employee.id not in _owner_employee_ids())


def user_is_visible(user):
    if not is_supervisor_scope(_current_user()):
        return True
    if is_owner_user(user):
        return False
    return not (user and user.employee_id and user.employee_id in _owner_employee_ids())


def _owner_user_ids():
    company_id = current_company_id()
    if not company_id:
        return []
    company_owner_ids = [
        owner_id
        for (owner_id,) in db.session.query(Company.created_by)
        .filter(Company.id == company_id, Company.created_by.isnot(None))
        .all()
    ]
    explicit_owner_ids = [
        user_id
        for (user_id,) in db.session.query(User.id)
        .filter(
            User.company_id == company_id,
            User.deleted_at.is_(None),
            (User.is_company_owner.is_(True)) | (User.role.in_([ROLE_OWNER, LEGACY_ADMIN])),
        )
        .all()
    ]
    return sorted(set(company_owner_ids + explicit_owner_ids))


def _owner_employee_ids():
    company_id = current_company_id()
    if not company_id:
        return []
    owner_user_ids = _owner_user_ids()
    query = Employee.query.filter(Employee.company_id == company_id, Employee.deleted_at.is_(None))
    marker_query = query.filter(
        (Employee.document_number.ilike("owner-%"))
        | (Employee.position.in_(["Jefe", "Dueño", "Dueno"]))
    )
    marker_ids = [employee_id for (employee_id,) in marker_query.with_entities(Employee.id).all()]
    if owner_user_ids:
        linked_ids = [
            employee_id
            for (employee_id,) in db.session.query(User.employee_id)
            .filter(User.id.in_(owner_user_ids), User.employee_id.isnot(None))
            .all()
        ]
    else:
        linked_ids = []
    return sorted(set(marker_ids + linked_ids))


def _exclude_ids(query, column, ids):
    if not ids:
        return query
    return query.filter(column.notin_(ids))


def _current_user():
    from flask_login import current_user

    return current_user
