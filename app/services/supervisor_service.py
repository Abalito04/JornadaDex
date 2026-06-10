from sqlalchemy import func, or_

from app.models import Employee, User
from app.roles import ROLE_SUPERVISOR


def supervisors_for_company(company_id):
    return (
        User.query.outerjoin(Employee, User.employee_id == Employee.id)
        .filter(
            User.company_id == company_id,
            User.deleted_at.is_(None),
            User.is_active_flag.is_(True),
            User.is_company_owner.is_(False),
            or_(
                func.lower(User.role) == ROLE_SUPERVISOR.lower(),
                func.lower(Employee.position).like("%supervisor%"),
            ),
        )
        .order_by(Employee.last_name, User.username)
        .all()
    )


def supervisor_for_company(company_id, supervisor_id):
    if not supervisor_id:
        return None
    return (
        User.query.outerjoin(Employee, User.employee_id == Employee.id)
        .filter(
            User.id == supervisor_id,
            User.company_id == company_id,
            User.deleted_at.is_(None),
            User.is_active_flag.is_(True),
            User.is_company_owner.is_(False),
            or_(
                func.lower(User.role) == ROLE_SUPERVISOR.lower(),
                func.lower(Employee.position).like("%supervisor%"),
            ),
        )
        .first()
    )
