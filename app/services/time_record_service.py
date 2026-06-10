from datetime import datetime, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import AccountingClient, Area, Employee, Task, TimeRecord, User
from app.roles import ROLE_SUPERVISOR
from app.services.audit_service import write_audit
from app.utils.datetime import argentina_now


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def calculate_hours(record_date, start_time, end_time):
    start_at = datetime.combine(record_date, start_time)
    end_at = datetime.combine(record_date, end_time)
    if end_at < start_at:
        end_at += timedelta(days=1)
    diff_seconds = (end_at - start_at).total_seconds()
    if diff_seconds == 0:
        return Decimal("0.00")
    if diff_seconds < 0:
        raise ValueError("La tarea debe finalizar despues de iniciarse.")
    return Decimal(diff_seconds / 3600).quantize(Decimal("0.01"))


def start_time_record(company_id, user_id, employee_id, supervisor_id, accounting_client_id, area_id, task_id, observations):
    employee = Employee.query.filter_by(id=employee_id, company_id=company_id, deleted_at=None).first()
    if not employee:
        raise ValueError("Empleado invalido.")

    supervisor = User.query.filter_by(
        id=supervisor_id,
        company_id=company_id,
        role=ROLE_SUPERVISOR,
        is_active_flag=True,
        deleted_at=None,
    ).first()
    if not supervisor:
        raise ValueError("Supervisor invalido.")

    accounting_client = AccountingClient.query.filter_by(
        id=accounting_client_id,
        company_id=company_id,
        active=True,
        deleted_at=None,
    ).first()
    if not accounting_client:
        raise ValueError("Cliente contable invalido.")

    area = Area.query.filter_by(id=area_id, company_id=company_id, deleted_at=None).first()
    if not area:
        raise ValueError("Area invalida.")

    task = Task.query.join(Area).filter(Task.id == task_id, Task.area_id == area.id, Task.deleted_at.is_(None)).first()
    if not task:
        raise ValueError("Tarea invalida para el area seleccionada.")

    now = argentina_now()
    record = TimeRecord(
        company_id=company_id,
        employee_id=employee_id,
        supervisor_id=supervisor_id,
        accounting_client_id=accounting_client_id,
        area_id=area_id,
        task_id=task_id,
        record_date=now.date(),
        start_time=now.time().replace(microsecond=0),
        hours=Decimal("0.00"),
        observations=observations,
        created_by=user_id,
    )
    db.session.add(record)
    db.session.flush()
    write_audit(
        "CREATE",
        "time_records",
        record.id,
        new_values={
            "employee_id": employee_id,
            "supervisor_id": supervisor_id,
            "accounting_client_id": accounting_client_id,
            "record_date": record.record_date.isoformat(),
            "start_time": record.start_time.strftime("%H:%M:%S"),
            "status": "in_progress",
            "area_id": area_id,
            "task_id": task_id,
        },
        company_id=company_id,
    )
    return record


def finish_time_record(record, user_id):
    if record.end_time is not None:
        raise ValueError("La tarea ya fue finalizada.")

    now = argentina_now()
    end_time = now.time().replace(microsecond=0)
    hours = calculate_hours(record.record_date, record.start_time, end_time)
    previous_values = {"status": "in_progress", "hours": str(record.hours)}
    record.end_time = end_time
    record.hours = hours
    record.updated_by = user_id
    db.session.flush()
    write_audit(
        "UPDATE",
        "time_records",
        record.id,
        previous_values=previous_values,
        new_values={
            "status": "finished",
            "end_time": end_time.strftime("%H:%M:%S"),
            "hours": str(hours),
        },
        company_id=record.company_id,
    )
    return record
