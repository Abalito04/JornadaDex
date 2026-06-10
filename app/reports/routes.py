import csv
from io import BytesIO, StringIO

from flask import Blueprint, Response, abort, render_template, request, send_file
from flask_login import current_user, login_required
from openpyxl import Workbook
from sqlalchemy import func

from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import AccountingClient, Area, Employee, Task, TimeRecord
from app.roles import ROLE_EMPLOYEE
from app.services.audit_service import write_audit
from app.services.supervisor_service import supervisors_for_company
from app.services.time_record_service import parse_date
from app.services.visibility_service import employee_is_visible, visible_employees_query, visible_time_records_query
from app.utils.datetime import format_duration_hs, format_time_hs

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    if is_platform_admin():
        abort(403)
    records = _filtered_records().all()
    can_filter_employee = not _is_employee_scope()
    if can_filter_employee:
        employees_query = Employee.query.filter_by(company_id=current_company_id(), deleted_at=None)
        employees = visible_employees_query(employees_query).order_by(Employee.last_name).all()
    else:
        employees = [current_user.employee] if current_user.employee else []
    can_filter_supervisor = not _is_employee_scope() and (current_user.is_company_owner or is_platform_admin())
    supervisors = supervisors_for_company(current_company_id())
    clients = AccountingClient.query.filter_by(company_id=current_company_id(), deleted_at=None).order_by(AccountingClient.name).all()
    areas = Area.query.filter_by(company_id=current_company_id(), deleted_at=None).order_by(Area.name).all()
    total_hours = sum(float(record.hours) for record in records)
    return render_template(
        "reports/index.html",
        records=records,
        employees=employees,
        supervisors=supervisors,
        clients=clients,
        areas=areas,
        total_hours=total_hours,
        can_filter_employee=can_filter_employee,
        can_filter_supervisor=can_filter_supervisor,
    )


@reports_bp.route("/export.csv")
@login_required
def export_csv():
    if is_platform_admin():
        abort(403)
    records = _filtered_records().all()
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Empleado", "Supervisor", "Cliente", "Fecha", "Inicio", "Fin", "Horas", "Estado", "Área", "Tarea", "Observaciones"])
    for record in records:
        writer.writerow(_record_row(record))
    write_audit("EXPORT", "time_records", new_values={"format": "csv", "count": len(records)})
    db.session.commit()
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=control_tiempo.csv"},
    )


@reports_bp.route("/export.xlsx")
@login_required
def export_excel():
    if is_platform_admin():
        abort(403)
    records = _filtered_records().all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Control de tiempo"
    ws.append(["Empleado", "Supervisor", "Cliente", "Fecha", "Inicio", "Fin", "Horas", "Estado", "Área", "Tarea", "Observaciones"])
    for record in records:
        ws.append(_record_row(record))
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    write_audit("EXPORT", "time_records", new_values={"format": "xlsx", "count": len(records)})
    db.session.commit()
    return send_file(
        buffer,
        as_attachment=True,
        download_name="control_tiempo.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _filtered_records():
    query = TimeRecord.query.filter_by(company_id=current_company_id(), deleted_at=None)
    can_filter_employee = not _is_employee_scope()
    can_filter_supervisor = current_user.is_company_owner or is_platform_admin()
    if not can_filter_employee:
        query = query.filter(TimeRecord.employee_id == current_user.employee_id)
    else:
        query = visible_time_records_query(query)

    employee_id = request.args.get("employee_id")
    supervisor_id = request.args.get("supervisor_id")
    accounting_client_id = request.args.get("accounting_client_id")
    area_id = request.args.get("area_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if employee_id and can_filter_employee:
        employee = Employee.query.filter_by(id=int(employee_id), company_id=current_company_id(), deleted_at=None).first()
        if not employee_is_visible(employee):
            query = query.filter(TimeRecord.employee_id == 0)
        else:
            query = query.filter(TimeRecord.employee_id == employee.id)
    if supervisor_id and can_filter_supervisor:
        query = query.filter(TimeRecord.supervisor_id == int(supervisor_id))
    if accounting_client_id:
        query = query.filter(TimeRecord.accounting_client_id == int(accounting_client_id))
    if area_id:
        query = query.filter(TimeRecord.area_id == int(area_id))
    if date_from:
        query = query.filter(TimeRecord.record_date >= parse_date(date_from))
    if date_to:
        query = query.filter(TimeRecord.record_date <= parse_date(date_to))
    return query.order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc())


def _is_employee_scope():
    return current_user.role == ROLE_EMPLOYEE and not current_user.is_company_owner and not is_platform_admin()


def _record_row(record):
    return [
        record.employee.full_name,
        _supervisor_name(record),
        record.accounting_client.name if record.accounting_client else "",
        record.record_date.isoformat(),
        format_time_hs(record.start_time),
        format_time_hs(record.end_time),
        format_duration_hs(record.hours),
        "En curso" if not record.end_time else "Finalizada",
        record.area.name,
        record.task.name,
        record.observations or "",
    ]


def _supervisor_name(record):
    if not record.supervisor:
        return ""
    return record.supervisor.employee.full_name if record.supervisor.employee else record.supervisor.username
