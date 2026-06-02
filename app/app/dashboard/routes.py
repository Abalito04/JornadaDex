from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.models import Area, Employee, Task, TimeRecord

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    base = TimeRecord.query.filter_by(company_id=current_user.company_id, deleted_at=None)
    if current_user.role == "Employee" and not current_user.is_company_owner:
        base = base.filter(TimeRecord.employee_id == current_user.employee_id)

    metrics = {
        "active_employees": Employee.query.filter_by(company_id=current_user.company_id, active=True, deleted_at=None).count(),
        "total_hours_today": _sum_hours(base.filter(TimeRecord.record_date == today)),
        "total_hours_week": _sum_hours(base.filter(TimeRecord.record_date >= week_start)),
        "total_hours_month": _sum_hours(base.filter(TimeRecord.record_date >= month_start)),
        "total_records": base.count(),
        "active_areas": Area.query.filter_by(company_id=current_user.company_id, active=True, deleted_at=None).count(),
        "active_tasks": Task.query.join(Area).filter(Area.company_id == current_user.company_id, Task.active.is_(True), Task.deleted_at.is_(None)).count(),
    }

    by_area = (
        base.join(Area, TimeRecord.area_id == Area.id)
        .with_entities(Area.name, func.sum(TimeRecord.hours))
        .group_by(Area.name)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(6)
        .all()
    )
    by_employee = (
        base.join(Employee, TimeRecord.employee_id == Employee.id)
        .with_entities(Employee.first_name, Employee.last_name, func.sum(TimeRecord.hours))
        .group_by(Employee.id)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(6)
        .all()
    )
    return render_template("dashboard/index.html", metrics=metrics, by_area=by_area, by_employee=by_employee)


def _sum_hours(query):
    return query.with_entities(func.coalesce(func.sum(TimeRecord.hours), 0)).scalar() or Decimal("0.00")
