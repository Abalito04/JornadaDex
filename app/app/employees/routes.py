from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import Employee, User
from app.permissions.decorators import manager_required
from app.services.audit_service import write_audit

employees_bp = Blueprint("employees", __name__, url_prefix="/employees")


@employees_bp.route("/")
@manager_required
def index():
    employees = Employee.query.filter_by(company_id=current_user.company_id, deleted_at=None).order_by(Employee.last_name).all()
    return render_template("employees/index.html", employees=employees)


@employees_bp.route("/create", methods=["GET", "POST"])
@manager_required
def create():
    if request.method == "POST":
        try:
            employee = Employee(
                company_id=current_user.company_id,
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
                raise ValueError("Completa nombre, apellido y documento.")
            db.session.add(employee)
            db.session.flush()

            if request.form.get("create_user") == "on":
                username = request.form.get("username", "").strip().lower()
                password = request.form.get("password", "")
                role = request.form.get("role", "Employee")
                if not username or not password:
                    raise ValueError("Para crear usuario, completa usuario y clave.")
                user = User(
                    company_id=current_user.company_id,
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
            flash("Empleado creado.", "success")
            return redirect(url_for("employees.index"))
        except (IntegrityError, ValueError) as exc:
            db.session.rollback()
            flash(str(getattr(exc, "orig", exc)), "danger")

    return render_template("employees/form.html")


@employees_bp.route("/<int:employee_id>/delete", methods=["POST"])
@manager_required
def delete(employee_id):
    employee = Employee.query.filter_by(id=employee_id, company_id=current_user.company_id, deleted_at=None).first_or_404()
    employee.soft_delete(current_user.id)
    employee.active = False
    if employee.user:
        employee.user.soft_delete(current_user.id)
        employee.user.is_active_flag = False
    write_audit("DELETE", "employees", employee.id, previous_values={"name": employee.full_name})
    db.session.commit()
    flash("Empleado eliminado logicamente.", "success")
    return redirect(url_for("employees.index"))
