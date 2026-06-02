import csv
from io import BytesIO, StringIO

from flask import Blueprint, Response, render_template, request, send_file
from flask_login import current_user, login_required
from openpyxl import Workbook
from sqlalchemy import func

from app.extensions import db
from app.models import Area, Employee, Task, TimeRecord
from app.services.audit_service import write_audit
from app.services.time_record_service import parse_date

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    records = _filtered_records().all()
    employees = Employee.query.filter_by(company_id=current_user.company_id, deleted_at=None).order_by(Employee.last_name).all()
    areas = Area.query.filter_by(company_id=current_user.company_id, deleted_at=None).order_by(Area.name).all()
    total_hours = sum(float(record.hours) for record in records)
    return render_template("reports/index.html", records=records, employees=employees, areas=areas, total_hours=total_hours)


@reports_bp.route("/export.csv")
@login_required
def export_csv():
    records = _filtered_records().all()
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Empleado", "Fecha", "Inicio", "Fin", "Horas", "Estado", "Area", "Tarea", "Observaciones"])
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
    records = _filtered_records().all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Control de tiempo"
    ws.append(["Empleado", "Fecha", "Inicio", "Fin", "Horas", "Estado", "Area", "Tarea", "Observaciones"])
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
    query = TimeRecord.query.filter_by(company_id=current_user.company_id, deleted_at=None)
    if current_user.role == "Employee" and not current_user.is_company_owner:
        query = query.filter(TimeRecord.employee_id == current_user.employee_id)

    employee_id = request.args.get("employee_id")
    area_id = request.args.get("area_id")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if employee_id:
        query = query.filter(TimeRecord.employee_id == int(employee_id))
    if area_id:
        query = query.filter(TimeRecord.area_id == int(area_id))
    if date_from:
        query = query.filter(TimeRecord.record_date >= parse_date(date_from))
    if date_to:
        query = query.filter(TimeRecord.record_date <= parse_date(date_to))
    return query.order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc())


def _record_row(record):
    return [
        record.employee.full_name,
        record.record_date.isoformat(),
        record.start_time.strftime("%H:%M:%S"),
        record.end_time.strftime("%H:%M:%S") if record.end_time else "",
        float(record.hours),
        "En curso" if not record.end_time else "Finalizada",
        record.area.name,
        record.task.name,
        record.observations or "",
    ]
