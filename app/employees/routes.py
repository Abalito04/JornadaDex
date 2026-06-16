from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app.context import current_company_id, is_platform_admin
from app.extensions import db
from app.models import Employee, User
from app.permissions.decorators import manager_required
from app.roles import ROLE_EMPLOYEE, ROLE_SUPERVISOR
from app.services.audit_service import write_audit
from app.services.visibility_service import employee_is_visible, visible_employees_query

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("/")
@manager_required
def index():
    employees_query = Employee.query.filter_by(company_id=current_company_id(), deleted_at=None)
    employees = visible_employees_query(employees_query).order_by(Employee.last_name).all()
    return render_template("employees/index.html", employees=employees)


@employees_bp.route("/create", methods=["GET", "POST"])
@manager_required
def create():
    if request.method == "POST":
        try:
            employee = Employee(
                company_id=current_company_id(),
                first_name=request.form.get("first_name", "").strip(),
                last_name=request.form.get("last_name", "").strip(),
                document_number=request.form.get("document_number", "").strip(),
                email=request.form.get("email", "").strip().lower() or None,
                phone=request.form.get("phone", "").strip() or None,
                position=request.form.get("position", "").strip() or None,
                notes=request.form.get("notes", "").strip() or None,
                created_by=current_user.id,
            )
            if not employee.first_name or not employee.last_name or not employee.document_number:
                raise ValueError("Completá nombre, apellido y documento.")
            db.session.add(employee)
            db.session.flush()

            if request.form.get("create_user") == "on":
                username = request.form.get("username", "").strip().lower()
                password = request.form.get("password", "")
                role = request.form.get("role", ROLE_EMPLOYEE)
                if role not in (ROLE_EMPLOYEE, ROLE_SUPERVISOR):
                    role = ROLE_EMPLOYEE
                if not username or not password:
                    raise ValueError("Para crear usuario, completa usuario y clave.")
                user = User(
                    company_id=current_company_id(),
                    employee_id=employee.id,
                    username=username,
                    email=employee.email or f"{username}@local",
                    role=role,
                    created_by=current_user.id,
                )
                user.set_password(password)
                db.session.add(user)

            write_audit("CREATE", "employees", employee.id, new_values={"name": employee.full_name})
            db.session.commit()
            flash("Colaborador creado.", "success")
            return redirect(url_for("employees.index"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    return render_template("employees/form.html", employee=None)


@employees_bp.route("/<int:employee_id>/edit", methods=["GET", "POST"])
@manager_required
def edit(employee_id):
    employee = Employee.query.filter_by(
        id=employee_id,
        company_id=current_company_id(),
        deleted_at=None,
    ).first_or_404()

    if employee.user and employee.user.is_company_owner and not current_user.is_company_owner and not is_platform_admin():
        return ("Forbidden", 403)
    if not employee_is_visible(employee):
        return ("Forbidden", 403)

    if request.method == "POST":
        try:
            previous_values = {
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "document_number": employee.document_number,
                "email": employee.email,
                "phone": employee.phone,
                "position": employee.position,
            }

            employee.first_name = request.form.get("first_name", "").strip()
            employee.last_name = request.form.get("last_name", "").strip()
            employee.document_number = request.form.get("document_number", "").strip()
            employee.email = request.form.get("email", "").strip().lower() or None
            employee.phone = request.form.get("phone", "").strip() or None
            employee.position = request.form.get("position", "").strip() or None
            employee.notes = request.form.get("notes", "").strip() or None
            employee.updated_by = current_user.id

            if not employee.first_name or not employee.last_name or not employee.document_number:
                raise ValueError("Completá nombre, apellido y documento.")

            if employee.user:
                employee.user.email = employee.email or employee.user.email
                employee.user.updated_by = current_user.id
                new_password = request.form.get("password", "")
                if new_password:
                    employee.user.set_password(new_password)
                    write_audit(
                        "PASSWORD_CHANGE",
                        "users",
                        employee.user.id,
                        new_values={"employee_id": employee.id, "reset_by": current_user.id},
                    )

            write_audit(
                "UPDATE",
                "employees",
                employee.id,
                previous_values=previous_values,
                new_values={
                    "first_name": employee.first_name,
                    "last_name": employee.last_name,
                    "document_number": employee.document_number,
                    "email": employee.email,
                    "phone": employee.phone,
                    "position": employee.position,
                },
            )
            db.session.commit()
            flash("Colaborador actualizado.", "success")
            return redirect(url_for("employees.index"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    return render_template("employees/form.html", employee=employee)


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@manager_required
def delete(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_company_id(), deleted_at=None).first_or_404()
    if employee.user and employee.user.is_company_owner and not current_user.is_company_owner and not is_platform_admin():
        return ("Forbidden", 403)
    if not employee_is_visible(employee):
        return ("Forbidden", 403)

    employee.soft_delete(current_user.id)
    employee.active = False
    if employee.user:
        employee.user.soft_delete(current_user.id)
        employee.user.is_active_flag = False
    write_audit("DELETE", "employees", employee.id, previous_values={"name": employee.full_name})
    db.session.commit()
    flash("Colaborador eliminado lógicamente.", "success")
    return redirect(url_for("employees.index"))
