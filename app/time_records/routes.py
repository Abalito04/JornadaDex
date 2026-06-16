from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import AccountingClient, Area, Employee, Task, TimeRecord
from app.roles import ROLE_EMPLOYEE, ROLE_SUPERVISOR
from app.services.audit_service import write_audit
from app.services.supervisor_service import supervisor_for_company, supervisors_for_company
from app.services.time_record_service import finish_time_record, parse_date, start_time_record
from app.services.visibility_service import employee_is_visible, visible_company_time_records_query, visible_employees_query, visible_time_records_query

time_records_bp = Blueprint("time_records", __name__, url_prefix="/time-records")


@time_records_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if is_platform_admin():
        abort(403)
    can_choose_employee = current_user.role != ROLE_EMPLOYEE or current_user.is_company_owner or is_platform_admin()
    can_choose_supervisor = current_user.role != ROLE_SUPERVISOR or current_user.is_company_owner or is_platform_admin()
    if request.method == "POST":
        try:
            employee_id = int(request.form.get("employee_id") or 0)
            if not can_choose_employee:
                employee_id = current_user.employee_id
            supervisor_id = int(request.form.get("supervisor_id") or 0)
            if not can_choose_supervisor:
                supervisor_id = current_user.id
            selected_employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id(), deleted_at=None).first()
            if not employee_is_visible(selected_employee):
                return ("Forbidden", 403)
            start_time_record(
                company_id=current_company_id(),
                user_id=current_user.id,
                employee_id=employee_id,
                supervisor_id=supervisor_id,
                accounting_client_id=int(request.form.get("accounting_client_id") or 0),
                area_id=int(request.form.get("area_id") or 0),
                task_id=int(request.form.get("task_id") or 0),
                observations=request.form.get("observations", "").strip() or None,
            )
            db.session.commit()
            flash("Tarea iniciada con fecha y hora automática.", "success")
            return redirect(url_for("time_records.index"))
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    employees_query = Employee.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None)
    employees = visible_employees_query(employees_query).order_by(Employee.last_name).all()
    if not can_choose_employee:
        employees = [current_user.employee] if current_user.employee else []
    elif current_user.role == ROLE_SUPERVISOR and current_user.employee and current_user.employee_id not in {employee.id for employee in employees}:
        employees.insert(0, current_user.employee)

    areas = Area.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None).order_by(Area.name).all()
    tasks = (
        Task.query.join(Area)
        .filter(Area.company_id == current_company_id(), Task.active.is_(True), Task.deleted_at.is_(None))
        .order_by(Task.name)
        .all()
    )
    clients = (
        AccountingClient.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None)
        .order_by(AccountingClient.name)
        .all()
    )
    supervisors = supervisors_for_company(current_company_id())
    records_query = TimeRecord.query.filter_by(company_id=current_company_id(), deleted_at=None)
    if not can_choose_employee:
        records_query = records_query.filter(TimeRecord.employee_id == current_user.employee_id)
    elif current_user.role == ROLE_SUPERVISOR and not current_user.is_company_owner and not is_platform_admin():
        records_query = visible_company_time_records_query(records_query)
    else:
        records_query = visible_time_records_query(records_query)

    open_records = (
        records_query.filter(TimeRecord.end_time.is_(None))
        .order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc())
        .limit(20)
        .all()
    )
    records_query = _apply_record_filters(records_query.filter(TimeRecord.end_time.isnot(None)), can_choose_employee)
    records = records_query.order_by(TimeRecord.record_date.desc(), TimeRecord.start_time.desc()).limit(100).all()
    return render_template(
        "time_records/index.html",
        employees=employees,
        clients=clients,
        areas=areas,
        tasks=tasks,
        open_records=open_records,
        records=records,
        supervisors=supervisors,
        can_choose_employee=can_choose_employee,
        can_choose_supervisor=can_choose_supervisor,
        can_edit_records=_can_edit_records(),
        edit_note_for_record=_edit_note_for_record,
        has_record_filters=_has_record_filters(),
    )


