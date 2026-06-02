from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import Area, Employee, TimeRecord
from app.services.audit_service import write_audit
from app.services.time_record_service import finish_time_record, start_time_record

time_records_bp = Blueprint("time_records", __name__, url_prefix="/time-records")


@time_records_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        try:
            employee_id = int(request.form.get("employee_id") or 0)
            if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin():
                employee_id = current_user.employee_id
            start_time_record(
                company_id=current_company_id(),
                user_id=current_user.id,
                employee_id=employee_id,
                area_id=int(request.form.get("area_id") or 0),
                task_id=int(request.form.get("task_id") or 0),
                observations=request.form.get("observations", "").strip() or None,
            )
            db.session.commit()
            flash("Tarea iniciada con fecha y hora automatica.", "success")
            return redirect(url_for("time_records.index"))
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    employees = Employee.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None).order_by(Employee.last_name).all()
    if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin():
        employees = [current_user.employee] if current_user.employee else []

    areas = Area.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None).order_by(Area.name).all()
    records_query = TimeRecord.query.filter_by(company_id=current_company_id(), deleted_at=None)
    if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin():
        records_query = records_query.filter(TimeRecord.employee_id == current_user.employee_id)
    records = records_query.order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc()).limit(100).all()
    return render_template("time_records/index.html", employees=employees, areas=areas, records=records)


@time_records_bp.route("/<int:record_id>/finish", methods=["POST"])
@login_required
def finish(record_id):
    record = TimeRecord.query.filter_by(id=record_id, company_id=current_company_id(), deleted_at=None).first_or_404()
    if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin() and record.employee_id != current_user.employee_id:
        return ("Forbidden", 403)
    try:
        finish_time_record(record, current_user.id)
        db.session.commit()
        flash("Tarea finalizada con hora automatica.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
    return redirect(url_for("time_records.index"))


@time_records_bp.route("/<int:record_id>/delete", methods=["POST"])
@login_required
def delete(record_id):
    record = TimeRecord.query.filter_by(id=record_id, company_id=current_company_id(), deleted_at=None).first_or_404()
    if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin() and record.employee_id != current_user.employee_id:
        return ("Forbidden", 403)
    record.soft_delete(current_user.id)
    write_audit("DELETE", "time_records", record.id, previous_values={"hours": str(record.hours)})
    db.session.commit()
    flash("Registro eliminado logicamente.", "success")
    return redirect(url_for("time_records.index"))
