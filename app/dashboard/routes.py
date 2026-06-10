from datetime import timedelta
from decimal import Decimal

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from app.context import current_company_id, is_platform_admin
from app.models import AccountingClient, Area, Employee, Task, TimeRecord
from app.roles import ROLE_EMPLOYEE, ROLE_SUPERVISOR
from app.services.visibility_service import visible_company_time_records_query, visible_employees_query, visible_time_records_query
from app.utils.datetime import argentina_now

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    today = argentina_now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    company_id = current_company_id()
    base = TimeRecord.query.filter_by(company_id=company_id, deleted_at=None)
    dashboard_role = _dashboard_role()
    if dashboard_role == "employee":
        base = base.filter(TimeRecord.employee_id == current_user.employee_id)
    elif dashboard_role == "supervisor":
        base = visible_company_time_records_query(base)
    else:
        base = visible_time_records_query(base)

    active_employees_query = Employee.query.filter_by(company_id=company_id, active=True, deleted_at=None)
    open_records = base.filter(TimeRecord.end_time.is_(None)).order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc()).limit(8).all()
    recent_records = base.order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc()).limit(8).all()
    metrics = {
        "active_employees": visible_employees_query(active_employees_query).count(),
        "active_clients": AccountingClient.query.filter_by(company_id=company_id, active=True, deleted_at=None).count(),
        "total_hours_today": _sum_hours(base.filter(TimeRecord.record_date == today)),
        "total_hours_week": _sum_hours(base.filter(TimeRecord.record_date >= week_start)),
        "total_hours_month": _sum_hours(base.filter(TimeRecord.record_date >= month_start)),
        "total_records": base.count(),
        "total_records_month": base.filter(TimeRecord.record_date >= month_start).count(),
        "open_records": base.filter(TimeRecord.end_time.is_(None)).count(),
        "finished_today": base.filter(TimeRecord.record_date == today, TimeRecord.end_time.isnot(None)).count(),
        "active_areas": Area.query.filter_by(company_id=company_id, active=True, deleted_at=None).count(),
        "active_tasks": Task.query.join(Area).filter(Area.company_id == company_id, Task.active.is_(True), Task.deleted_at.is_(None)).count(),
    }

    by_area = (
        base.join(Area, TimeRecord.area_id == Area.id)
        .with_entities(Area.name, func.sum(TimeRecord.hours))
        .group_by(Area.name)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(6)
        .all()
    )
    by_area_week = (
        base.filter(TimeRecord.record_date >= week_start)
        .join(Area, TimeRecord.area_id == Area.id)
        .with_entities(Area.name, func.sum(TimeRecord.hours))
        .group_by(Area.name)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(8)
        .all()
    )
    by_area_month = (
        base.filter(TimeRecord.record_date >= month_start)
        .join(Area, TimeRecord.area_id == Area.id)
        .with_entities(Area.name, func.sum(TimeRecord.hours))
        .group_by(Area.name)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(8)
        .all()
    )
    by_client = (
        base.join(AccountingClient, TimeRecord.accounting_client_id == AccountingClient.id)
        .with_entities(AccountingClient.name, func.sum(TimeRecord.hours))
        .group_by(AccountingClient.name)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(6)
        .all()
    )
    by_employee_week = (
        base.filter(TimeRecord.record_date >= week_start)
        .join(Employee, TimeRecord.employee_id == Employee.id)
        .with_entities(Employee.first_name, Employee.last_name, func.sum(TimeRecord.hours))
        .group_by(Employee.id)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(10)
        .all()
    )
    by_employee = (
        base.filter(TimeRecord.record_date >= month_start)
        .join(Employee, TimeRecord.employee_id == Employee.id)
        .with_entities(Employee.first_name, Employee.last_name, func.sum(TimeRecord.hours))
        .group_by(Employee.id)
        .order_by(func.sum(TimeRecord.hours).desc())
        .limit(10)
        .all()
    )
    area_chart = _chart_rows([(name, hours) for name, hours in by_area])
    area_week_chart = _chart_rows([(name, hours) for name, hours in by_area_week])
    area_month_chart = _chart_rows([(name, hours) for name, hours in by_area_month])
    client_chart = _chart_rows([(name, hours) for name, hours in by_client])
    employee_week_chart = _chart_rows([(f"{first} {last}", hours) for first, last, hours in by_employee_week])
    employee_chart = _chart_rows([(f"{first} {last}", hours) for first, last, hours in by_employee])
    return render_template(
        "dashboard/index.html",
        dashboard_role=dashboard_role,
        metrics=metrics,
        by_area=by_area,
        by_client=by_client,
        by_employee=by_employee,
        area_chart=area_chart,
        area_week_chart=area_week_chart,
        area_month_chart=area_month_chart,
        client_chart=client_chart,
        employee_week_chart=employee_week_chart,
        employee_chart=employee_chart,
        open_records=open_records,
        recent_records=recent_records,
    )


def _sum_hours(query):
    return query.with_entities(func.coalesce(func.sum(TimeRecord.hours), 0)).scalar() or Decimal("0.00")


def _chart_rows(rows):
    normalized = [(label, float(value or 0)) for label, value in rows]
    max_value = max((value for _, value in normalized), default=0)
    return [
        {
            "label": label,
            "value": value,
            "width": 0 if max_value == 0 else max(6, round((value / max_value) * 100)),
        }
        for label, value in normalized
    ]


def _dashboard_role():
    if is_platform_admin() or current_user.is_company_owner:
        return "owner"
    if current_user.role == ROLE_SUPERVISOR:
        return "supervisor"
    if current_user.role == ROLE_EMPLOYEE:
        return "employee"
    return "owner"