@time_records_bp.route("/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
def edit(record_id):
    if is_platform_admin():
        abort(403)
    if not _can_edit_records():
        return ("Forbidden", 403)
    record = TimeRecord.query.filter_by(id=record_id, company_id=current_company_id(), deleted_at=None).first_or_404()
    if not employee_is_visible(record.employee):
        return ("Forbidden", 403)

    can_choose_supervisor = current_user.role != ROLE_SUPERVISOR or current_user.is_company_owner or is_platform_admin()
    employees_query = Employee.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None)
    employees = visible_employees_query(employees_query).order_by(Employee.last_name).all()
    if current_user.role == ROLE_SUPERVISOR and current_user.employee and current_user.employee_id not in {employee.id for employee in employees}:
        employees.insert(0, current_user.employee)
    supervisors = supervisors_for_company(current_company_id())
    clients = AccountingClient.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None).order_by(AccountingClient.name).all()
    areas = Area.query.filter_by(company_id=current_company_id(), active=True, deleted_at=None).order_by(Area.name).all()
    tasks = Task.query.filter_by(area_id=record.area_id, active=True, deleted_at=None).order_by(Task.name).all()

    if request.method == "POST":
        try:
            previous_values = {
                "employee_id": record.employee_id,
                "supervisor_id": record.supervisor_id,
                "accounting_client_id": record.accounting_client_id,
                "area_id": record.area_id,
                "task_id": record.task_id,
                "observations": record.observations,
            }
            employee_id = int(request.form.get("employee_id") or 0)
            supervisor_id = int(request.form.get("supervisor_id") or record.supervisor_id or 0)
            accounting_client_id = int(request.form.get("accounting_client_id") or 0)
            area_id = int(request.form.get("area_id") or 0)
            task_id = int(request.form.get("task_id") or 0)
            selected_employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id(), deleted_at=None).first()
            if not employee_is_visible(selected_employee):
                return ("Forbidden", 403)
            if not supervisor_for_company(current_company_id(), supervisor_id):
                raise ValueError("Encargado invalido.")
            if not AccountingClient.query.filter_by(id=accounting_client_id, company_id=current_company_id(), active=True, deleted_at=None).first():
                raise ValueError("Cliente contable invalido.")
            selected_area = Area.query.filter_by(id=area_id, company_id=current_company_id(), active=True, deleted_at=None).first()
            if not selected_area:
                raise ValueError("Área inválida.")
            if not Task.query.filter_by(id=task_id, area_id=selected_area.id, active=True, deleted_at=None).first():
                raise ValueError("Tarea inválida para el área seleccionada.")

            record.employee_id = employee_id
            record.supervisor_id = supervisor_id
            record.accounting_client_id = accounting_client_id
            record.area_id = area_id
            record.task_id = task_id
            record.observations = request.form.get("observations", "").strip() or None
            edit_note = request.form.get("edit_note", "").strip()
            if edit_note:
                record.observations = _append_edit_note(record.observations, edit_note)
            record.updated_by = current_user.id
            write_audit(
                "UPDATE",
                "time_records",
                record.id,
                previous_values=previous_values,
                new_values={
                    "employee_id": record.employee_id,
                    "supervisor_id": record.supervisor_id,
                    "accounting_client_id": record.accounting_client_id,
                    "area_id": record.area_id,
                    "task_id": record.task_id,
                    "observations": record.observations,
                    "edit_note": edit_note,
                },
            )
            db.session.commit()
            flash("Registro actualizado.", "success")
            return redirect(url_for("time_records.index"))
        except (ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "time_records/edit.html",
        record=record,
        employees=employees,
        supervisors=supervisors,
        clients=clients,
        areas=areas,
        tasks=tasks,
        can_choose_supervisor=can_choose_supervisor,
    )


@time_records_bp.route("/<int:record_id>/finish", methods=["POST"])
@login_required
def finish(record_id):
    if is_platform_admin():
        abort(403)
    record = TimeRecord.query.filter_by(id=record_id, company_id=current_company_id(), deleted_at=None).first_or_404()
    if not employee_is_visible(record.employee):
        return ("Forbidden", 403)
    if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin() and record.employee_id != current_user.employee_id:
        return ("Forbidden", 403)
    try:
        finish_time_record(record, current_user.id)
        db.session.commit()
        flash("Tarea finalizada con hora automática.", "success")
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "danger")
    return redirect(url_for("time_records.index"))


@time_records_bp.route("/<int:record_id>/delete", methods=["POST"])
@login_required
def delete(record_id):
    if is_platform_admin():
        abort(403)
    record = TimeRecord.query.filter_by(id=record_id, company_id=current_company_id(), deleted_at=None).first_or_404()
    if not employee_is_visible(record.employee):
        return ("Forbidden", 403)
    if current_user.role == "Employee" and not current_user.is_company_owner and not is_platform_admin() and record.employee_id != current_user.employee_id:
        return ("Forbidden", 403)
    record.soft_delete(current_user.id)
    write_audit("DELETE", "time_records", record.id, previous_values={"hours": str(record.hours)})
    db.session.commit()
    flash("Registro eliminado lógicamente.", "success")
    return redirect(url_for("time_records.index"))


def _can_edit_records():
    return current_user.role == ROLE_SUPERVISOR or current_user.is_company_owner or is_platform_admin()


def _append_edit_note(observations, edit_note):
    prefix = "Edicion encargado"
    if current_user.is_company_owner or is_platform_admin():
        prefix = "Edición gestión"
    text = f"{prefix}: {edit_note}"
    return f"{observations}\n{text}" if observations else text


def _edit_note_for_record(record):
    if not record.observations:
        return ""
    notes = [
        line.strip()
        for line in record.observations.splitlines()
        if line.strip().lower().startswith(("edición ", "edicion "))
    ]
    return notes[-1] if notes else ""


def _apply_record_filters(query, can_choose_employee):
    employee_id = request.args.get("record_employee_id", type=int)
    supervisor_id = request.args.get("record_supervisor_id", type=int)
    client_id = request.args.get("record_accounting_client_id", type=int)
    area_id = request.args.get("record_area_id", type=int)
    task_id = request.args.get("record_task_id", type=int)
    date_from = request.args.get("record_date_from", "").strip()
    date_to = request.args.get("record_date_to", "").strip()

    if employee_id and can_choose_employee:
        employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id(), deleted_at=None).first()
        if employee_is_visible(employee):
            query = query.filter(TimeRecord.employee_id == employee.id)
        else:
            query = query.filter(TimeRecord.employee_id == 0)
    if supervisor_id:
        query = query.filter(TimeRecord.supervisor_id == supervisor_id)
    if client_id:
        query = query.filter(TimeRecord.accounting_client_id == client_id)
    if area_id:
        query = query.filter(TimeRecord.area_id == area_id)
    if task_id:
        query = query.filter(TimeRecord.task_id == task_id)
    if date_from:
        query = query.filter(TimeRecord.record_date >= parse_date(date_from))
    if date_to:
        query = query.filter(TimeRecord.record_date <= parse_date(date_to))
    return query


def _has_record_filters():
    return any(
        request.args.get(key)
        for key in (
            "record_employee_id",
            "record_supervisor_id",
            "record_accounting_client_id",
            "record_area_id",
            "record_task_id",
            "record_date_from",
            "record_date_to",
        )
    )
